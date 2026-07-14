#!/usr/bin/env python3
"""批次 1 验收判据（item_analysis §6 预注册；由 09_panel_batch1.sh 末步调用）。

  C1  facet 满分率 < 15%（全库非 canary；v0.3 现状 38.1%）
  C2  重写题（revision != unchanged）spread 中位数 ≥ 4
  C3  [已废除 2026-07-15 修正案] 难度层均分仅作描述性报告（脱钩=论文发现）
  C4  每道 claim-capable 重写题至少 1 个模型触发任务特异 cap
      （claim_findings 非空；全 cue 题 002/006/012 无 claims，记 N/A）

exit 0 = 全部适用判据 PASS（题集可冻结，进批次 2）；exit 2 = 有判据 FAIL
（不达标题回炉修订——见逐题表）。

用法：python3 update_v04/run/09b_acceptance_batch1.py
     [--scored-csv <path>] [--references <path>]
"""
import argparse
import csv
import json
import os
from collections import defaultdict
from statistics import mean, median

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_SCORED = os.path.join(ROOT, "scores", "pilot_v0.4",
                              "ModelOutput_batch1_scored_v0.4.csv")
DEFAULT_REFS = os.path.join(ROOT, "dataset", "references_private_v0.4.jsonl")
DIFF_ORDER = ["easy", "medium", "hard", "hard_plus"]
ALL_CUE_TASKS = {"easy_wave_1d_icbc_002", "easy_reaction_diffusion_1d_006",
                 "medium_wave_sparse_sensors_012"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored-csv", default=DEFAULT_SCORED)
    ap.add_argument("--references", default=DEFAULT_REFS)
    args = ap.parse_args()

    with open(args.references, encoding="utf-8") as f:
        refs = {d["id"]: d for d in (json.loads(l) for l in f if l.strip())}
    with open(args.scored_csv, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if not r["task_id"].startswith("canary_")]

    totals = defaultdict(lambda: defaultdict(float))   # task -> model -> total
    claim_hits = defaultdict(set)                      # task -> {model}
    diff_of, full, nrows = {}, 0, 0
    for r in rows:
        s = float(r["score"])
        totals[r["task_id"]][r["model"]] += s
        diff_of[r["task_id"]] = r["difficulty"]
        nrows += 1
        full += (s == 5)
        if r.get("claim_findings"):
            claim_hits[r["task_id"]].add(r["model"])

    revised = [t for t in totals if refs[t].get("revision") != "unchanged"]
    spread = {t: max(m.values()) - min(m.values()) for t, m in totals.items()}

    c1_rate = full / nrows
    c1 = c1_rate < 0.15
    c2_med = median(spread[t] for t in revised) if revised else float("nan")
    c2 = bool(revised) and c2_med >= 4
    layer_mean = {d: mean(v for t, m in totals.items() if diff_of[t] == d
                          for v in m.values()) for d in DIFF_ORDER}
    # C3 已废除（预注册修正案，作者裁决 2026-07-15，rework_batch1_v0.4.md P-C）：
    # 难度标签沿承数值执行难度，对规划得分无预测力——V 型倒挂跨版本（v0.3 item_analysis）
    # 跨量纲（原始/strict-five）复现。降级为描述性报告，不再计入验收判定；
    # "规划难度与执行难度脱钩"作为论文实证发现报告，支点密度 tier 另行入元数据。
    c3_monotone = all(layer_mean[a] > layer_mean[b]
                      for a, b in zip(DIFF_ORDER, DIFF_ORDER[1:]))
    c4_applicable = [t for t in revised if t not in ALL_CUE_TASKS]
    c4_missing = [t for t in c4_applicable if not claim_hits.get(t)]
    c4 = not c4_missing

    print("== 批次 1 预注册验收（item_analysis §6）==")
    print(f"C1 facet 满分率 <15%:   {'PASS' if c1 else 'FAIL'}  ({c1_rate:.1%})")
    print(f"C2 重写题 spread 中位≥4: {'PASS' if c2 else 'FAIL'}  (中位 {c2_med:g}, n={len(revised)})")
    print(f"C3 难度层均分[已废除,仅报告]: {'单调' if c3_monotone else '非单调'}  ("
          + " > ".join(f"{d} {layer_mean[d]:.1f}" for d in DIFF_ORDER)
          + ")  修正案 2026-07-15：脱钩转论文发现")
    print(f"C4 重写题 claim cap≥1:  {'PASS' if c4 else 'FAIL'}"
          + (f"  未触发: {sorted(c4_missing)}" if c4_missing else "")
          + f"  (适用 {len(c4_applicable)} 题, 全 cue 题 {len(ALL_CUE_TASKS)} 记 N/A)")
    print("\n逐题（重写题）: task | spread | 满分率 | claim cap 模型数")
    for t in sorted(revised):
        sub = [float(r["score"]) for r in rows if r["task_id"] == t]
        print(f"  {t} | {spread[t]:g} | {sum(1 for s in sub if s == 5)/len(sub):.0%}"
              f" | {len(claim_hits.get(t, set()))}")

    ok = c1 and c2 and c4
    print(f"\n结论: {'PASS —— 题集可冻结,进批次 2' if ok else 'FAIL —— 不达标题回炉修订'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
