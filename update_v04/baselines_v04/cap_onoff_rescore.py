#!/usr/bin/env python3
"""cap 规则开/关重打分（修订项 #2：cap 消融）。

四种变体（镜像打分，守卫断言先行）：
  full        默认（pf_strict 内部 cap + 外部 generic/hard-trap cap 全开）
  no_ext      关外部 cap（generic + hard-trap）
  no_pf       关 pf_strict 内部 cap
  no_caps     全关（纯 Eq.5 覆盖分）

报告：每模型均分变化、模型排名 Kendall tau、cap 触发原因分布、
基线臂（T/S1/S2/GOLD）在各变体下的均分——cap 对反模板防线的贡献一目了然。

输出：generated/cap_onoff_v0.4.csv + generated/sections/20_cap_onoff.md
用法：python3 cap_onoff_rescore.py（须先跑 score_baselines.py）
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scorer_mirror as sm

GEN = HERE / "generated"
SECTIONS = GEN / "sections"

VARIANTS = {  # name -> (pf_strict_caps, external_caps)
    "full": (True, True),
    "no_ext": (True, False),
    "no_pf": (False, True),
    "no_caps": (False, False),
}


def main() -> int:
    SECTIONS.mkdir(parents=True, exist_ok=True)
    references = sm.load_references()
    panel_rows = sm.read_rows(sm.PANEL_SCORED)
    base_rows = sm.read_rows(GEN / "baseline_arms_scored_v0.4.csv")

    n = sm.verify_against_frozen(panel_rows, references)
    n += sm.verify_against_frozen(base_rows, references)
    print(f"守卫断言 PASS: {n} 行镜像逐行等值")

    feats = [sm.build_features(r, references[r["task_id"]])
             for r in panel_rows + base_rows]
    models = sorted({r["model"] for r in panel_rows})
    arms = sorted({r["model"] for r in base_rows})

    # (variant, model) -> task -> total
    totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    changed_rows = Counter()
    for f in feats:
        s_full = sm.score_from_features(f)
        for vname, (pf_on, ext_on) in VARIANTS.items():
            s = sm.score_from_features(f, pf_strict_caps=pf_on, external_caps=ext_on)
            totals[(vname, f["model"])][f["task_id"]] += s
            if vname != "full" and s != s_full and f["model"] in models:
                changed_rows[vname] += 1

    out_csv = GEN / "cap_onoff_v0.4.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["variant", "who", "kind", "mean_total_25"])
        for vname in VARIANTS:
            for m in models:
                w.writerow([vname, m, "model",
                            round(mean(totals[(vname, m)].values()), 2)])
            for a in arms:
                w.writerow([vname, a, "arm",
                            round(mean(totals[(vname, a)].values()), 2)])

    # cap 触发原因分布（面板行，full 变体下实际生效的 cap）
    reason_counter = Counter()
    pf_cap_rows = 0
    for f, row in zip(feats, panel_rows + base_rows):
        if f["model"] not in models:
            continue
        raw_nocap = sm.score_from_features(f, pf_strict_caps=False, external_caps=False)
        if sm.score_from_features(f, pf_strict_caps=True, external_caps=False) < raw_nocap:
            pf_cap_rows += 1
        if f["cap_min"] is not None and sm.score_from_features(
                f, pf_strict_caps=True, external_caps=False) > f["cap_min"]:
            for reason in f["cap_reasons"]:
                reason_counter[reason] += 1

    default_rank = {m: mean(totals[("full", m)].values()) for m in models}
    lines = ["## cap 规则开/关重打分（cap 消融）", ""]
    lines.append("| 变体 | " + " | ".join(m.split("/")[-1] for m in models)
                 + " | 排名 τ vs 默认 | 变动行数/780 |")
    lines.append("|---|" + "---|" * (len(models) + 2))
    for vname in VARIANTS:
        rank = {m: mean(totals[(vname, m)].values()) for m in models}
        tau = sm.kendall_tau(default_rank, rank)
        cells = " | ".join(f"{rank[m]:.2f}" for m in models)
        lines.append(f"| {vname} | {cells} | {tau:.3f} | {changed_rows.get(vname, 0)} |")
    lines.append("")
    lines.append("基线臂在各变体下的均分/25（cap 对反模板防线的贡献）：")
    lines.append("")
    lines.append("| 变体 | " + " | ".join(a.split("/")[-1] for a in arms) + " |")
    lines.append("|---|" + "---|" * len(arms))
    for vname in VARIANTS:
        cells = " | ".join(f"{mean(totals[(vname, a)].values()):.2f}" for a in arms)
        lines.append(f"| {vname} | {cells} |")
    lines += ["", f"pf_strict 内部 cap 生效行数（面板 780 行）：{pf_cap_rows}",
              "", "外部 cap（generic/hard-trap）触发原因 Top 10（面板行）：", ""]
    for reason, cnt in reason_counter.most_common(10):
        lines.append(f"- {cnt} 次：{reason}")
    lines += ["", "全量数据：`generated/cap_onoff_v0.4.csv`。", ""]
    (SECTIONS / "20_cap_onoff.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"cap 开/关汇总 -> {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
