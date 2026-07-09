#!/usr/bin/env python3
"""执行效度子集的参考解生成器（v0.4）。

五道题的预注册数值实例（见 docs/execution_validation_protocol_v0.4.md 实例化表）：
  easy_poisson_2d_source_003      制造解 u*=sin(pi x)sin(pi y), f=2pi^2 sin sin, [0,1]^2, 齐次 Dirichlet
  easy_advection_1d_periodic_005  u_t + c u_x = 0, c=1, x in [0,1) 周期, u0=sin(2pi x), 精确解
  medium_burgers_inverse_viscosity_010  u_t + u u_x = nu u_xx, nu_true=0.01/pi, x in [-1,1],
                                        u0=-sin(pi x), Dirichlet 0（Raissi 经典反问题设定）
  hard_allen_cahn_016             u_t = d u_xx + 5(u - u^3), d=1e-4, x in [-1,1) 周期,
                                  u0=x^2 cos(pi x)（经典 PINN 硬基准）
  hard_plus_euler_shock_023       Sod 激波管, gamma=1.4, 精确 Riemann 解, t in (0, 0.2]

全部参考解缓存到 reference_data/*.npz（一次计算，多次复用）。
用法：python references.py [--self-test]
"""
import argparse
import os

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "reference_data")

GAMMA = 1.4
NU_TRUE = 0.01 / np.pi
AC_D = 1e-4


def _cache(name, builder):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name + ".npz")
    if os.path.exists(path):
        return dict(np.load(path))
    data = builder()
    np.savez(path, **data)
    return data


# ---------------------------------------------------------------- Poisson 2D
def poisson_reference(n=129):
    """制造解，天然精确。返回网格与 u*。"""
    def build():
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        X, Y = np.meshgrid(x, y, indexing="ij")
        U = np.sin(np.pi * X) * np.sin(np.pi * Y)
        return {"x": x, "y": y, "u": U}

    return _cache("poisson_003", build)


# ------------------------------------------------------------- Advection 1D
def advection_reference(nx=256, nt=101, c=1.0, T=1.0):
    """精确解：初值随速度 c 周期平移。"""
    def build():
        x = np.linspace(0.0, 1.0, nx, endpoint=False)
        t = np.linspace(0.0, T, nt)
        X, Tt = np.meshgrid(x, t, indexing="ij")
        U = np.sin(2.0 * np.pi * (X - c * Tt))
        return {"x": x, "t": t, "u": U, "c": np.array(c)}

    return _cache("advection_005", build)


# ------------------------------------------------------- Burgers 1D (viscous)
def burgers_reference(nx=2049, nt=101, nu=NU_TRUE, T=1.0):
    """高分辨 method-of-lines 参考解（中心差分 + LSODA 自适应刚性积分）。"""
    def build():
        x = np.linspace(-1.0, 1.0, nx)
        dx = x[1] - x[0]
        u0 = -np.sin(np.pi * x)

        def rhs(_t, u):
            du = np.zeros_like(u)
            ux = (u[2:] - u[:-2]) / (2 * dx)
            uxx = (u[2:] - 2 * u[1:-1] + u[:-2]) / dx**2
            du[1:-1] = -u[1:-1] * ux + nu * uxx
            du[0] = du[-1] = 0.0  # Dirichlet 0
            return du

        t = np.linspace(0.0, T, nt)
        sol = solve_ivp(rhs, (0.0, T), u0, t_eval=t, method="LSODA",
                        rtol=1e-8, atol=1e-10, lband=1, uband=1)
        assert sol.success, sol.message
        return {"x": x, "t": t, "u": sol.y, "nu": np.array(nu)}

    return _cache("burgers_010", build)


