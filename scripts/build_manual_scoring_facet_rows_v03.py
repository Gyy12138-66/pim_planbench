#!/usr/bin/env python3
"""Build full v0.3 facet-level manual scoring rows as CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

TASKS_PATH = Path("dataset/tasks_public_v0.3.jsonl")
REFERENCES_PATH = Path("dataset/references_private_v0.3.jsonl")
DEFAULT_OUTPUT_PATH = Path("outputs/scoring_v0.3/manual_scoring_facet_rows_v0.3.csv")

FACET_ORDER = [
    ("Problem Formalization", "problem_formalization"),
    ("Physics Constraints", "physics_constraints"),
    ("Model Choice", "model_choice"),
    ("Training Strategy", "training_strategy"),
    ("Validation Failure Risks", "validation_failure_risks"),
]

MODEL_FILES = [
    {
        "model": "deepseek-ai/DeepSeek-V4-Flash",
        "path": Path("runs/pilot_v0.3/normalized/deepseek-ai_DeepSeek-V4-Flash__canonical_v0.3.jsonl"),
    },
    {
        "model": "Pro/moonshotai/Kimi-K2.6",
        "path": Path("runs/pilot_v0.3/normalized/Pro_moonshotai_Kimi-K2.6__canonical_v0.3.jsonl"),
    },
    {
        "model": "Pro/zai-org/GLM-4.7",
        "path": Path("runs/pilot_v0.3/normalized/Pro_zai-org_GLM-4.7__canonical_v0.3.jsonl"),
    },
]

FIELDNAMES = [
    "task_id",
    "difficulty",
    "domain",
    "task_type",
    "pde_system",
    "model",
    "prompt_setting",
    "facet",
    "facet_id",
    "model_answer",
    "reference_answer",
    "assistant_view",
    "scoring_standard",
    "human_score_0_5",
    "human_error_tags",
    "human_notes",
]

SCORING_STANDARDS = {
    "problem_formalization": (
        "0=无可用形式化；1=只复述题面；2=识别部分变量/目标但有重大遗漏；"
        "3=基本正确但不完整；4=明确区分未知量、已知量、数据、域和任务目标；"
        "5=完整精确，并在不编造条件的前提下标出缺失规格。"
    ),
    "physics_constraints": (
        "0=遗漏或写错核心物理约束；1=只泛泛说满足 PDE；"
        "2=包含部分约束但漏 IC/BC/观测/特殊约束；3=主要 residual 与条件基本正确；"
        "4=明确给出 residual、作用区域、IC/BC/观测和物理假设；"
        "5=进一步识别兼容性、守恒、散度、变系数、正则性等任务特异要求。"
    ),
    "model_choice": (
        "0=无合适模型；1=泛称 NN/PINN；2=模型可行但理由弱；"
        "3=模型类别、输入输出和基本理由正确；"
        "4=架构与 PDE 类型、数据、导数、约束和正/反问题匹配；"
        "5=能针对高频、刚性、守恒、多尺度、复杂几何或可辨识性做任务感知选择。"
    ),
    "training_strategy": (
        "0=无可用训练方案；1=只泛称训练/最小化误差；2=有部分 loss 但漏关键项；"
        "3=包含 PDE、IC/BC/数据 loss、采样和优化；"
        "4=含归一化、Adam+L-BFGS、loss balancing、稳定性或监控；"
        "5=针对刚性、高频、长时程、边界层、多尺度、inverse/noisy 等困难给出具体训练策略。"
    ),
    "validation_failure_risks": (
        "0=无验证或风险分析；1=泛泛说检查精度；2=有部分验证但不任务特异；"
        "3=包含参考解/held-out/residual/IC-BC 检查和常见 PINN 风险；"
        "4=包含任务特异物理一致性指标与失败模式；"
        "5=深入说明不可验证内容、可辨识性、缺失条件、高频/守恒/散度/刚性等细节风险。"
    ),
}

CUE_SETS = {
    "problem_formalization": [
        "known",
        "unknown",
        "parameter",
        "domain",
        "geometry",
        "field",
        "forward",
        "inverse",
        "variable",
        "identify",
        "missing",
    ],
    "physics_constraints": [
        "pde",
        "residual",
        "equation",
        "initial",
        "boundary",
        "dirichlet",
        "neumann",
        "periodic",
        "constraint",
        "conservation",
        "divergence",
        "incompressible",
        "mass",
    ],
    "model_choice": [
        "pinn",
        "physics-informed",
        "neural",
        "mlp",
        "operator",
        "fourier",
        "siren",
        "architecture",
        "network",
        "domain decomposition",
        "weak",
    ],
    "training_strategy": [
        "loss",
        "residual",
        "data",
        "initial",
        "boundary",
        "sampling",
        "collocation",
        "optimizer",
        "adam",
        "l-bfgs",
        "weight",
        "normalize",
        "adaptive",
    ],
    "validation_failure_risks": [
        "validate",
        "validation",
        "residual",
        "error",
        "compare",
        "risk",
        "failure",
        "identifiability",
        "conservation",
        "divergence",
        "stability",
        "reference",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_OUTPUT_PATH,
        help="Output CSV path. Defaults to outputs/scoring_v0.3/manual_scoring_facet_rows_v0.3.csv.",
    )
    return parser.parse_args()


def read_jsonl(relative_path: Path) -> list[dict[str, Any]]:
    path = ROOT / relative_path
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def format_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(part for part in (format_value(item) for item in value) if part)
    if isinstance(value, dict):
        return " | ".join(
            f"{key}: {formatted}"
            for key, item in value.items()
            if (formatted := format_value(item))
        )
    return str(value)


def cap_rules_for_facet(reference: dict[str, Any], facet_id: str) -> list[str]:
    rules = []
    for rule in reference.get("facet_cap_rules", []):
        if facet_id in rule.get("affected_facets", []):
            condition = rule.get("condition", "")
            max_score = rule.get("max_score", "")
            rationale = rule.get("rationale", "")
            rules.append(f"{condition} => max {max_score}. {rationale}".strip())
    return rules


def reference_for_facet(reference: dict[str, Any], facet_id: str) -> str:
    pieces: list[str] = []
    critical = reference.get("critical_points", {}).get(facet_id, [])
    if critical:
        pieces.append(f"critical_points: {format_value(critical)}")

    if facet_id == "problem_formalization":
        pieces.extend(
            [
                f"variables: {format_value(reference.get('variables'))}",
                f"known_parameters: {format_value(reference.get('known_parameters'))}",
                f"unknowns: {format_value(reference.get('unknowns'))}",
                f"domain_spec: {format_value(reference.get('domain_spec'))}",
                f"parameter_values: {format_value(reference.get('parameter_values'))}",
            ]
        )
    elif facet_id == "physics_constraints":
        pieces.extend(
            [
                f"canonical_pde: {format_value(reference.get('canonical_pde'))}",
                f"constraints: {format_value(reference.get('constraints'))}",
                f"reference_conditions: {format_value(reference.get('reference_conditions'))}",
            ]
        )
    elif facet_id == "model_choice":
        pieces.append(f"acceptable_model_choices: {format_value(reference.get('acceptable_model_choices'))}")
    elif facet_id == "training_strategy":
        pieces.extend(
            [
                f"expected_loss_terms: {format_value(reference.get('expected_loss_terms'))}",
                f"expected_training_strategy: {format_value(reference.get('expected_training_strategy'))}",
            ]
        )
    elif facet_id == "validation_failure_risks":
        pieces.extend(
            [
                f"expected_validation: {format_value(reference.get('expected_validation'))}",
                f"failure_traps: {format_value(reference.get('failure_traps'))}",
            ]
        )

    if reference.get("scoring_note"):
        pieces.append(f"scoring_note: {reference['scoring_note']}")
    cap_rules = cap_rules_for_facet(reference, facet_id)
    if cap_rules:
        pieces.append(f"facet_cap_rules: {format_value(cap_rules)}")
    return " || ".join(part for part in pieces if part)


def make_assistant_view(answer: str, facet_id: str, record: dict[str, Any]) -> str:
    lowered = answer.lower()
    cues = [cue for cue in CUE_SETS[facet_id] if cue in lowered]
    missing = [cue for cue in CUE_SETS[facet_id] if cue not in lowered]
    schema_note = "schema_valid=True"
    if record.get("schema_valid") is False:
        schema_note = f"schema_valid=False: {format_value(record.get('missing_section_keys') or record.get('parse_error'))}"
    cue_note = f"mentions cues: {', '.join(cues[:12])}" if cues else "mentions cues: none detected"
    missing_note = f"check possible missing cues: {', '.join(missing[:8])}" if missing else "check possible missing cues: none"
    return f"AUTO_REVIEW: {schema_note} | {cue_note} | {missing_note} | This is a preliminary reading aid, not an automatic score."


def build_rows() -> list[dict[str, str]]:
    tasks = read_jsonl(TASKS_PATH)
    references_by_id = {row["id"]: row for row in read_jsonl(REFERENCES_PATH)}
    rows: list[dict[str, str]] = []

    for model_file in MODEL_FILES:
        records = read_jsonl(model_file["path"])
        records_by_id = {row["id"]: row for row in records}
        missing_tasks = [task["id"] for task in tasks if task["id"] not in records_by_id]
        if missing_tasks:
            raise ValueError(f"Missing normalized answers for {model_file['model']}: {missing_tasks}")

        for task in tasks:
            task_id = task["id"]
            reference = references_by_id.get(task_id)
            if reference is None:
                raise ValueError(f"Missing private reference for {task_id}")
            record = records_by_id[task_id]
            answer_by_facet = record.get("answer") or {}

            for facet_name, facet_id in FACET_ORDER:
                answer = str(answer_by_facet.get(facet_name, ""))
                rows.append(
                    {
                        "task_id": task_id,
                        "difficulty": task.get("difficulty", ""),
                        "domain": task.get("domain", ""),
                        "task_type": task.get("task_type", ""),
                        "pde_system": task.get("pde_system", ""),
                        "model": record.get("model") or model_file["model"],
                        "prompt_setting": record.get("prompt_setting", ""),
                        "facet": facet_name,
                        "facet_id": facet_id,
                        "model_answer": answer,
                        "reference_answer": reference_for_facet(reference, facet_id),
                        "assistant_view": make_assistant_view(answer, facet_id, record),
                        "scoring_standard": SCORING_STANDARDS[facet_id],
                        "human_score_0_5": "",
                        "human_error_tags": "",
                        "human_notes": "",
                    }
                )
    return rows


def main() -> int:
    args = parse_args()
    rows = build_rows()
    expected_rows = len(read_jsonl(TASKS_PATH)) * len(MODEL_FILES) * len(FACET_ORDER)
    if len(rows) != expected_rows:
        raise ValueError(f"Unexpected row count: {len(rows)} != {expected_rows}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({"output": str(args.output), "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
