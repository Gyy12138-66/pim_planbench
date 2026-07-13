#!/usr/bin/env python3
"""IAA 一致性分析（协议 iaa_protocol_v0.4.md §5 承诺的脚本，盲于数据定稿）。

输入：
  --scores     iaa_scores_raw.csv（annotator, task_id, answer_code, facet, score[, rationale]）
  --auto       可选：自动评分 CSV（task_id, answer_code, facet, score）
  --code-map   可选：answer_code → model 映射 CSV（task_id, answer_code, model），
               提供后计算模型排名 τ（人工均值 vs 自动）
输出（--outdir）：iaa_report_v0.4.md + iaa_metrics.csv

指标与判定（协议 §5，冻结后不得改动）：
  facet 级二次加权 κ（标注者两两）；全体 ordinal Krippendorff's α；
  标注者 vs 自动的加权 κ；模型排名 Kendall τ。
  substantial agreement ⟺ 汇总加权 κ ≥ 0.6 且 α ≥ 0.667；排名稳定 ⟺ τ ≥ 0.7。
自检：python3 analyze_iaa.py --demo
"""
import argparse
import itertools
import os

import numpy as np
import pandas as pd
from scipy import stats

K_LEVELS = 6  # 0-5 分制


def quadratic_weighted_kappa(a, b, k=K_LEVELS):
    """两评分序列的二次加权 κ。a, b: 等长 int 数组（0..k-1）。"""
    a, b = np.asarray(a, int), np.asarray(b, int)
    obs = np.zeros((k, k))
    for x, y in zip(a, b):
        obs[x, y] += 1
    n = obs.sum()
    if n == 0:
        return np.nan
    obs /= n
    exp = np.outer(obs.sum(1), obs.sum(0))
    w = np.array([[(i - j) ** 2 for j in range(k)] for i in range(k)]) / (k - 1) ** 2
    denom = (w * exp).sum()
    return 1.0 - (w * obs).sum() / denom if denom > 0 else np.nan


def krippendorff_alpha_ordinal(units):
    """ordinal Krippendorff's α。units: 列表，每项是一个单元内各标注者的分值列表。"""
    vals = sorted({v for u in units for v in u})
    idx = {v: i for i, v in enumerate(vals)}
    m = len(vals)
    coin = np.zeros((m, m))
    for u in units:
        mu = len(u)
        if mu < 2:
            continue
        for a, b in itertools.permutations(u, 2):
            coin[idx[a], idx[b]] += 1.0 / (mu - 1)
    n_c = coin.sum(1)
    n = n_c.sum()
    if n <= 1:
        return np.nan
    # ordinal 距离：δ_ck = (Σ_{g=c..k} n_g − (n_c+n_k)/2)²
    delta = np.zeros((m, m))
    for c in range(m):
        for k2 in range(m):
            lo, hi = min(c, k2), max(c, k2)
            delta[c, k2] = (n_c[lo:hi + 1].sum() - (n_c[c] + n_c[k2]) / 2) ** 2
    do = sum(coin[c, k2] * delta[c, k2] for c in range(m) for k2 in range(m) if c != k2) / n
    de = sum(n_c[c] * n_c[k2] * delta[c, k2] for c in range(m) for k2 in range(m) if c != k2) \
        / (n * (n - 1))
    return 1.0 - do / de if de > 0 else np.nan


def pair_pivot(df, ann_a, ann_b):
    """两标注者在共同 (task, answer_code, facet) 单元上的配对分值。"""
    a = df[df["annotator"] == ann_a].set_index(["task_id", "answer_code", "facet"])["score"]
    b = df[df["annotator"] == ann_b].set_index(["task_id", "answer_code", "facet"])["score"]
    common = a.index.intersection(b.index)
    return a.loc[common], b.loc[common]


