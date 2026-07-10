#!/usr/bin/env python3
"""执行效度分析：PlanScore 能否预测执行结果（协议 §6 预注册分析）。

输入：
  --results      run_validation.py 的输出 CSV（arm 列为盲码 arm_xxxxxx）
  --arms         arms_v0.4.csv，列：task,arm,label,kind,parent_arm,scorer_only,
                 plan_score,capped[,capped_facets]；kind ∈ {natural,gold,template,ablation}
  --code-map     盲码映射 CSV（task,arm,label,code）；缺省自动探测
                 analysis_only/arm_code_map.csv，找不到则假定 results 已解盲
  --configs      臂 YAML 目录（H4b config 同一性检查）；缺省自动探测 configs/arms
  --facet-scores facet 级评分 CSV（辅助 2）；缺省自动探测
                 arms_text/generated/arms_scored_v0.4.csv
  --diversity    config_diversity.csv（§5.6 H4a 资格门）；缺省自动探测
输出（--outdir）：
  validity_summary.md   统计结果（含预注册判定）
  validity_scatter.png  主图：PlanScore vs log10 relL2
  per_task_spearman.csv / h4b_pairs.csv

预注册规则（docs/execution_validation_protocol_v0.4.md §6，冻结于 commit 8e7d3aa）：
  - H4a 主检验只用自然臂 N1–N6 + G + T；支持 H4a ⟺ 跨任务平均 ρ 的
    bootstrap 95% CI 上界 < 0；含 D 臂的全臂版本仅作次要报告。
  - H4b 配对 = 可执行消融臂 vs parent 同种子（Wilcoxon 单侧 greater）；
    转写后 config 与 parent 逐键相同的消融臂自动剔除并列明。
  - 发散/NaN 的 run 记 rel_l2 = 10（log10 = 1，比任何收敛结果都差）。
自检：python analyze_validity.py --demo
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats

DIVERGED_RELL2 = 10.0
MAIN_KINDS = ("natural", "gold", "template")  # H4a 主检验臂型
HERE = os.path.dirname(os.path.abspath(__file__))


def md(df):
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```\n" + df.to_string(index=False) + "\n```"


def unblind(res, code_map_csv, notes):
    """把 results 的盲码 arm 列映射回真实臂号；保留 blind_code 备审计。"""
    cmap = pd.read_csv(code_map_csv)
    res = res.rename(columns={"arm": "blind_code"})
    res = res.merge(cmap[["task", "code", "arm"]],
                    left_on=["task", "blind_code"], right_on=["task", "code"],
                    how="left").drop(columns=["code"])
    unmapped = res[res["arm"].isna()]["blind_code"].unique()
    if len(unmapped):
        raise SystemExit(f"结果中存在 code map 未收录的盲码，请核查: {list(unmapped)}")
    ran = set(map(tuple, res[["task", "blind_code"]].drop_duplicates().values))
    expected = set(map(tuple, cmap[["task", "code"]].values))
    missing = sorted(expected - ran)
    if missing:
        notes.append(f"code map 中 {len(missing)} 个臂尚无执行结果（运行不完整？）: "
                     + ", ".join(f"{t}/{c}" for t, c in missing))
    return res


def load(results_csv, arms_csv, code_map_csv, notes):
    res = pd.read_csv(results_csv)
    if code_map_csv:
        res = unblind(res, code_map_csv, notes)
    dup = res.duplicated(subset=["task", "arm", "seed"], keep="first")
    if dup.any():
        notes.append(f"剔除重复 (task,arm,seed) 行 {int(dup.sum())} 条（保留首条）")
        res = res[~dup]
    if "eval_error" in res.columns:
        n_err = res["eval_error"].notna() & (res["eval_error"].astype(str).str.strip() != "")
        if n_err.any():
            notes.append(f"{int(n_err.sum())} 条 run 带 eval_error（按发散规则记 rel_l2=10）")
    res["rel_l2"] = pd.to_numeric(res["rel_l2"], errors="coerce")
    res.loc[(res["diverged"] == 1) | res["rel_l2"].isna(),
            "rel_l2"] = DIVERGED_RELL2
    res["log_rel_l2"] = np.log10(res["rel_l2"].clip(lower=1e-12))
    arms = pd.read_csv(arms_csv)
    df = res.merge(arms, on=["task", "arm"], how="left", validate="m:1",
                   suffixes=("", "_arms"))
    missing = df[df["plan_score"].isna()]["arm"].unique()
    if len(missing):
        notes.append(f"arms 缺少 plan_score，剔除: {list(missing)}")
        df = df.dropna(subset=["plan_score"])
    if "scorer_only" in df.columns:
        bad = df[df["scorer_only"].astype(str) == "True"]["arm"].unique()
        if len(bad):
            notes.append(f"警告：scorer_only 臂出现在执行结果里（不应发生）: {list(bad)}")
    return df


def arm_level(df):
    """种子聚合：每 (task, arm) 取 log10 relL2 的中位数。"""
    agg = dict(log_rel_l2=("log_rel_l2", "median"),
               plan_score=("plan_score", "first"),
               capped=("capped", "first"),
               kind=("kind", "first"),
               n_seeds=("seed", "nunique"),
               diverged_frac=("diverged", "mean"))
    if "label" in df.columns:
        agg["label"] = ("label", "first")
    return df.groupby(["task", "arm"], as_index=False).agg(**agg)


def seed_deficits(arm_df, notes):
    """协议 §5.5：自然/G/T 臂 ≥2 种子，消融臂 ≥3 种子。"""
    need = arm_df["kind"].map(lambda k: 3 if k == "ablation" else 2)
    short = arm_df[arm_df["n_seeds"] < need]
    if len(short):
        notes.append("种子数不足协议最低要求: "
                     + ", ".join(f"{r.task}/{r.arm}({r.n_seeds})"
                                 for r in short.itertuples()))


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


def h4a_verdict(table, mean_rho, ci):
    n_dir = int((table["rho"] < 0).sum())
    n_in = int(table["rho"].notna().sum())
    supported = np.isfinite(ci[1]) and ci[1] < 0
    verdict = ("**支持 H4a**（CI 上界 < 0）" if supported
               else "**未证实 H4a**（CI 上界 ≥ 0，如实报告，不做事后子集挑选）")
    return (f"跨任务平均 ρ = {mean_rho:.3f}，bootstrap 95% CI "
            f"[{ci[0]:.3f}, {ci[1]:.3f}]；方向一致（ρ<0）任务 {n_dir}/{n_in}。\n\n"
            f"预注册判定：{verdict}")


def config_identical_ablations(arms, code_map_csv, configs_dir, notes):
    """协议 §4：转写后 config 与 parent 逐键相同的消融臂剔除出 H4b 并列明。"""
    if not (code_map_csv and configs_dir and os.path.isdir(configs_dir)):
        return set()
    try:
        import yaml
    except ImportError:
        notes.append("pyyaml 不可用，跳过 config 同一性检查")
        return set()
    cmap = pd.read_csv(code_map_csv).set_index(["task", "arm"])["code"]

    def cfg(task, arm):
        try:
            path = os.path.join(configs_dir, cmap.loc[(task, arm)] + ".yaml")
        except KeyError:
            return None
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    identical = set()
    abl = arms[(arms["kind"] == "ablation")
               & (arms["scorer_only"].astype(str) != "True")]
    for r in abl.itertuples():
        c, p = cfg(r.task, r.arm), cfg(r.task, r.parent_arm)
        if c is not None and p is not None and c == p:
            identical.add((r.task, r.arm))
    if identical:
        notes.append("config 与 parent 逐键相同、剔除出 H4b 的消融臂: "
                     + ", ".join(f"{t}/{a}" for t, a in sorted(identical)))
    return identical


def paired_ablation(df, excluded=frozenset()):
    """同 (task, seed) 下 ablation vs parent 的配对差，Wilcoxon 符号秩。"""
    abl = df[df["kind"] == "ablation"]
    rows, diffs_all = [], {}
    for (task, arm_name), sub in abl.groupby(["task", "arm"]):
        if (task, arm_name) in excluded:
            continue
        diffs = []
        for _, r in sub.iterrows():
            parent = df[(df["task"] == r["task"]) & (df["arm"] == r["parent_arm"])
                        & (df["seed"] == r["seed"])]
            if len(parent):
                diffs.append(r["log_rel_l2"] - float(parent["log_rel_l2"].iloc[0]))
        row = {"task": task, "ablation": arm_name, "n_seeds": len(diffs),
               "median_delta_log10": float(np.median(diffs)) if diffs else np.nan}
        if len(diffs) >= 5:
            row["wilcoxon_p"] = float(stats.wilcoxon(
                diffs, alternative="greater").pvalue)
        else:
            row["wilcoxon_p"] = np.nan
        rows.append(row)
        diffs_all[(task, arm_name)] = diffs
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


def nu_report(df):
    """协议 §6：010 另报 |ν̂−ν|/ν（臂级种子中位数）。"""
    sub = df[df["task"].str.contains("burgers_inverse", na=False)]
    if not len(sub) or "nu_rel_err" not in sub.columns:
        return None
    sub = sub.copy()
    sub["nu_rel_err"] = pd.to_numeric(sub["nu_rel_err"], errors="coerce")
    g = sub.groupby("arm", as_index=False).agg(
        kind=("kind", "first"), plan_score=("plan_score", "first"),
        nu_rel_err_median=("nu_rel_err", "median"),
        log_rel_l2=("log_rel_l2", "median"))
    return g.sort_values("nu_rel_err_median")


def facet_analysis(arm_df, facet_csv):
    """辅助 2：facet 级任务内 Spearman（仅主检验臂型），预期物理约束/训练策略最强。"""
    fs = pd.read_csv(facet_csv)
    need = {"task_id", "model", "facet", "score"}
    if not need.issubset(fs.columns):
        return None
    piv = (fs.pivot_table(index=["task_id", "model"], columns="facet",
                          values="score", aggfunc="first").reset_index())
    sub = arm_df[arm_df["kind"].isin(MAIN_KINDS)]
    if "label" not in sub.columns:
        return None
    m = sub.merge(piv, left_on=["task", "label"],
                  right_on=["task_id", "model"], how="inner")
    facets = [c for c in piv.columns if c not in ("task_id", "model")]
    rows = []
    for facet in facets:
        rhos = []
        for task, s in m.groupby("task"):
            if s[facet].nunique() < 2 or s["log_rel_l2"].nunique() < 2:
                continue
            r, _ = stats.spearmanr(s[facet], s["log_rel_l2"])
            if np.isfinite(r):
                rhos.append(r)
        rows.append({"facet": facet, "n_tasks": len(rhos),
                     "mean_rho": float(np.mean(rhos)) if rhos else np.nan})
    return pd.DataFrame(rows).sort_values("mean_rho")


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
            arms.append({"task": task, "arm": arm, "label": arm,
                         "plan_score": round(score, 1),
                         "capped": int(score < 15), "kind": kind,
                         "parent_arm": "gold_1" if kind == "ablation" else "",
                         "scorer_only": False})
            for seed in range(3):
                err = 10 ** (-0.12 * score + rng.normal(0, 0.25))
                rows.append({"task": task, "arm": arm, "config": arm, "seed": seed,
                             "diverged": 0, "rel_l2": err})
    rp, ap_ = os.path.join(tmpdir, "demo_results.csv"), os.path.join(tmpdir, "demo_arms.csv")
    pd.DataFrame(rows).to_csv(rp, index=False)
    pd.DataFrame(arms).to_csv(ap_, index=False)
    return rp, ap_


def autodetect(explicit, relpath):
    if explicit == "none":
        return None
    if explicit:
        return explicit
    cand = os.path.join(HERE, relpath)
    return cand if os.path.exists(cand) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results")
    ap.add_argument("--arms")
    ap.add_argument("--code-map", help="盲码映射 CSV；'none' 表示 results 已解盲")
    ap.add_argument("--configs", help="臂 YAML 目录（config 同一性检查）")
    ap.add_argument("--facet-scores", help="facet 级评分 CSV（辅助 2）")
    ap.add_argument("--diversity", help="config_diversity.csv（H4a 资格门）")
    ap.add_argument("--outdir", default="analysis_v0.4")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        os.makedirs(args.outdir, exist_ok=True)
        args.results, args.arms = make_demo(args.outdir)
        args.code_map = args.configs = args.facet_scores = args.diversity = "none"
        print("demo inputs ->", args.results, args.arms)
    assert args.results and args.arms, "--results 与 --arms 必填（或用 --demo）"
    code_map = autodetect(args.code_map, "analysis_only/arm_code_map.csv")
    configs_dir = autodetect(args.configs, "configs/arms")
    facet_csv = autodetect(args.facet_scores,
                           "arms_text/generated/arms_scored_v0.4.csv")
    diversity_csv = autodetect(args.diversity, "config_diversity.csv")

    os.makedirs(args.outdir, exist_ok=True)
    notes = []
    df = load(args.results, args.arms, code_map, notes)
    arm_df = arm_level(df)
    seed_deficits(arm_df, notes)

    # H4a 资格门（§5.6）：自然臂配置零方差的题剔除
    eligible = set(arm_df["task"].unique())
    if diversity_csv:
        div = pd.read_csv(diversity_csv)
        drop = set(div[div["h4a_eligible"] != 1]["task"])
        if drop & eligible:
            notes.append(f"§5.6 多样性门剔除出 H4a 的题: {sorted(drop & eligible)}")
        eligible -= drop

    main_df = arm_df[arm_df["kind"].isin(MAIN_KINDS)
                     & arm_df["task"].isin(eligible)]
    table, mean_rho, ci = within_task_spearman(main_df)
    verdict = h4a_verdict(table, mean_rho, ci)
    table_all, mean_rho_all, ci_all = within_task_spearman(arm_df)

    arms_meta = pd.read_csv(args.arms)
    identical = config_identical_ablations(arms_meta, code_map, configs_dir, notes)
    abl_table, pooled, pooled_p = paired_ablation(df, identical)
    cap = capped_comparison(arm_df)
    nu = nu_report(df)
    facet = facet_analysis(arm_df, facet_csv) if facet_csv else None

    table.to_csv(os.path.join(args.outdir, "per_task_spearman.csv"), index=False)
    abl_table.to_csv(os.path.join(args.outdir, "h4b_pairs.csv"), index=False)
    scatter(arm_df, os.path.join(args.outdir, "validity_scatter.png"))

    n_total = len(pd.read_csv(args.results))
    lines = ["# 执行效度分析（v0.4）", "",
             f"输入：{n_total} 条 run，臂级聚合后 {len(arm_df)} 臂 / "
             f"{arm_df['task'].nunique()} 题；发散 run 比例 "
             f"{df['diverged'].mean():.3f}。", "",
             "## H4a 主检验（仅 N1–N6 + G + T；预注册判定：CI 上界 < 0）", "",
             md(table), "",
             verdict, "",
             "### 次要报告：全臂版本（含 D 臂，循环论证风险，仅作参考）", "",
             md(table_all), "",
             f"全臂跨任务平均 ρ = {mean_rho_all:.3f}，CI "
             f"[{ci_all[0]:.3f}, {ci_all[1]:.3f}]", "",
             "## H4b 消融配对检验（ablation − parent，预期 Δ>0）", "",
             md(abl_table), "",
             f"合并配对 n={len(pooled)}，Wilcoxon 单侧 p = {pooled_p}", "",
             "## H4c capped vs uncapped（臂级）", "", str(cap), ""]
    if nu is not None:
        lines += ["## 010 反问题 ν 恢复（|ν̂−ν|/ν，种子中位数）", "", md(nu), ""]
    if facet is not None:
        lines += ["## 辅助：facet 级任务内相关（仅 N+G+T；预期 Physics "
                  "Constraints / Training Strategy 最强）", "", md(facet), ""]
    if notes:
        lines += ["## 审计注记", ""] + [f"- {n}" for n in notes] + [""]
    out_md = os.path.join(args.outdir, "validity_summary.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written ->", out_md)
    for n in notes:
        print("NOTE:", n)
    print(f"H4a main: mean rho = {mean_rho:.3f}, CI [{ci[0]:.3f}, {ci[1]:.3f}]")
    print(f"H4b pooled: n={len(pooled)}, p={pooled_p}")


if __name__ == "__main__":
    main()
