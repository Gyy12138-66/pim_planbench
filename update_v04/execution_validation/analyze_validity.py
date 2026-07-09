#!/usr/bin/env python3
"""执行效度分析：PlanScore 能否预测执行结果。

输入：
  --results  run_validation.py 的输出 CSV
  --arms     arm 元数据 CSV，列：task,arm,plan_score,capped,kind,parent_arm
             kind ∈ {natural, gold, template, ablation}
             parent_arm 仅 ablation 需要（配对检验的对照，一般是 gold）
输出（--outdir）：
  validity_summary.md   统计结果
  validity_scatter.png  主图：PlanScore vs log10 relL2
  per_task_spearman.csv

预注册规则：发散的 run 记 rel_l2 = 10（log10 = 1，比任何收敛结果都差）。
自检：python analyze_validity.py --demo
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats

DIVERGED_RELL2 = 10.0


def md(df):
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```\n" + df.to_string(index=False) + "\n```"


def load(results_csv, arms_csv):
    res = pd.read_csv(results_csv)
    arms = pd.read_csv(arms_csv)
    res["rel_l2"] = pd.to_numeric(res["rel_l2"], errors="coerce")
    res.loc[(res["diverged"] == 1) | res["rel_l2"].isna(),
            "rel_l2"] = DIVERGED_RELL2
    res["log_rel_l2"] = np.log10(res["rel_l2"].clip(lower=1e-12))
    df = res.merge(arms, on=["task", "arm"], how="left", validate="m:1")
    missing = df[df["plan_score"].isna()]["arm"].unique()
    if len(missing):
        print("WARN: arms 缺少 plan_score，将被剔除:", missing)
        df = df.dropna(subset=["plan_score"])
    return df


def arm_level(df):
    """种子聚合：每 (task, arm) 取 log10 relL2 的中位数。"""
    g = df.groupby(["task", "arm"], as_index=False).agg(
        log_rel_l2=("log_rel_l2", "median"),
        plan_score=("plan_score", "first"),
        capped=("capped", "first"),
        kind=("kind", "first"),
        n_seeds=("seed", "nunique"),
        diverged_frac=("diverged", "mean"))
    return g


def within_task_spearman(arm_df, boot=10000, rng_seed=0):
    rows = []
    per_task_rho = {}
    for task, sub in arm_df.groupby("task"):
        if sub["plan_score"].nunique() < 3:
            rows.append({"task": task, "n_arms": len(sub), "rho": np.nan,
                         "p": np.nan, "note": "score variance不足"})
            continue
        rho, p = stats.spearmanr(sub["plan_score"], sub["log_rel_l2"])
        per_task_rho[task] = rho
        rows.append({"task": task, "n_arms": len(sub),
                     "rho": rho, "p": p, "note": ""})
    table = pd.DataFrame(rows)

    # bootstrap: 各题内重采样 arm，重算 rho，再对题平均
    rng = np.random.default_rng(rng_seed)
    means = []
    tasks = [t for t in per_task_rho]
    for _ in range(boot):
        vals = []
        for task in tasks:
            sub = arm_df[arm_df["task"] == task]
            idx = rng.integers(0, len(sub), len(sub))
            s = sub.iloc[idx]
            if s["plan_score"].nunique() < 2 or s["log_rel_l2"].nunique() < 2:
                continue
            r, _ = stats.spearmanr(s["plan_score"], s["log_rel_l2"])
            if np.isfinite(r):
                vals.append(r)
        if vals:
            means.append(np.mean(vals))
    mean_rho = float(np.mean(list(per_task_rho.values()))) if per_task_rho else np.nan
    ci = (np.percentile(means, 2.5), np.percentile(means, 97.5)) if means else (np.nan, np.nan)
    return table, mean_rho, ci


def paired_ablation(df):
    """同 (task, seed) 下 ablation vs parent 的配对差，Wilcoxon 符号秩。"""
    abl = df[df["kind"] == "ablation"]
    rows, diffs_all = [], {}
    for arm_name, sub in abl.groupby("arm"):
        diffs = []
        for _, r in sub.iterrows():
            parent = df[(df["task"] == r["task"]) & (df["arm"] == r["parent_arm"])
                        & (df["seed"] == r["seed"])]
            if len(parent):
                diffs.append(r["log_rel_l2"] - float(parent["log_rel_l2"].iloc[0]))
        if len(diffs) >= 5:
            w = stats.wilcoxon(diffs, alternative="greater")
            rows.append({"ablation": arm_name, "n_pairs": len(diffs),
                         "median_delta_log10": float(np.median(diffs)),
                         "wilcoxon_p": float(w.pvalue)})
        else:
            rows.append({"ablation": arm_name, "n_pairs": len(diffs),
                         "median_delta_log10": float(np.median(diffs)) if diffs else np.nan,
                         "wilcoxon_p": np.nan})
        diffs_all[arm_name] = diffs
    pooled = [d for v in diffs_all.values() for d in v]
    pooled_p = (float(stats.wilcoxon(pooled, alternative="greater").pvalue)
                if len(pooled) >= 6 else np.nan)
    return pd.DataFrame(rows), pooled, pooled_p


def capped_comparison(arm_df):
    a = arm_df[arm_df["capped"] == 1]["log_rel_l2"]
    b = arm_df[arm_df["capped"] == 0]["log_rel_l2"]
    if len(a) >= 3 and len(b) >= 3:
        u = stats.mannwhitneyu(a, b, alternative="greater")
        return {"n_capped": len(a), "n_uncapped": len(b),
                "median_capped": float(a.median()), "median_uncapped": float(b.median()),
                "mannwhitney_p": float(u.pvalue)}
    return {"n_capped": len(a), "n_uncapped": len(b), "mannwhitney_p": np.nan}


def scatter(arm_df, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"natural": "o", "gold": "*", "template": "s", "ablation": "v"}
    tasks = sorted(arm_df["task"].unique())
    cmap = plt.get_cmap("tab10")
    for i, task in enumerate(tasks):
        sub = arm_df[arm_df["task"] == task]
        parts = task.split("_")
        short = "_".join(parts[1:-1]) if len(parts) > 2 else task
        for kind, mk in markers.items():
            s2 = sub[sub["kind"] == kind]
            if len(s2):
                ax.scatter(s2["plan_score"], s2["log_rel_l2"], marker=mk,
                           color=cmap(i % 10), s=70 if kind == "gold" else 40,
                           label=short if kind == "natural" else None,
                           alpha=0.85, edgecolors="none")
    ax.set_xlabel("PlanScore (out of 25)")
    ax.set_ylabel("log10 relative L2 error")
    ax.legend(fontsize=8, title="task")
    ax.set_title("Execution validity: PlanScore vs execution error")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)


def make_demo(tmpdir):
    """合成数据自检：构造 rho<0 的假结果，验证管线端到端可跑。"""
    rng = np.random.default_rng(42)
    tasks = ["taskA", "taskB", "taskC"]
    rows, arms = [], []
    for task in tasks:
        for j in range(10):
            score = rng.uniform(8, 25)
            kind = ["natural", "gold", "template", "ablation"][min(j, 3) if j < 4 else 0]
            arm = f"{kind}_{j}"
            arms.append({"task": task, "arm": arm, "plan_score": round(score, 1),
                         "capped": int(score < 15), "kind": kind,
                         "parent_arm": "gold_1" if kind == "ablation" else ""})
            for seed in range(3):
                err = 10 ** (-0.12 * score + rng.normal(0, 0.25))
                rows.append({"task": task, "arm": arm, "config": arm, "seed": seed,
                             "diverged": 0, "rel_l2": err})
    rp, ap_ = os.path.join(tmpdir, "demo_results.csv"), os.path.join(tmpdir, "demo_arms.csv")
    pd.DataFrame(rows).to_csv(rp, index=False)
    pd.DataFrame(arms).to_csv(ap_, index=False)
    return rp, ap_


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results")
    ap.add_argument("--arms")
    ap.add_argument("--outdir", default="analysis_v0.4")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        os.makedirs(args.outdir, exist_ok=True)
        args.results, args.arms = make_demo(args.outdir)
        print("demo inputs ->", args.results, args.arms)
    assert args.results and args.arms, "--results 与 --arms 必填（或用 --demo）"

    os.makedirs(args.outdir, exist_ok=True)
    df = load(args.results, args.arms)
    arm_df = arm_level(df)

    table, mean_rho, ci = within_task_spearman(arm_df)
    abl_table, pooled, pooled_p = paired_ablation(df)
    cap = capped_comparison(arm_df)
    table.to_csv(os.path.join(args.outdir, "per_task_spearman.csv"), index=False)
    scatter(arm_df, os.path.join(args.outdir, "validity_scatter.png"))

    lines = ["# 执行效度分析（v0.4）", "",
             "## 任务内 Spearman ρ（PlanScore vs log10 relL2，预期为负）", "",
             md(table), "",
             f"**跨任务平均 ρ = {mean_rho:.3f}**，bootstrap 95% CI "
             f"[{ci[0]:.3f}, {ci[1]:.3f}]", "",
             "## 消融配对检验（ablation − parent，预期 Δ>0）", "",
             md(abl_table), "",
             f"合并配对 n={len(pooled)}，Wilcoxon 单侧 p = {pooled_p}", "",
             "## capped vs uncapped", "", str(cap), ""]
    out_md = os.path.join(args.outdir, "validity_summary.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written ->", out_md)
    print(f"mean within-task Spearman rho = {mean_rho:.3f}, CI {ci}")


if __name__ == "__main__":
    main()
