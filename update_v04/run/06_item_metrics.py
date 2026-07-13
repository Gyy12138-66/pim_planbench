#!/usr/bin/env python3
"""Item 级区分度指标（可复现版）：docs/item_analysis_v0.4.md 的数据源。

每题：spread（6 模型总分极差）、item-rest Spearman、facet 满分率、
cap 触发行数、hard-trap 触发数、难度残差。重写题验收（item_analysis §6）
复用本脚本：--scored-csv 指向重打分后的新 CSV 对照即可。

用法：python3 update_v04/run/06_item_metrics.py
     [--scored-csv <facet 行 CSV>] [--out <csv>]
"""
import argparse
import os
import re

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_SCORED = os.path.join(
    ROOT, "scores", "pilot_v0.3", "ModelOutput_all_existing_scored_v0.3.csv")
DEFAULT_OUT = os.path.join(HERE, "..", "docs", "item_metrics_v0.4.csv")

FACET_COLS = {"Model Choice": "mc_full", "Training Strategy": "ts_full",
              "Physics Constraints": "pc_full", "Problem Formalization": "pf_full",
              "Validation Failure Risks": "vr_full"}


def cap_kinds(rationale):
    kinds = []
    for pat, k in [("pf_strict_cap", "pf_strict"), ("generic", "generic"),
                   ("hallucin", "hallucination"), ("wrong.task", "wrong_task"),
                   ("trap|shock|periodic|divergence|helmholtz|cahn|darcy", "hard_trap")]:
        if re.search(pat, rationale, re.I) and "cap" in rationale.lower():
            kinds.append(k)
    return "|".join(kinds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored-csv", default=DEFAULT_SCORED)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    f = pd.read_csv(args.scored_csv)
    f["cap_kinds"] = f["score_rationale"].astype(str).map(cap_kinds)

    t = f.groupby(["task_id", "difficulty", "model"])["score"].sum().reset_index()
    piv = t.pivot_table(index=["task_id", "difficulty"], columns="model", values="score")
    totals = piv.sum(axis=0)
    grand = piv.values.mean()

    rows = []
    for (task, diff), r in piv.iterrows():
        rest = totals - r
        disc = stats.spearmanr(r.values, rest.values)[0] if r.std() > 0 else np.nan
        sub = f[f["task_id"] == task]
        fac_full = sub.groupby("facet")["score"].apply(lambda s: (s == 5).mean())
        row = dict(task=task, difficulty=diff, mean=round(r.mean(), 1),
                   spread=r.max() - r.min(),
                   item_rest_rho=round(disc, 2) if np.isfinite(disc) else np.nan)
        for facet, col in FACET_COLS.items():
            row[col] = round(fac_full.get(facet, np.nan), 2)
        row.update(n_cap_rows=int((sub["cap_kinds"] != "").sum()),
                   hard_trap_fired=int(sub["cap_kinds"].str.contains("hard_trap").sum()),
                   mean_dev=round(r.mean() - grand, 1))
        rows.append(row)

    d = pd.DataFrame(rows).sort_values(["spread", "item_rest_rho"])
    d.to_csv(args.out, index=False)
    print(d.to_string(index=False))
    print()
    print("全局 facet 满分率:", round((f["score"] == 5).mean(), 3), "（目标 <0.15）")
    print("难度层均分:", t.groupby("difficulty")["score"].mean().round(1).to_dict())
    print("分差≤3 的题数:", int((d["spread"] <= 3).sum()), "/", len(d))
    print("written ->", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
