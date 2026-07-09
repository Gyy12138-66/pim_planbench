#!/usr/bin/env python3
"""PIM-PlanBench v0.4 执行效度子集的统一 PINN 训练 harness。

设计约束（见协议文档）：
  * 全部计划共用同一个 harness，只有 YAML 配置不同 —— 排除"实现者技巧"混淆；
  * 组件菜单：网络宽深 / Fourier 特征 / 周期嵌入 / 软硬 IC·BC / 损失权重（可线性 ramp）/
    均匀采样 + RAR / 课程式时间推进 / Adam(+L-BFGS) / 反问题参数 / 人工粘性（Euler）；
  * 计划未指定的旋钮一律取 configs/defaults_v0.4.yaml 的预注册默认值。

用法：
  python pinn_harness.py --config configs/smoke/poisson_003.yaml [--seed 0]
      [--max-adam-steps 500] [--out results.csv]
"""
import argparse
import copy
import csv
import json
import math
import os
import time

import numpy as np
import torch
import yaml

import references as refs

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULTS_PATH = os.path.join(HERE, "configs", "defaults_v0.4.yaml")


# ------------------------------------------------------------------ utilities
def deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def grad(u, X):
    """du/dX，保留计算图。u: (N,1) 或 (N,), X: (N,d) -> (N,d)"""
    return torch.autograd.grad(u, X, torch.ones_like(u), create_graph=True)[0]


def mse(x, target=None):
    if target is None:
        return (x**2).mean()
    return ((x - target) ** 2).mean()


class Ramp:
    """损失权重：常数，或 {start,end,steps} 线性爬升后保持。"""

    def __init__(self, spec):
        if isinstance(spec, dict):
            self.w0, self.w1 = float(spec["start"]), float(spec["end"])
            self.n = max(1, int(spec["steps"]))
        else:
            self.w0 = self.w1 = float(spec)
            self.n = 1

    def __call__(self, step):
        if step >= self.n:
            return self.w1
        return self.w0 + (self.w1 - self.w0) * step / self.n


# ------------------------------------------------------------------- network
class MLP(torch.nn.Module):
    def __init__(self, in_dim, out_dim, width, depth, activation="tanh"):
        super().__init__()
        act = {"tanh": torch.nn.Tanh, "gelu": torch.nn.GELU,
               "sin": None}[activation]
        layers, d = [], in_dim
        for _ in range(depth):
            layers += [torch.nn.Linear(d, width), act() if act else Sine()]
            d = width
        layers += [torch.nn.Linear(d, out_dim)]
        self.net = torch.nn.Sequential(*layers)

    def forward(self, z):
        return self.net(z)


class Sine(torch.nn.Module):
    def forward(self, z):
        return torch.sin(z)


class FeatureMap(torch.nn.Module):
    """输入特征：可选周期嵌入（第 0 维空间坐标）+ 可选随机 Fourier 特征。"""

    def __init__(self, in_dim, cfg, x_range=None, generator=None):
        super().__init__()
        self.harmonics = int(cfg.get("periodic_harmonics", 0) or 0)
        self.x_range = x_range
        if self.harmonics > 0 and x_range is None:
            raise ValueError("periodic_harmonics: 该任务不支持周期嵌入")
        dim = in_dim
        if self.harmonics > 0:
            dim = in_dim - 1 + 2 * self.harmonics
        four = cfg.get("fourier", {}) or {}
        self.n_four = int(four.get("num", 0) or 0)
        if self.n_four > 0:
            sigma = float(four.get("sigma", 5.0))
            B = torch.randn(dim, self.n_four, generator=generator) * sigma
            self.register_buffer("B", B)
            dim = 2 * self.n_four
        self.out_dim = dim

    def forward(self, X):
        Z = X
        if self.harmonics > 0:
            a, b = self.x_range
            theta = 2.0 * math.pi * (X[:, :1] - a) / (b - a)
            feats = [f(k * theta) for k in range(1, self.harmonics + 1)
                     for f in (torch.sin, torch.cos)]
            Z = torch.cat(feats + [X[:, 1:]], dim=1)
        if self.n_four > 0:
            proj = 2.0 * math.pi * (Z @ self.B)
            Z = torch.cat([torch.sin(proj), torch.cos(proj)], dim=1)
        return Z