def burgers_observations(n_obs=2000, noise_rel=0.01, seed=0):
    """反问题观测集：从参考解双线性插值采样 + 相对高斯噪声。固定种子，预注册。"""
    name = f"burgers_010_obs_n{n_obs}_noise{noise_rel}_seed{seed}"

    def build():
        ref = burgers_reference()
        x, t, u = ref["x"], ref["t"], ref["u"]
        rng = np.random.default_rng(seed)
        xo = rng.uniform(x[0], x[-1], n_obs)
        to = rng.uniform(t[0], t[-1], n_obs)
        ix = np.clip(np.searchsorted(x, xo) - 1, 0, len(x) - 2)
        it = np.clip(np.searchsorted(t, to) - 1, 0, len(t) - 2)
        wx = (xo - x[ix]) / (x[ix + 1] - x[ix])
        wt = (to - t[it]) / (t[it + 1] - t[it])
        uo = ((1 - wx) * (1 - wt) * u[ix, it] + wx * (1 - wt) * u[ix + 1, it]
              + (1 - wx) * wt * u[ix, it + 1] + wx * wt * u[ix + 1, it + 1])
        uo = uo + rng.normal(0.0, noise_rel * np.std(u), n_obs)
        return {"x": xo, "t": to, "u": uo}

    return _cache(name, build)


# ------------------------------------------------------------- Allen-Cahn 1D
def allen_cahn_reference(n=512, nt=101, d=AC_D, T=1.0):
    """周期谱方法 + 自适应积分（k_max^2 d ~ 65，非强刚性，RK45 足够）。"""
    def build():
        x = -1.0 + 2.0 * np.arange(n) / n
        k = 2.0 * np.pi * np.fft.rfftfreq(n, d=2.0 / n)
        u0 = x**2 * np.cos(np.pi * x)

        def rhs(_t, u):
            uxx = np.fft.irfft(-(k**2) * np.fft.rfft(u), n=n)
            return d * uxx + 5.0 * (u - u**3)

        t = np.linspace(0.0, T, nt)
        sol = solve_ivp(rhs, (0.0, T), u0, t_eval=t, method="RK45",
                        rtol=1e-7, atol=1e-9)
        assert sol.success, sol.message
        return {"x": x, "t": t, "u": sol.y, "d": np.array(d)}

    return _cache("allen_cahn_016", build)


# ------------------------------------------------- Euler (Sod) 精确 Riemann 解
def _pressure_fn(p, pk, rk, ck, g=GAMMA):
    """Toro 式压力函数 f_K(p)：激波支 / 稀疏波支。"""
    if p > pk:  # shock
        a = 2.0 / ((g + 1.0) * rk)
        b = (g - 1.0) / (g + 1.0) * pk
        return (p - pk) * np.sqrt(a / (p + b))
    return 2.0 * ck / (g - 1.0) * ((p / pk) ** ((g - 1.0) / (2.0 * g)) - 1.0)


def _riemann_star(pl, rl, ul, pr, rr, ur, g=GAMMA):
    cl = np.sqrt(g * pl / rl)
    cr = np.sqrt(g * pr / rr)
    fun = lambda p: (_pressure_fn(p, pl, rl, cl) + _pressure_fn(p, pr, rr, cr)
                     + (ur - ul))
    pstar = brentq(fun, 1e-10, 10.0 * max(pl, pr), xtol=1e-14)
    ustar = 0.5 * (ul + ur) + 0.5 * (_pressure_fn(pstar, pr, rr, cr)
                                     - _pressure_fn(pstar, pl, rl, cl))
    return pstar, ustar


def _sample_riemann(xi, pl, rl, ul, pr, rr, ur, g=GAMMA):
    """按自相似变量 xi = (x - x0)/t 采样单点 (rho, u, p)。通用左右波型。"""
    cl = np.sqrt(g * pl / rl)
    cr = np.sqrt(g * pr / rr)
    ps, us = _riemann_star(pl, rl, ul, pr, rr, ur, g)
    gm, gp = g - 1.0, g + 1.0

    if xi <= us:  # 接触间断左侧
        if ps > pl:  # 左激波
            rsl = rl * ((ps / pl + gm / gp) / (gm / gp * ps / pl + 1.0))
            sl = ul - cl * np.sqrt((gp / (2 * g)) * ps / pl + gm / (2 * g))
            return (rl, ul, pl) if xi <= sl else (rsl, us, ps)
        # 左稀疏波
        rsl = rl * (ps / pl) ** (1.0 / g)
        csl = cl * (ps / pl) ** (gm / (2 * g))
        head, tail = ul - cl, us - csl
        if xi <= head:
            return (rl, ul, pl)
        if xi >= tail:
            return (rsl, us, ps)
        u = 2.0 / gp * (cl + gm / 2.0 * ul + xi)
        c = 2.0 / gp * (cl + gm / 2.0 * (ul - xi))
        return (rl * (c / cl) ** (2.0 / gm), u, pl * (c / cl) ** (2 * g / gm))

    # 接触间断右侧
    if ps > pr:  # 右激波
        rsr = rr * ((ps / pr + gm / gp) / (gm / gp * ps / pr + 1.0))
        sr = ur + cr * np.sqrt((gp / (2 * g)) * ps / pr + gm / (2 * g))
        return (rr, ur, pr) if xi >= sr else (rsr, us, ps)
    # 右稀疏波
    rsr = rr * (ps / pr) ** (1.0 / g)
    csr = cr * (ps / pr) ** (gm / (2 * g))
    head, tail = ur + cr, us + csr
    if xi >= head:
        return (rr, ur, pr)
    if xi <= tail:
        return (rsr, us, ps)
    u = 2.0 / gp * (-cr + gm / 2.0 * ur + xi)
    c = 2.0 / gp * (cr - gm / 2.0 * (ur - xi))
    return (rr * (c / cr) ** (2.0 / gm), u, pr * (c / cr) ** (2 * g / gm))