def make_demo(outdir):
    rng = np.random.default_rng(3)
    facets = ["Problem Formalization", "Physics Constraints", "Model Choice",
              "Training Strategy", "Validation Failure Risks"]
    rows, auto_rows, map_rows = [], [], []
    for ti in range(12):
        task = f"task_{ti:02d}"
        for mi in range(6):
            code = f"ans_{ti:02d}_{mi}"
            map_rows.append(dict(task_id=task, answer_code=code, model=f"model_{mi}"))
            base = rng.uniform(1.5, 4.8)
            for facet in facets:
                true = np.clip(base + rng.normal(0, 0.5), 0, 5)
                for ann in ("A", "B"):
                    rows.append(dict(annotator=ann, task_id=task, answer_code=code,
                                     facet=facet,
                                     score=int(np.clip(round(true + rng.normal(0, 0.55)), 0, 5))))
                auto_rows.append(dict(task_id=task, answer_code=code, facet=facet,
                                      score=int(np.clip(round(true + rng.normal(0, 0.7)), 0, 5))))
    p = {k: os.path.join(outdir, f"demo_{k}.csv") for k in ("scores", "auto", "map")}
    pd.DataFrame(rows).to_csv(p["scores"], index=False)
    pd.DataFrame(auto_rows).to_csv(p["auto"], index=False)
    pd.DataFrame(map_rows).to_csv(p["map"], index=False)
    return p["scores"], p["auto"], p["map"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores")
    ap.add_argument("--auto")
    ap.add_argument("--code-map")
    ap.add_argument("--outdir", default="iaa_analysis_v0.4")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    if args.demo:
        args.scores, args.auto, args.code_map = make_demo(args.outdir)
        print("demo inputs ->", args.scores)
    assert args.scores, "--scores 必填（或 --demo）"

    df = pd.read_csv(args.scores)
    anns = sorted(df["annotator"].unique())
    assert len(anns) >= 2, "需要 ≥2 名标注者"

    # facet 级两两加权 κ
    rows = []
    kappas_all = []
    for pa, pb in itertools.combinations(anns, 2):
        for facet, sub in df.groupby("facet"):
            a, b = pair_pivot(sub, pa, pb)
            k = quadratic_weighted_kappa(a, b)
            rows.append(dict(pair=f"{pa}-{pb}", facet=facet, n=len(a),
                             weighted_kappa=round(k, 3)))
        a, b = pair_pivot(df, pa, pb)
        k_all = quadratic_weighted_kappa(a, b)
        kappas_all.append(k_all)
        rows.append(dict(pair=f"{pa}-{pb}", facet="(全体 facet 汇总)", n=len(a),
                         weighted_kappa=round(k_all, 3)))
    kappa_table = pd.DataFrame(rows)

    # Krippendorff α（全体 facet，ordinal）
    units = [list(g["score"]) for _, g in
             df.groupby(["task_id", "answer_code", "facet"]) if len(g) >= 2]
    alpha = krippendorff_alpha_ordinal(units)

    # vs 自动评分
    auto_table = None
    tau = np.nan
    if args.auto:
        auto = pd.read_csv(args.auto)
        both = pd.concat(
            [df, auto.assign(annotator="AUTO")[["annotator", "task_id",
                                                "answer_code", "facet", "score"]]],
            ignore_index=True)
        arow = []
        for ann in anns:
            a, b = pair_pivot(both, ann, "AUTO")
            arow.append(dict(pair=f"{ann}-AUTO", n=len(a),
                             weighted_kappa=round(quadratic_weighted_kappa(a, b), 3)))
        auto_table = pd.DataFrame(arow)
        if args.code_map:
            cmap = pd.read_csv(args.code_map)
            human = df.merge(cmap, on=["task_id", "answer_code"])
            hum_rank = human.groupby("model")["score"].mean()
            am = auto.merge(cmap, on=["task_id", "answer_code"])
            auto_rank = am.groupby("model")["score"].mean()
            models = hum_rank.index.intersection(auto_rank.index)
            tau = stats.kendalltau(hum_rank[models], auto_rank[models])[0]

    # 判定（协议 §5）
    kmean = float(np.nanmean(kappas_all))
    v1 = kmean >= 0.6 and alpha >= 0.667
    lines = ["# IAA 一致性分析报告（v0.4）", "",
             "## facet 级二次加权 κ（标注者两两）", "",
             kappa_table.to_markdown(index=False), "",
             f"**Krippendorff's α (ordinal, 全体) = {alpha:.3f}**", "",
             f"预注册判定 1：substantial external agreement "
             f"{'**成立**' if v1 else '**不成立**（如实报告，不做事后挑选）'}"
             f"（汇总 κ = {kmean:.3f}，阈值 0.6；α 阈值 0.667）", ""]
    if auto_table is not None:
        lines += ["## 标注者 vs 自动评分", "", auto_table.to_markdown(index=False), ""]
        if np.isfinite(tau):
            v2 = tau >= 0.7
            lines += [f"模型排名 Kendall τ（人工均值 vs 自动）= {tau:.3f}；"
                      f"预注册判定 2：排名稳定 {'**成立**' if v2 else '**不成立**'}"
                      f"（阈值 0.7）", ""]
    kappa_table.to_csv(os.path.join(args.outdir, "iaa_metrics.csv"), index=False)
    out_md = os.path.join(args.outdir, "iaa_report_v0.4.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written ->", out_md)
    print(f"κ(汇总)={kmean:.3f}  α={alpha:.3f}  τ={tau if np.isfinite(tau) else 'n/a'}")


if __name__ == "__main__":
    main()
