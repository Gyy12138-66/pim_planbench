#!/usr/bin/env python3
"""score_v04 管线迁移核验（提交/启用前必跑，exit 0 = 通过）。

硬不变量（55 臂集，5 题执行子集）：
  I1  每题 cap 后 D2/D3 总分 < 同题 G 总分（R5 语义在新管线下维持）
  I2  G / T / N1–N6 / D1 臂零 claim cap（误伤门）
  I3  score_v04 自身守卫（漂移守卫 + 封顶自检）不触发

差异审计（报告，不判失败——D2 政策变更的显式记账）：
  - cue-dropped：v0.3 硬编码 hard-trap 外部 cap 在新管线不再自动执行的行
    （新分 ≥ 旧分；这些规则以 trigger:"cue" 挂起，见 cue_rules_pending 列）
  - claim-added：新 claim 层压低分数的行（v0.3 scored CSV 无 claim 层）
  - 面板 unchanged 题子集（9 题 × 6 模型）同口径对比

输出：score_v04_migration_report.md
用法：python check_score_v04.py
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import claim_verifier_v04 as cv4

ARMS_INPUT = ROOT / "update_v04/execution_validation/arms_text/generated/arms_input_v0.4.csv"
ARMS_V03_SCORED = ROOT / "update_v04/execution_validation/arms_text/generated/arms_scored_v0.4.csv"
PANEL_V03_SCORED = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_scored_v0.3.csv"
OUT_DIR = HERE / "generated"
REPORT = HERE / "score_v04_migration_report.md"


def read(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def score_with_v04(input_csv, output_csv):
    subprocess.run(
        [sys.executable, str(HERE / "score_v04.py"), "--input", str(input_csv),
         "--output", str(output_csv)],
        check=True)
    return read(output_csv)


def arm_id(model):
    return model.split("/", 1)[1] if model.startswith("ARM/") else "N"


def diff_audit(old_rows, new_rows, label, lines):
    key = lambda r: (r["task_id"], r["model"], r["facet"])
    old = {key(r): r for r in old_rows}
    cue_dropped, claim_added, other = [], [], []
    for r in new_rows:
        o = old.get(key(r))
        if o is None:
            continue
        s_new, s_old = float(r["score"]), float(o["score"])
        if s_new == s_old:
            continue
        entry = f"{r['task_id']} / {r['model']} / {r['facet']}: {s_old:g} -> {s_new:g}"
        if s_new > s_old and "cap<= " in o["score_rationale"]:
            cue_dropped.append(entry)
        elif s_new < s_old and r.get("claim_findings"):
            claim_added.append(entry)
        else:
            other.append(entry)
    lines += [f"### {label}", "",
              f"- cue-dropped（v0.3 硬编码外部 cap 挂起为 cue 规则）：{len(cue_dropped)} 行",
              f"- claim-added（新断言层压分）：{len(claim_added)} 行",
              f"- 其他差异：{len(other)} 行" + ("（须逐行解释!）" if other else ""), ""]
    for name, group in (("cue-dropped", cue_dropped), ("claim-added", claim_added),
                        ("其他", other)):
        for e in group:
            lines.append(f"  - [{name}] {e}")
    lines.append("")
    return other


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    failures, lines = [], ["# score_v04 迁移核验报告", ""]

    # ---- 55 臂集 ----
    new_arms = score_with_v04(ARMS_INPUT, OUT_DIR / "arms_scored_by_score_v04.csv")
    totals, claim_capped = defaultdict(float), defaultdict(int)
    for r in new_arms:
        k = (r["task_id"], r["model"])
        totals[k] += float(r["score"])
        if r.get("claim_findings"):
            claim_capped[k] += 1

    tasks = sorted({t for t, _ in totals})
    for task in tasks:
        g = next(v for (t, m), v in totals.items() if t == task and m == "ARM/G")
        for (t, m), v in sorted(totals.items()):
            if t != task:
                continue
            aid = m.split("/", 1)[1] if m.startswith("ARM/") else "N"
            if aid in ("D2", "D3") and v >= g:
                failures.append(f"I1 未分离: {task}/{aid} {v} >= G {g}")
            if aid not in ("D2", "D3") and claim_capped.get((t, m)):
                failures.append(f"I2 误伤: {task}/{m} 被 claim cap {claim_capped[(t, m)]} 行")

    lines += ["## 55 臂不变量", "",
              f"- I1 D2/D3 < G：{'PASS' if not any(f.startswith('I1') for f in failures) else 'FAIL'}",
              f"- I2 非消融臂零 claim cap：{'PASS' if not any(f.startswith('I2') for f in failures) else 'FAIL'}",
              ""]
    diff_audit(read(ARMS_V03_SCORED), new_arms, "55 臂：v0.3 管线 vs score_v04", lines)

    # ---- 面板 unchanged 题子集 ----
    refs = cv4.load_references(ROOT / "dataset/references_private_v0.4.jsonl")
    unchanged = {t for t, r in refs.items() if r.get("revision") == "unchanged"}
    panel = [r for r in read(PANEL_V03_SCORED) if r["task_id"] in unchanged]
    panel_in = OUT_DIR / "panel_unchanged_input.csv"
    with panel_in.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(panel[0].keys()))
        w.writeheader()
        w.writerows(panel)
    new_panel = score_with_v04(panel_in, OUT_DIR / "panel_unchanged_scored_by_score_v04.csv")
    lines.append(f"## 面板 unchanged 题子集（{len(unchanged)} 题 × 6 模型 = {len(panel)} 行）")
    lines.append("")
    diff_audit(panel, new_panel, "面板 unchanged：v0.3 管线 vs score_v04", lines)

    ok = not failures
    lines.insert(2, f"**结论：{'PASS' if ok else f'{len(failures)} 项失败'}**")
    if failures:
        lines.insert(3, "")
        for f_ in failures:
            lines.insert(4, f"- {f_}")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{'PASS' if ok else 'FAIL'} -> {REPORT}")
    for f_ in failures:
        print("FAIL:", f_)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