def sod_reference(nx=513, nt=41, T=0.2, x0=0.5):
    """Sod 激波管精确解：左 (1,0,1) 右 (0.125,0,0.1)，t in (0, T]。"""
    def build():
        pl, rl, ul = 1.0, 1.0, 0.0
        pr, rr, ur = 0.1, 0.125, 0.0
        x = np.linspace(0.0, 1.0, nx)
        t = np.linspace(0.0, T, nt)
        R = np.zeros((nx, nt))
        U = np.zeros((nx, nt))
        P = np.zeros((nx, nt))
        R[:, 0], U[:, 0], P[:, 0] = np.where(x < x0, rl, rr), 0.0, np.where(x < x0, pl, pr)
        for j, tj in enumerate(t[1:], start=1):
            for i, xi in enumerate(x):
                R[i, j], U[i, j], P[i, j] = _sample_riemann(
                    (xi - x0) / tj, pl, rl, ul, pr, rr, ur)
        return {"x": x, "t": t, "rho": R, "u": U, "p": P}

    return _cache("sod_023", build)


REFERENCE_BUILDERS = {
    "easy_poisson_2d_source_003": poisson_reference,
    "easy_advection_1d_periodic_005": advection_reference,
    "medium_burgers_inverse_viscosity_010": burgers_reference,
    "hard_allen_cahn_016": allen_cahn_reference,
    "hard_plus_euler_shock_023": sod_reference,
}


def self_test():
    ps, us = _riemann_star(1.0, 1.0, 0.0, 0.1, 0.125, 0.0)
    print(f"Sod star state: p*={ps:.5f} (expect ~0.30313), u*={us:.5f} (expect ~0.92745)")
    assert abs(ps - 0.30313) < 1e-3 and abs(us - 0.92745) < 1e-3

    adv = advection_reference()
    assert abs(adv["u"][:, 0] - np.sin(2 * np.pi * adv["x"])).max() < 1e-12

    bur = burgers_reference()
    # 已知性质：t≈0.5 时 x=0 处形成陡峭梯度，且解保持奇对称
    mid = np.argmin(np.abs(bur["t"] - 0.5))
    sym = np.abs(bur["u"] + bur["u"][::-1, :]).max()
    print(f"Burgers: max|u(x)+u(-x)|={sym:.2e} (odd symmetry), "
          f"max|u_x(0,t=0.5)| steep={np.abs(np.gradient(bur['u'][:, mid], bur['x'])).max():.1f}")
    assert sym < 1e-4

    ac = allen_cahn_reference()
    assert np.abs(ac["u"]).max() < 1.2, "Allen-Cahn 解应保持在 [-1,1] 附近"
    print(f"Allen-Cahn: range [{ac['u'].min():.3f}, {ac['u'].max():.3f}]")

    sod = sod_reference()
    print(f"Sod grid: rho range [{sod['rho'].min():.3f}, {sod['rho'].max():.3f}]")
    poisson_reference()
    print("All references built & cached OK ->", DATA_DIR)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        for tid, fn in REFERENCE_BUILDERS.items():
            fn()
            print("built", tid)