class Model(torch.nn.Module):
    """FeatureMap -> MLP -> 任务级输出变换（硬约束在任务里实现）。"""

    def __init__(self, task, cfg, generator):
        super().__init__()
        self.task = task
        self.fmap = FeatureMap(task.in_dim, cfg["features"],
                               x_range=task.periodic_range, generator=generator)
        self.mlp = MLP(self.fmap.out_dim, task.raw_out_dim,
                       cfg["net"]["width"], cfg["net"]["depth"],
                       cfg["net"]["activation"])

    def forward(self, X):
        raw = self.mlp(self.fmap(X))
        return self.task.output_transform(X, raw)


# ------------------------------------------------------------------- tasks
class TaskBase:
    """每题定义：域、残差、IC/BC 损失项、硬约束变换、评测。"""
    in_dim = 2
    raw_out_dim = 1
    periodic_range = None  # (a,b) -> 周期嵌入可用

    def __init__(self, cfg, device, dtype):
        self.cfg = cfg
        self.device = device
        self.dtype = dtype
        self.hard_bc = bool(cfg["constraints"].get("hard_bc", False))
        self.hard_ic = bool(cfg["constraints"].get("hard_ic", False))
        self.check_supported()

    def check_supported(self):
        pass

    def t(self, arr):
        return torch.tensor(np.asarray(arr), device=self.device, dtype=self.dtype)

    def rand(self, n, lo, hi, rng):
        u = torch.rand(n, len(lo), generator=rng, device=self.device, dtype=self.dtype)
        lo = self.t(lo)
        hi = self.t(hi)
        return lo + (hi - lo) * u

    # 下面由子类实现
    def sample_pde(self, n, rng, t_frac=1.0):
        raise NotImplementedError

    def residual(self, model, X):
        raise NotImplementedError

    def output_transform(self, X, raw):
        return raw

    def loss_terms(self, model, rng, t_frac=1.0):
        """返回 {name: loss}，不含 pde 项。"""
        return {}

    def evaluate(self, model):
        raise NotImplementedError

    @torch.no_grad()
    def _predict_grid(self, model, cols, chunk=65536):
        X = torch.stack(cols, dim=1)
        outs = []
        for i in range(0, X.shape[0], chunk):
            outs.append(model(X[i:i + chunk]))
        return torch.cat(outs, 0)


def rel_l2(pred, ref):
    ref_n = np.linalg.norm(ref)
    return float(np.linalg.norm(pred - ref) / (ref_n + 1e-30))


class Poisson003(TaskBase):
    """-Δu = f, f = 2π² sin(πx)sin(πy), [0,1]², 齐次 Dirichlet。"""

    def sample_pde(self, n, rng, t_frac=1.0):
        return self.rand(n, [0.0, 0.0], [1.0, 1.0], rng)

    def residual(self, model, X):
        X = X.detach().requires_grad_(True)
        u = model(X)
        g = grad(u, X)
        u_xx = grad(g[:, :1], X)[:, :1]
        u_yy = grad(g[:, 1:2], X)[:, 1:2]
        f = 2.0 * math.pi**2 * torch.sin(math.pi * X[:, :1]) * torch.sin(math.pi * X[:, 1:2])
        return u_xx + u_yy + f

    def output_transform(self, X, raw):
        if self.hard_bc:
            bump = (X[:, :1] * (1 - X[:, :1]) * X[:, 1:2] * (1 - X[:, 1:2]))
            return bump * raw
        return raw

    def loss_terms(self, model, rng, t_frac=1.0):
        if self.hard_bc:
            return {}
        n = self.cfg["sampling"]["n_bc"]
        s = torch.rand(n, 1, generator=rng, device=self.device, dtype=self.dtype)
        zeros = torch.zeros_like(s)
        ones = torch.ones_like(s)
        Xb = torch.cat([torch.cat([s, zeros], 1), torch.cat([s, ones], 1),
                        torch.cat([zeros, s], 1), torch.cat([ones, s], 1)], 0)
        return {"bc": mse(model(Xb))}

    def evaluate(self, model):
        ref = refs.poisson_reference()
        x, y, U = ref["x"], ref["y"], ref["u"]
        X, Y = np.meshgrid(x, y, indexing="ij")
        pred = self._predict_grid(model, [self.t(X.ravel()), self.t(Y.ravel())])
        return {"rel_l2": rel_l2(pred.cpu().numpy().ravel(), U.ravel())}


