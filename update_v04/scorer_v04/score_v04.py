#!/usr/bin/env python3
"""PlanScore v0.4 评分管线（schema §3.4 消费契约的落地）。

    scores   = coverage_layer(...)     # v0.3 给分层原样（含 pf_strict 与 VFR 下限）
    findings = verify_entry(ref, ...)  # claim_verifier_v04，读 verifiable_claims
    final    = apply_caps(scores, claim_caps ∪ generic_caps)

三类 trigger 的执行方式（单一事实源 = references JSONL 的 facet_cap_rules）：
  claim    机器执行——verifier findings → on_contradiction → rule_id → 封顶
  generic  机器执行——v0.3 generic_cap 检测器判定触发，封顶值取自数据侧
           cap_generic_pinn 规则（检测器语义沿 v0.3：封顶检出所在 facet）
  cue      本管线**不机器执行**（D2：代码不再内嵌逐题条件）；逐行输出
           `cue_rules_pending` 列，供人工复核 / LLM-judge 层消费。
           v0.3 硬编码 hard_trap_caps 路径在本管线中废止。

纪律：
  - 冻结评分器 scripts/score_3modeloutput_v03.py 只 import 其函数,绝不修改
  - 漂移守卫：revision=="unchanged" 的题,coverage 分在 v0.4 参考与 v0.3
    参考下必须逐行等值,不等即中止
  - canary_ 前缀任务照常打分但从两份 summary 中排除
  - score_rationale 保留 "cap<= n:" 记法（06_item_metrics 兼容）

用法：
  python score_v04.py --input <facet 行 CSV> --output <scored CSV>
                      [--references dataset/references_private_v0.4.jsonl]
                      [--summary <csv>] [--task-summary <csv>]
迁移核验（提交前必跑）：python check_score_v04.py
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import claim_verifier_v04 as cv4

FROZEN_PATH = ROOT / "scripts" / "score_3modeloutput_v03.py"
DEFAULT_REFERENCES = ROOT / "dataset" / "references_private_v0.4.jsonl"
V03_REFERENCES = ROOT / "dataset" / "references_private_v0.3.jsonl"
CANARY_PREFIX = "canary_"


def load_frozen():
    spec = importlib.util.spec_from_file_location("score_v03_frozen", FROZEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FROZEN = load_frozen()


def _rules_by_trigger(ref):
    out = defaultdict(list)
    for r in ref.get("facet_cap_rules", []):
        out[r["trigger"]].append(r)
    return out


def _cue_pending(rules, facet_id):
    ids = [r["rule_id"] for r in rules.get("cue", [])
           if not r["affected_facets"] or facet_id in r["affected_facets"]]
    return "|".join(ids)


def drift_guard(rows, refs_v04):
    """unchanged 题的 coverage 分在 v0.4/v0.3 参考下逐行等值,防参考字段漂移。"""
    refs_v03 = {r["id"]: r for r in FROZEN.read_jsonl(V03_REFERENCES)}
    checked = 0
    for row in rows:
        ref = refs_v04.get(row["task_id"])
        if ref is None or ref.get("revision") != "unchanged":
            continue
        s_new, _ = FROZEN.raw_score(row, ref)
        s_old, _ = FROZEN.raw_score(row, refs_v03[row["task_id"]])
        if s_new != s_old:
            raise SystemExit(
                f"漂移守卫失败: unchanged 题 {row['task_id']} / {row['model']} / "
                f"{row['facet_id']} coverage {s_old} -> {s_new}（v0.4 参考字段被改动?）")
        checked += 1
    return checked


def score_rows(rows, refs, strict_five=0.0):
    """逐行打分；返回 scored rows（新增 score/score_rationale/cue_rules_pending/claim_findings 列）。

    strict_five>0 时启用 v0.4 量程重标定（rework_batch1 提案 P-A）：5 分要求
    specificity ≥ 阈值，否则封到 4。这是全局重标定而非 claim cap——冻结 v0.3
    raw_score 的 cue/长度/短语项对前沿模型饱和（白送 ≈3.65 分），specificity≥0.55
    即可凑满 5（批次 1 满分率 33.5%）。默认关闭；回归套件在关闭态运行。
    """
    groups = defaultdict(dict)   # (task, model) -> {facet_display: row}
    for row in rows:
        groups[(row["task_id"], row["model"])][row["facet"]] = row

    for (task, model), facet_rows in groups.items():
        ref = refs.get(task)
        if ref is None:
            raise SystemExit(f"无 v0.4 私有参考: {task}")
        rules = _rules_by_trigger(ref)
        texts = {fname: r["model_answer"] for fname, r in facet_rows.items()}
        findings = cv4.verify_entry(ref, texts)
        rule_index = {r["rule_id"]: r for r in ref.get("facet_cap_rules", [])}

        # claim 层：finding → rule → (facet, max_score, note)
        claim_caps = defaultdict(list)   # facet_id -> [(max_score, note, finding_desc)]
        for f in findings:
            rule = rule_index.get(f.rule_id)
            if rule is None:
                raise SystemExit(f"{task}: finding 引用未定义规则 {f.rule_id}")
            affected = rule["affected_facets"] or [f.facet_id]
            for fid in affected:
                claim_caps[fid].append(
                    (rule["max_score"], f"cap<= {rule['max_score']}: {f.detail} [{f.rule_id}]",
                     f"{f.kind}:{f.claim_id}"))

        for fname, row in facet_rows.items():
            fid = row["facet_id"] or FROZEN.FACET_IDS[fname]
            score, rationale = FROZEN.raw_score(row, ref)
            notes = []

            if strict_five > 0 and score == 5:
                sp, _m, _t = FROZEN.specificity_ratio(
                    FROZEN.norm(row["model_answer"]), ref, fid)
                if sp < strict_five:
                    score = 4
                    notes.append(
                        f"strict5<=4: specificity {sp:.2f} < {strict_five:.2f} [strict_five_v04]")

            answer = FROZEN.norm(row["model_answer"])
            g_cap, g_reason = FROZEN.generic_cap(answer, fid)
            if g_cap is not None:
                for r in rules.get("generic", []):
                    if score > r["max_score"]:
                        score = r["max_score"]
                        notes.append(f"cap<= {r['max_score']}: {g_reason} [{r['rule_id']}]")

            for max_score, note, _ in sorted(claim_caps.get(fid, [])):
                if score > max_score:
                    score = max_score
                    notes.append(note)

            row["human_score_0_5"] = str(score)
            row["score"] = str(score)
            row["score_rationale"] = rationale + ("; " + "; ".join(notes) if notes else "")
            row["cue_rules_pending"] = _cue_pending(rules, fid)
            row["claim_findings"] = "|".join(d for _, _, d in claim_caps.get(fid, []))

        # 自检：与 verifier 官方 apply_caps 的封顶结果一致（注意其仅比较 claim 层）
        base = {FROZEN.FACET_IDS[fn]: int(facet_rows[fn]["score"]) for fn in facet_rows}
        # （generic 层在 base 里已生效,claim 层已生效 → 官方 apply_caps 应为不动点）
        official, _ = cv4.apply_caps(dict(base), findings, ref)
        if official != base:
            raise SystemExit(f"封顶自检失败: {task}/{model} {base} != {official}")

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, default=None)
    ap.add_argument("--task-summary", type=Path, default=None)
    ap.add_argument(
        "--strict-five-threshold", type=float, default=0.0,
        help="v0.4 量程重标定（提案 P-A）：5 分要求 specificity≥该值，0=关闭（默认）。批次 1 校准值 0.80。")
    args = ap.parse_args()

    refs = cv4.load_references(args.references)
    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"task_id", "model", "facet", "facet_id", "model_answer"}
    missing = required - set(rows[0].keys())
    if missing:
        raise SystemExit(f"输入缺列: {sorted(missing)}")

    n_guard = drift_guard(rows, refs)
    scored = score_rows(rows, refs, strict_five=args.strict_five_threshold)

    fieldnames = list(scored[0].keys())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(scored)

    stat_rows = [r for r in scored if not r["task_id"].startswith(CANARY_PREFIX)]
    if args.summary:
        FROZEN.write_summary(args.summary, stat_rows)
    if args.task_summary:
        FROZEN.write_task_summary(args.task_summary, stat_rows)

    scores = [float(r["score"]) for r in stat_rows]
    print(json.dumps({
        "input": str(args.input), "output": str(args.output),
        "rows": len(scored), "stat_rows(non-canary)": len(stat_rows),
        "drift_guard_rows": n_guard,
        "avg_score": round(sum(scores) / len(scores), 3),
        "claim_capped_rows": sum(1 for r in stat_rows if r["claim_findings"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
