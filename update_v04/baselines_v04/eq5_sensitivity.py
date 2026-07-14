#!/usr/bin/env python3
"""Eq.5 常数敏感性分析（修订项 #2，回应 PdEo "constants unexplained with no ablation"）。

对 raw_score 的 9 个数值常数（scorer_mirror.DEFAULT_PARAMS）做两类扰动，
其余管线（门槛阈值、facet 规则、cap）保持默认：
  OAT   每常数单独 ×{0.8, 0.9, 1.1, 1.2}（36 次重打分）
  JOINT 9 常数联合均匀扰动 ±25%（200 次，随机种子固定 20260713）

指标：6 模型排名 Kendall tau vs 默认、排名是否完全不变、模型均分最大偏移。

输出：generated/eq5_sensitivity_v0.4.csv + generated/sections/30_eq5.md
用法：python3 eq5_sensitivity.py
"""
from __future__ import annotations

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scorer_mirror as sm

GEN = HERE / "generated"
SECTIONS = GEN / "sections"
OAT_MULTIPLIERS = [0.8, 0.9, 1.1, 1.2]
N_JOINT = 200
JOINT_SPAN = 0.25
SEED = 20260713


def model_means(feats, params):
    totals = defaultdict(lambda: defaultdict(float))
    for f in feats:
        totals[f["model"]][f["task_id"]] += sm.score_from_features(f, params)
    return {m: mean(t.values()) for m, t in totals.items()}


def main() -> int:
    SECTIONS.mkdir(parents=True, exist_ok=True)
    references = sm.load_references()
    rows = sm.read_rows(sm.PANEL_SCORED)
    sm.verify_against_frozen(rows, references)
    print("守卫断言 PASS: 780 行镜像逐行等值")

    feats = [sm.build_features(r, references[r["task_id"]]) for r in rows]
    default_means = model_means(feats, sm.DEFAULT_PARAMS)
    default_order = sorted(default_means, key=default_means.get, reverse=True)

    results = []  # dict rows for CSV

    def evaluate(kind, label, params):
        means = model_means(feats, params)
        tau = sm.kendall_tau(default_means, means)
        order = sorted(means, key=means.get, reverse=True)
        results.append({
            "kind": kind, "perturbation": label,
            "tau": round(tau, 4),
            "ranking_unchanged": int(sm.strict_inversions(default_means, means) == 0),
            "max_abs_delta_mean": round(max(abs(means[m] - default_means[m])
                                            for m in means), 3),
            "top1": order[0],
        })
        return tau

    for const in sm.DEFAULT_PARAMS:
        for mult in OAT_MULTIPLIERS:
            params = dict(sm.DEFAULT_PARAMS)
            params[const] = sm.DEFAULT_PARAMS[const] * mult
            evaluate("oat", f"{const}x{mult}", params)

    rng = random.Random(SEED)
    for i in range(N_JOINT):
        params = {k: v * (1 + rng.uniform(-JOINT_SPAN, JOINT_SPAN))
                  for k, v in sm.DEFAULT_PARAMS.items()}
        evaluate("joint", f"joint_{i:03d}", params)

    out_csv = GEN / "eq5_sensitivity_v0.4.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    oat = [r for r in results if r["kind"] == "oat"]
    joint = [r for r in results if r["kind"] == "joint"]
    worst_by_const = {}
    for r in oat:
        const = r["perturbation"].split("x")[0]
        worst_by_const[const] = min(worst_by_const.get(const, 1.0), r["tau"])

    lines = ["## Eq.5 常数敏感性", "",
             f"默认排名（26 题均分/25）：" + " > ".join(
                 f"{m.split('/')[-1]} {default_means[m]:.2f}" for m in default_order),
             "",
             "### OAT：每常数单独 ×{0.8, 0.9, 1.1, 1.2}",
             "",
             "| 常数 | 默认值 | 最差排名 τ | 无严格逆序的扰动数/4 |",
             "|---|---|---|---|"]
    for const, default in sm.DEFAULT_PARAMS.items():
        unchanged = sum(r["ranking_unchanged"] for r in oat
                        if r["perturbation"].split("x")[0] == const)
        lines.append(f"| {const} | {default} | {worst_by_const[const]:.3f} | {unchanged}/4 |")

    taus = [r["tau"] for r in joint]
    unchanged_frac = sum(r["ranking_unchanged"] for r in joint) / len(joint)
    top1_stable = sum(1 for r in joint if r["top1"] == default_order[0]) / len(joint)
    lines += [
        "",
        f"### 联合扰动：9 常数同时均匀 ±{JOINT_SPAN:.0%} × {N_JOINT} 次（种子 {SEED}）",
        "",
        f"- 排名 τ（tau-b，并列校正）：min {min(taus):.3f} / median {median(taus):.3f} "
        f"/ mean {mean(taus):.3f}",
        f"- 无严格逆序比例（默认严格序对零反转；默认排名中恰有一对并列，"
        f"脱离并列不计）：{unchanged_frac:.1%}；Top-1 不变比例：{top1_stable:.1%}",
        f"- 模型均分最大偏移（全部扰动中）：{max(r['max_abs_delta_mean'] for r in joint):.2f} / 25",
        "",
        "范围说明：仅扰动 Eq.5 的 9 个数值常数；长度/比例门槛与 facet 规则逻辑属规则结构，"
        "保持固定（cap 的消融见上一节）。全量数据：`generated/eq5_sensitivity_v0.4.csv`。",
        "",
    ]
    (SECTIONS / "30_eq5.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"敏感性数据 -> {out_csv}")
    print(f"joint tau: min={min(taus):.3f} median={median(taus):.3f} "
          f"unchanged={unchanged_frac:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