class Advection005(TaskBase):
    """u_t + c u_x = 0, c=1, x∈[0,1) 周期, u0=sin(2πx), t∈[0,1]。"""
    C = 1.0
    periodic_range = (0.0, 1.0)

    def u0(self, x):
        return torch.sin(2.0 * math.pi * x)

    def sample_pde(self, n, rng, t_frac=1.0):
        return self.rand(n, [0.0, 0.0], [1.0, t_frac], rng)

    def residual(self, model, X):
        X = X.detach().requires_grad_(True)
        u = model(X)
        g = grad(u, X)
        return g[:, 1:2] + self.C * g[:, :1]

    def output_transform(self, X, raw):
        if self.hard_ic:
            return self.u0(X[:, :1]) + X[:, 1:2] * raw
        return raw

    def loss_terms(self, model, rng, t_frac=1.0):
        terms = {}
        n = self.cfg["sampling"]["n_ic"]
        if not self.hard_ic:
            x = torch.rand(n, 1, generator=rng, device=self.device, dtype=self.dtype)
            Xi = torch.cat([x, torch.zeros_like(x)], 1)
            terms["ic"] = mse(model(Xi), self.u0(x))
        if self.cfg["features"].get("periodic_harmonics", 0) == 0:
            tt = torch.rand(self.cfg["sampling"]["n_bc"], 1, generator=rng,
                            device=self.device, dtype=self.dtype) * t_frac
            X0 = torch.cat([torch.zeros_like(tt), tt], 1)
            X1 = torch.cat([torch.ones_like(tt), tt], 1)
            terms["periodic"] = mse(model(X0) - model(X1))
        return terms

    def evaluate(self, model):
        ref = refs.advection_reference()
        X, T = np.meshgrid(ref["x"], ref["t"], indexing="ij")
        pred = self._predict_grid(model, [self.t(X.ravel()), self.t(T.ravel())])
        return {"rel_l2": rel_l2(pred.cpu().numpy().ravel(), ref["u"].ravel())}


class BurgersInverse010(TaskBase):
    """u_t + u u_x = ν u_xx；ν 未知（log 参数化），稀疏噪声观测。"""
    NU_TRUE = refs.NU_TRUE

    def __init__(self, cfg, device, dtype):
        super().__init__(cfg, device, dtype)
        init_nu = float(cfg["inverse"].get("init_nu", 0.1))
        self.log_nu = torch.nn.Parameter(
            torch.tensor(math.log(init_nu), device=device, dtype=dtype))
        d = cfg["data"]
        obs = refs.burgers_observations(d["n_obs"], d["noise_rel"], d["seed"])
        self.obs_X = self.t(np.stack([obs["x"], obs["t"]], 1))
        self.obs_u = self.t(obs["u"]).reshape(-1, 1)

    def extra_parameters(self):
        return [self.log_nu]

    def u0(self, x):
        return -torch.sin(math.pi * x)

    def sample_pde(self, n, rng, t_frac=1.0):
        return self.rand(n, [-1.0, 0.0], [1.0, t_frac], rng)

    def residual(self, model, X):
        X = X.detach().requires_grad_(True)
        u = model(X)
        g = grad(u, X)
        u_x, u_t = g[:, :1], g[:, 1:2]
        u_xx = grad(u_x, X)[:, :1]
        return u_t + u * u_x - torch.exp(self.log_nu) * u_xx

    def output_transform(self, X, raw):
        if self.hard_ic:  # 同时硬化 IC 与 Dirichlet0 边界
            return self.u0(X[:, :1]) + X[:, 1:2] * (1 - X[:, :1] ** 2) * raw
        return raw

    def loss_terms(self, model, rng, t_frac=1.0):
        terms = {"data": mse(model(self.obs_X), self.obs_u)}
        if not self.hard_ic:
            n = self.cfg["sampling"]["n_ic"]
            x = -1 + 2 * torch.rand(n, 1, generator=rng, device=self.device, dtype=self.dtype)
            terms["ic"] = mse(model(torch.cat([x, torch.zeros_like(x)], 1)), self.u0(x))
            tt = torch.rand(self.cfg["sampling"]["n_bc"], 1, generator=rng,
                            device=self.device, dtype=self.dtype) * t_frac
            Xb = torch.cat([torch.cat([-torch.ones_like(tt), tt], 1),
                            torch.cat([torch.ones_like(tt), tt], 1)], 0)
            terms["bc"] = mse(model(Xb))
        return terms

    def evaluate(self, model):
        ref = refs.burgers_reference()
        X, T = np.meshgrid(ref["x"], ref["t"], indexing="ij")
        pred = self._predict_grid(model, [self.t(X.ravel()), self.t(T.ravel())])
        nu_hat = float(torch.exp(self.log_nu))
        return {"rel_l2": rel_l2(pred.cpu().numpy().ravel(), ref["u"].ravel()),
                "nu_hat": nu_hat,
                "nu_rel_err": abs(nu_hat - self.NU_TRUE) / self.NU_TRUE}


