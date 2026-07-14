#!/usr/bin/env python3
"""构建修订项 #2 的基线臂（T / S1 / S2 / GOLD）→ 评分器输入 CSV。

四类臂 × 26 题 × 5 facet（行格式与 execution_validation/build_arms.py 一致）：

  T     通用模板计划（arms_text/T_template.json 原文，一份全题复用）
        —— d2gd 要求的 template baseline 全题投放
  S1    关键词堆砌·黑盒：只允许使用公开信息——公开题面词汇 + 公开 rubric
        （docs/rubric_v0.3.md）词汇。模拟"读了 rubric 来套分"的对手
        （PdEo 的 rubric-matching text 质疑）。无结构关键词罗列，非连贯计划。
  S2    关键词堆砌·白盒（最坏情形）：直接堆砌评分器内部线索词表
        （FACET_CORE_CUES + SYNONYMS + 各门控词）。对手读过评分器源码。
  GOLD  私有参考字段的确定性渲染（字段→facet 映射复用评分器
        reference_items() 同一映射），oracle 天花板锚点——它见过私有参考，
        不冒充"专家手写计划"。

输出：generated/baseline_arms_input_v0.4.csv
用法：python3 build_baseline_arms.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scorer_mirror as sm

ROOT = sm.ROOT
FROZEN = sm.FROZEN
GEN = HERE / "generated"
PANEL_CSV = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv"
TASKS_PUBLIC = ROOT / "dataset/tasks_public_v0.3.jsonl"
RUBRIC = ROOT / "docs/rubric_v0.3.md"
T_TEMPLATE = ROOT / "update_v04/execution_validation/arms_text/T_template.json"

FACETS = [
    ("Problem Formalization", "problem_formalization"),
    ("Physics Constraints", "physics_constraints"),
    ("Model Choice", "model_choice"),
    ("Training Strategy", "training_strategy"),
    ("Validation Failure Risks", "validation_failure_risks"),
]

MISS_PHRASES = ["missing", "unspecified", "not specified", "must be specified",
                "if available"]


def dedup(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def tokens(text: str, limit: int = 10**9) -> list[str]:
    out = dedup(re.findall(r"[a-z][a-z0-9-]{3,}", text.lower()))
    return out[:limit]


def rubric_vocab() -> dict[str, list[str]]:
    """S1 词表：公开 rubric 的通用节 + 对应 facet 节的 token（黑盒对手可见）。"""
    text = RUBRIC.read_text(encoding="utf-8")
    head, _, rest = text.partition("## Facets")
    body, _, _ = rest.partition("## Scoring Examples")
    general = tokens(head, 150)
    sections: dict[str, list[str]] = {}
    for chunk in re.split(r"\n### ", body)[1:]:
        name, _, sec = chunk.partition("\n")
        key = re.sub(r"[^a-z]", "", name.lower())  # "Validation & Failure Risks" 归一
        sections[key] = tokens(sec, 150)
    vocab = {}
    for fname, _fid in FACETS:
        key = re.sub(r"[^a-z]", "", fname.lower())
        if key not in sections:
            raise SystemExit(f"rubric 中找不到 facet 节: {fname}")
        vocab[fname] = dedup(sections[key] + general)
    return vocab


# S2 白盒词表：评分器内部线索 + 门控词（转录自 scorer_mirror，与冻结评分器同源）
S2_EXTRA = {
    "problem_formalization": (sm._PF_GOVERNING + sm._PF_KNOWN + sm._PF_TARGET
                              + sm._PF_DOMAIN + sm._PF_TASK_TYPE
                              + sm._PF_HANDLES_MISSING),
    "physics_constraints": [],
    "model_choice": [],
    "training_strategy": [],
    "validation_failure_risks": sm._VFR_RISK_MARKERS + sm._VFR_VALIDATION_MARKERS,
}


def s1_text(fname: str, task: dict, vocab: dict[str, list[str]]) -> str:
    task_terms = dedup(
        tokens(task["problem"]) + tokens(" ".join(task.get("tags", [])))
        + tokens(task["pde_system"]))
    return (f"{fname} plan for the {task['pde_system']} task. Rubric terms: "
            + ", ".join(vocab[fname])
            + ". Task terms: " + ", ".join(task_terms)
            + ". Missing information must be specified before execution; "
              "any assumption is labeled as an assumption.")


def s2_text(fname: str, fid: str) -> str:
    syn_flat = [cue for cues in FROZEN.SYNONYMS.values() for cue in cues]
    words = dedup(list(FROZEN.FACET_CORE_CUES[fid]) + S2_EXTRA[fid]
                  + MISS_PHRASES + syn_flat)
    return f"{fname}: " + ", ".join(words) + "."


def gold_text(reference: dict, fid: str) -> str:
    return "; ".join(FROZEN.reference_items(reference, fid))


def main() -> int:
    GEN.mkdir(exist_ok=True)
    with PANEL_CSV.open(encoding="utf-8-sig", newline="") as f:
        panel = list(csv.DictReader(f))
    columns = list(panel[0].keys())
    meta = {}
    for r in panel:
        meta.setdefault(r["task_id"], {k: r[k] for k in
                                       ("difficulty", "domain", "task_type", "pde_system")})

    tasks = {t["id"]: t for t in
             (json.loads(l) for l in TASKS_PUBLIC.read_text(encoding="utf-8").splitlines()
              if l.strip())}
    references = sm.load_references()
    template = json.loads(T_TEMPLATE.read_text(encoding="utf-8"))["facets"]
    vocab = rubric_vocab()

    task_ids = sorted(meta)
    if set(task_ids) != set(tasks) or set(task_ids) != set(references):
        raise SystemExit("面板任务、公开任务、私有参考三者的任务集合不一致")

    rows = []
    for tid in task_ids:
        for fname, fid in FACETS:
            texts = {
                "BASE/T": template[fname],
                "BASE/S1": s1_text(fname, tasks[tid], vocab),
                "BASE/S2": s2_text(fname, fid),
                "BASE/GOLD": gold_text(references[tid], fid),
            }
            for arm, answer in texts.items():
                row = {c: "" for c in columns}
                row.update(meta[tid])
                row.update({"task_id": tid, "model": arm,
                            "prompt_setting": "baselines_v0.4", "facet": fname,
                            "facet_id": fid, "model_answer": answer,
                            "schema_valid": "True"})
                rows.append(row)

    out = GEN / "baseline_arms_input_v0.4.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    print(f"baseline_arms_input_v0.4.csv: {len(rows)} rows "
          f"({len(task_ids)} tasks x 4 arms x 5 facets) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