class AllenCahn016(TaskBase):
    """u_t = d u_xx + 5(u - u³), d=1e-4, x∈[-1,1) 周期, u0=x²cos(πx)。"""
    D = refs.AC_D
    periodic_range = (-1.0, 1.0)

    def u0(self, x):
        return x**2 * torch.cos(math.pi * x)

    def sample_pde(self, n, rng, t_frac=1.0):
        return self.rand(n, [-1.0, 0.0], [1.0, t_frac], rng)

    def residual(self, model, X):
        X = X.detach().requires_grad_(True)
        u = model(X)
        g = grad(u, X)
        u_xx = grad(g[:, :1], X)[:, :1]
        return g[:, 1:2] - self.D * u_xx - 5.0 * (u - u**3)

    def output_transform(self, X, raw):
        if self.hard_ic:
            return self.u0(X[:, :1]) + X[:, 1:2] * raw
        return raw

    def loss_terms(self, model, rng, t_frac=1.0):
        terms = {}
        if not self.hard_ic:
            n = self.cfg["sampling"]["n_ic"]
            x = -1 + 2 * torch.rand(n, 1, generator=rng, device=self.device, dtype=self.dtype)
            terms["ic"] = mse(model(torch.cat([x, torch.zeros_like(x)], 1)), self.u0(x))
        if self.cfg["features"].get("periodic_harmonics", 0) == 0:
            tt = torch.rand(self.cfg["sampling"]["n_bc"], 1, generator=rng,
                            device=self.device, dtype=self.dtype) * t_frac
            Xa = torch.cat([-torch.ones_like(tt), tt], 1)
            Xb = torch.cat([torch.ones_like(tt), tt], 1)
            terms["periodic"] = mse(model(Xa) - model(Xb))
        return terms

    def evaluate(self, model):
        ref = refs.allen_cahn_reference()
        X, T = np.meshgrid(ref["x"], ref["t"], indexing="ij")
        pred = self._predict_grid(model, [self.t(X.ravel()), self.t(T.ravel())])
        return {"rel_l2": rel_l2(pred.cpu().numpy().ravel(), ref["u"].ravel())}


class EulerSod023(TaskBase):
    """1D 可压缩 Euler（Sod 激波管），守恒形式残差 + 可选人工粘性。
    网络输出 (ρ, u, p)，ρ、p 经 softplus 保正。"""
    raw_out_dim = 3
    T_MAX = 0.2

    def sample_pde(self, n, rng, t_frac=1.0):
        return self.rand(n, [0.0, 0.0], [1.0, self.T_MAX * t_frac], rng)

    def output_transform(self, X, raw):
        rho = torch.nn.functional.softplus(raw[:, :1])
        u = raw[:, 1:2]
        p = torch.nn.functional.softplus(raw[:, 2:3])
        return torch.cat([rho, u, p], 1)

    def _ic(self, x):
        left = (x < 0.5).to(x.dtype)
        rho = left * 1.0 + (1 - left) * 0.125
        p = left * 1.0 + (1 - left) * 0.1
        return rho, torch.zeros_like(x), p

    def residual(self, model, X):
        X = X.detach().requires_grad_(True)
        out = model(X)
        rho, u, p = out[:, :1], out[:, 1:2], out[:, 2:3]
        g = refs.GAMMA
        m = rho * u
        E = p / (g - 1.0) + 0.5 * rho * u**2
        U = [rho, m, E]
        F = [m, m * u + p, u * (E + p)]
        eps = float(self.cfg["euler"].get("artificial_viscosity", 0.0))
        res = []
        for Ui, Fi in zip(U, F):
            gU = grad(Ui, X)
            gF = grad(Fi, X)
            r = gU[:, 1:2] + gF[:, :1]
            if eps > 0:
                r = r - eps * grad(gU[:, :1], X)[:, :1]
            res.append(r)
        return torch.cat(res, 1)

    def loss_terms(self, model, rng, t_frac=1.0):
        n = self.cfg["sampling"]["n_ic"]
        x = torch.rand(n, 1, generator=rng, device=self.device, dtype=self.dtype)
        rho0, u0, p0 = self._ic(x)
        out = model(torch.cat([x, torch.zeros_like(x)], 1))
        ic = mse(out[:, :1], rho0) + mse(out[:, 1:2], u0) + mse(out[:, 2:3], p0)

        nb = self.cfg["sampling"]["n_bc"]
        tt = torch.rand(nb, 1, generator=rng, device=self.device,
                        dtype=self.dtype) * self.T_MAX * t_frac
        bc = 0.0
        for xv, (r_t, u_t, p_t) in [(0.0, (1.0, 0.0, 1.0)), (1.0, (0.125, 0.0, 0.1))]:
            Xb = torch.cat([torch.full_like(tt, xv), tt], 1)
            ob = model(Xb)
            bc = bc + mse(ob[:, :1], torch.full_like(tt, r_t)) \
                + mse(ob[:, 1:2], torch.full_like(tt, u_t)) \
                + mse(ob[:, 2:3], torch.full_like(tt, p_t))
        return {"ic": ic, "bc": bc}

    def evaluate(self, model):
        ref = refs.sod_reference()
        x, t = ref["x"], ref["t"][1:]  # 跳过 t=0 间断本身
        X, T = np.meshgrid(x, t, indexing="ij")
        pred = self._predict_grid(model, [self.t(X.ravel()), self.t(T.ravel())])
        pred = pred.cpu().numpy()
        fields = {}
        for i, name in enumerate(["rho", "u", "p"]):
            fields[f"rel_l2_{name}"] = rel_l2(pred[:, i], ref[name][:, 1:].ravel())
        fields["rel_l2"] = float(np.mean(list(fields.values())))
        return fields


TASKS = {
    "easy_poisson_2d_source_003": Poisson003,
    "easy_advection_1d_periodic_005": Advection005,
    "medium_burgers_inverse_viscosity_010": BurgersInverse010,
    "hard_allen_cahn_016": AllenCahn016,
    "hard_plus_euler_shock_023": EulerSod023,
}


# ------------------------------------------------------------------- training
def run_from_config(cfg_path, seed=None, max_adam_steps=None):
    with open(cfg_path, encoding="utf-8") as f:
        user_cfg = yaml.safe_load(f)
    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        cfg = deep_merge(yaml.safe_load(f), user_cfg)
    if seed is not None:
        cfg["seed"] = seed
    if max_adam_steps is not None:
        cur = cfg.get("curriculum") or []
        total = sum(int(ph["steps"]) for ph in cur)
        if total > 0:
            for ph in cur:
                ph["steps"] = max(1, int(ph["steps"] * max_adam_steps / total))
        cfg["optimizer"]["adam"]["steps"] = max_adam_steps

    dev = cfg["device"]
    device = torch.device(("cuda" if torch.cuda.is_available() else "cpu")
                          if dev == "auto" else dev)
    dtype = {"float32": torch.float32, "float64": torch.float64}[cfg["dtype"]]
    torch.manual_seed(cfg["seed"])
    rng = torch.Generator(device="cpu").manual_seed(cfg["seed"])
    gen_dev = (torch.Generator(device=device).manual_seed(cfg["seed"])
               if device.type != "cpu" else rng)

    task_cls = TASKS[cfg["task"]]
    task = task_cls(cfg, device, dtype)
    model = Model(task, cfg, generator=rng).to(device=device, dtype=dtype)

    params = list(model.parameters())
    if hasattr(task, "extra_parameters"):
        params += task.extra_parameters()

    weights = {k: Ramp(v) for k, v in cfg["weights"].items()}
    samp = cfg["sampling"]
    phases = cfg.get("curriculum") or [{"t_frac": 1.0,
                                        "steps": cfg["optimizer"]["adam"]["steps"]}]

    def total_loss(X_pde, t_frac, step):
        terms = {"pde": mse(task.residual(model, X_pde))}
        terms.update(task.loss_terms(model, gen_dev, t_frac))
        loss = 0.0
        for name, val in terms.items():
            loss = loss + weights.get(name, Ramp(1.0))(step) * val
        return loss, terms

    t0 = time.time()
    diverged = False
    step_global = 0
    opt = torch.optim.Adam(params, lr=cfg["optimizer"]["adam"]["lr"])
    X_pde = task.sample_pde(samp["n_pde"], gen_dev, phases[0]["t_frac"])

    for phase in phases:
        t_frac = float(phase["t_frac"])
        X_pde = task.sample_pde(samp["n_pde"], gen_dev, t_frac)
        for it in range(int(phase["steps"])):
            if samp["resample_every"] and step_global and \
                    step_global % samp["resample_every"] == 0:
                X_pde = task.sample_pde(samp["n_pde"], gen_dev, t_frac)
            rar = samp.get("rar") or {}
            if rar.get("every") and step_global and step_global % rar["every"] == 0:
                pool = task.sample_pde(rar["pool"], gen_dev, t_frac)
                with torch.enable_grad():
                    r = task.residual(model, pool).detach().abs().mean(dim=1)
                idx = torch.topk(r, int(rar["add"])).indices
                X_pde = torch.cat([X_pde, pool[idx].detach()], 0)

            opt.zero_grad()
            loss, terms = total_loss(X_pde, t_frac, step_global)
            if not torch.isfinite(loss):
                diverged = True
                break
            loss.backward()
            opt.step()
            if cfg["log_every"] and step_global % cfg["log_every"] == 0:
                msg = " ".join(f"{k}={float(v):.2e}" for k, v in terms.items())
                print(f"[{cfg['task']}|seed{cfg['seed']}] step {step_global} "
                      f"loss={float(loss):.3e} {msg}", flush=True)
            step_global += 1
        if diverged:
            break

    lbfgs_steps = int(cfg["optimizer"]["lbfgs"]["steps"])
    if lbfgs_steps > 0 and not diverged:
        lopt = torch.optim.LBFGS(params, lr=cfg["optimizer"]["lbfgs"]["lr"],
                                 max_iter=lbfgs_steps,
                                 history_size=50, line_search_fn="strong_wolfe")
        X_fix = X_pde.detach()

        def closure():
            lopt.zero_grad()
            loss, _ = total_loss(X_fix, phases[-1]["t_frac"], step_global)
            loss.backward()
            return loss

        try:
            lopt.step(closure)
        except Exception as e:  # L-BFGS 数值失败按发散记录
            print("L-BFGS failed:", e)
            diverged = True

    wall = time.time() - t0
    metrics = {"diverged": int(diverged), "wall_time_s": round(wall, 1)}
    try:
        ev = task.evaluate(model)
        if any(not np.isfinite(v) for v in ev.values() if isinstance(v, float)):
            metrics["diverged"] = 1
        metrics.update(ev)
    except Exception as e:
        metrics["diverged"] = 1
        metrics["eval_error"] = str(e)
    metrics.update({"task": cfg["task"], "arm": cfg.get("arm", "?"),
                    "seed": cfg["seed"], "config": os.path.basename(cfg_path),
                    "adam_steps": cfg["optimizer"]["adam"]["steps"]})
    return metrics


def append_csv(path, row):
    exists = os.path.exists(path)
    keys = ["task", "arm", "config", "seed", "adam_steps", "diverged",
            "rel_l2", "rel_l2_rho", "rel_l2_u", "rel_l2_p",
            "nu_hat", "nu_rel_err", "wall_time_s", "eval_error"]
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--max-adam-steps", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    m = run_from_config(args.config, args.seed, args.max_adam_steps)
    print(json.dumps(m, indent=2, ensure_ascii=False))
    if args.out:
        append_csv(args.out, m)
