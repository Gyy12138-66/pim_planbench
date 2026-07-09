#!/usr/bin/env python3
"""Generate a readiness audit for PIM-PlanBench pilot results.

The audit is diagnostic, not a scorer. It checks whether the current task set,
private references, and pilot scores show enough coverage and discrimination to
support a paper-facing benchmark iteration.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable


FACET_ORDER = [
    "Problem Formalization",
    "Physics Constraints",
    "Model Choice",
    "Training Strategy",
    "Validation Failure Risks",
]

FAILURE_CATEGORIES = {
    "missing_or_hallucinated_conditions": [
        r"missing",
        r"unspecified",
        r"hallucinat",
        r"invent",
        r"\bic\b",
        r"\bbc\b",
        r"boundary",
        r"initial",
    ],
    "wrong_pde_or_wrong_physics": [
        r"wrong pde",
        r"confuses",
        r"drops",
        r"omits .*term",
        r"source term",
        r"nonlinear",
    ],
    "loss_or_constraint_omission": [
        r"loss",
        r"residual",
        r"penalty",
        r"constraint",
        r"enforce",
    ],
    "inverse_identifiability": [
        r"inverse",
        r"identifiability",
        r"non-unique",
        r"nonuniqu",
        r"sparse",
        r"noise",
        r"unknown parameter",
    ],
    "high_frequency_or_spectral_bias": [
        r"high-frequency",
        r"high frequency",
        r"oscillat",
        r"spectral",
        r"helmholtz",
        r"wave",
        r"fourier",
        r"siren",
    ],
    "stiffness_or_multiscale": [
        r"stiff",
        r"small",
        r"multiscale",
        r"high-contrast",
        r"boundary layer",
        r"sharp",
        r"interface",
    ],
    "conservation_or_divergence": [
        r"conservation",
        r"conserve",
        r"mass",
        r"divergence",
        r"incompressib",
        r"monopole",
    ],
    "geometry_or_boundary_complexity": [
        r"geometry",
        r"corner",
        r"staircase",
        r"maze",
        r"obstacle",
        r"boundary",
        r"radiation",
    ],
    "shock_or_discontinuity": [
        r"shock",
        r"discontinu",
        r"weak form",
        r"entropy",
        r"conservative",
        r"gibbs",
    ],
    "operator_or_family_generalization": [
        r"operator",
        r"family",
        r"generalization",
        r"neural operator",
        r"domain decomposition",
        r"coefficient-aware",
    ],
}


@dataclass(frozen=True)
class ScoreRow:
    task_id: str
    model: str
    facet: str
    score: float


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row is not an object at {path}:{line_no}")
            rows.append(row)
    return rows


def read_scores(path: Path) -> list[ScoreRow]:
    rows: list[ScoreRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"task_id", "model", "facet", "score"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required score columns in {path}: {sorted(missing)}")
        for line_no, row in enumerate(reader, start=2):
            score_text = (row.get("score") or "").strip()
            try:
                score = float(score_text)
            except ValueError as exc:
                raise ValueError(f"Invalid score at {path}:{line_no}: {score_text!r}") from exc
            if score < 0 or score > 5:
                raise ValueError(f"Score out of 0-5 range at {path}:{line_no}: {score}")
            rows.append(
                ScoreRow(
                    task_id=(row.get("task_id") or "").strip(),
                    model=(row.get("model") or "").strip(),
                    facet=(row.get("facet") or "").strip(),
                    score=score,
                )
            )
    return rows


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    materialized = [list(row) for row in rows]
    out = [
        "| " + " | ".join(md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in materialized:
        padded = row + [""] * (len(headers) - len(row))
        out.append("| " + " | ".join(md_escape(cell) for cell in padded[: len(headers)]) + " |")
    return "\n".join(out)


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def fmt(value: float, digits: int = 2) -> str:
    if math.isnan(value):
        return "NA"
    return f"{value:.{digits}f}"


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "NA"
    return f"{numerator / denominator * 100:.1f}%"


def safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else math.nan


def safe_pstdev(values: Iterable[float]) -> float:
    values = list(values)
    return pstdev(values) if len(values) > 1 else 0.0


def task_number(task_id: str) -> int:
    suffix = task_id.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else 10_000


def compact_list(values: Iterable[str], limit: int = 8) -> str:
    cleaned = [value for value in values if value]
    if len(cleaned) <= limit:
        return ", ".join(cleaned)
    return ", ".join(cleaned[:limit]) + f", +{len(cleaned) - limit} more"


def reference_text(task: dict[str, Any], reference: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "problem",
        "pde_system",
        "task_type",
        "domain",
        "difficulty",
    ):
        value = task.get(key)
        if value:
            parts.append(str(value))
    for key in (
        "canonical_pde",
        "failure_traps",
        "scoring_tags",
        "expected_loss_terms",
        "expected_training_strategy",
        "expected_validation",
        "review_flags",
    ):
        value = reference.get(key)
        if value:
            parts.append(json.dumps(value, ensure_ascii=False))
    for rule in reference.get("facet_cap_rules", []) or []:
        if isinstance(rule, dict):
            parts.append(str(rule.get("condition", "")))
            parts.append(str(rule.get("rationale", "")))
    return " ".join(parts).lower()


def category_hits(task: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    text = reference_text(task, reference)
    hits = []
    for category, patterns in FAILURE_CATEGORIES.items():
        if any(re.search(pattern, text) for pattern in patterns):
            hits.append(category)
    return hits


def summarize_distribution(rows: list[dict[str, Any]], key: str) -> list[tuple[str, int]]:
    return sorted(Counter(str(row.get(key, "unknown")) for row in rows).items(), key=lambda item: (-item[1], item[0]))


def build_audit(
    *,
    tasks: list[dict[str, Any]],
    references: list[dict[str, Any]],
    scores: list[ScoreRow],
    args: argparse.Namespace,
) -> str:
    root = Path(__file__).resolve().parents[1]
    tasks_by_id = {row["id"]: row for row in tasks}
    refs_by_id = {row["id"]: row for row in references}
    task_ids = sorted(tasks_by_id, key=task_number)
    scored_task_ids = sorted({row.task_id for row in scores}, key=task_number)
    models = sorted({row.model for row in scores})
    facets = FACET_ORDER

    score_by_combo: dict[tuple[str, str, str], float] = {}
    for row in scores:
        score_by_combo[(row.task_id, row.model, row.facet)] = row.score

    expected_score_rows = len(scored_task_ids) * len(models) * len(facets)
    missing_score_rows = [
        (task_id, model, facet)
        for task_id in scored_task_ids
        for model in models
        for facet in facets
        if (task_id, model, facet) not in score_by_combo
    ]

    unscored_public_tasks = [task_id for task_id in task_ids if task_id not in scored_task_ids]
    scored_unknown_tasks = [task_id for task_id in scored_task_ids if task_id not in tasks_by_id]
    missing_references = [task_id for task_id in task_ids if task_id not in refs_by_id]

    by_model: dict[str, list[float]] = defaultdict(list)
    by_difficulty: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_facet_model: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_facet: dict[str, list[float]] = defaultdict(list)
    task_model_totals: dict[tuple[str, str], float] = defaultdict(float)
    task_model_counts: dict[tuple[str, str], int] = defaultdict(int)

    for row in scores:
        task = tasks_by_id.get(row.task_id, {})
        difficulty = str(task.get("difficulty", "unknown"))
        by_model[row.model].append(row.score)
        by_difficulty[(row.model, difficulty)].append(row.score)
        by_facet_model[(row.facet, row.model)].append(row.score)
        by_facet[row.facet].append(row.score)
        task_model_totals[(row.task_id, row.model)] += row.score
        task_model_counts[(row.task_id, row.model)] += 1

    task_discrimination_rows = []
    ceiling_task_rows = []
    low_discrimination_task_rows = []
    for task_id in scored_task_ids:
        totals = [
            task_model_totals[(task_id, model)]
            for model in models
            if task_model_counts[(task_id, model)] == len(facets)
        ]
        if not totals:
            continue
        total_range = max(totals) - min(totals)
        total_mean = mean(totals)
        total_std = safe_pstdev(totals)
        task = tasks_by_id.get(task_id, {})
        row = {
            "task_id": task_id,
            "difficulty": task.get("difficulty", "unknown"),
            "task_type": task.get("task_type", "unknown"),
            "pde_system": task.get("pde_system", "unknown"),
            "mean_total": total_mean,
            "range_total": total_range,
            "std_total": total_std,
            "ceiling_models": sum(1 for total in totals if total >= args.task_ceiling_threshold),
        }
        task_discrimination_rows.append(row)
        if total_mean >= args.task_ceiling_threshold:
            ceiling_task_rows.append(row)
        if total_range <= args.low_task_range_threshold:
            low_discrimination_task_rows.append(row)

    facet_range_values: dict[str, list[float]] = defaultdict(list)
    low_discrimination_facet_rows = []
    for task_id in scored_task_ids:
        for facet in facets:
            values = [
                score_by_combo[(task_id, model, facet)]
                for model in models
                if (task_id, model, facet) in score_by_combo
            ]
            if len(values) < 2:
                continue
            score_range = max(values) - min(values)
            facet_range_values[facet].append(score_range)
            if score_range <= args.low_facet_range_threshold:
                low_discrimination_facet_rows.append(
                    {
                        "task_id": task_id,
                        "facet": facet,
                        "mean": mean(values),
                        "range": score_range,
                        "scores": values,
                    }
                )

    category_counter: Counter[str] = Counter()
    task_category_rows = []
    trap_counts = []
    cap_rule_counts = []
    review_flag_rows = []
    for task_id in task_ids:
        task = tasks_by_id[task_id]
        reference = refs_by_id.get(task_id, {})
        hits = category_hits(task, reference)
        category_counter.update(hits)
        traps = reference.get("failure_traps", []) or []
        cap_rules = reference.get("facet_cap_rules", []) or []
        review_flags = reference.get("review_flags", []) or []
        trap_counts.append((task_id, len(traps)))
        cap_rule_counts.append((task_id, len(cap_rules)))
        if review_flags:
            review_flag_rows.append((task_id, compact_list(map(str, review_flags), 4)))
        task_category_rows.append(
            (
                task_id,
                task.get("difficulty", "unknown"),
                task.get("task_type", "unknown"),
                len(traps),
                len(cap_rules),
                compact_list(hits, 5),
            )
        )

    score_counter = Counter(row.score for row in scores)
    ceiling_rows = [row for row in scores if row.score >= args.facet_ceiling_threshold]
    max_score_rows = [row for row in scores if row.score == 5]

    top_task_discrimination = sorted(task_discrimination_rows, key=lambda row: (-row["range_total"], row["task_id"]))[:10]
    weakest_task_discrimination = sorted(task_discrimination_rows, key=lambda row: (row["range_total"], -row["mean_total"], row["task_id"]))[:10]
    saturated_tasks = sorted(ceiling_task_rows, key=lambda row: (-row["mean_total"], row["range_total"], row["task_id"]))[:10]

    facet_summary_rows = []
    for facet in facets:
        values = by_facet[facet]
        ranges = facet_range_values.get(facet, [])
        facet_summary_rows.append(
            [
                facet,
                fmt(safe_mean(values)),
                fmt(safe_pstdev(values)),
                fmt(safe_mean(ranges)),
                fmt(min(ranges) if ranges else math.nan),
                fmt(max(ranges) if ranges else math.nan),
                pct(sum(1 for row in scores if row.facet == facet and row.score >= args.facet_ceiling_threshold), len(values)),
            ]
        )

    model_rows = []
    for model in models:
        values = by_model[model]
        model_rows.append(
            [
                model,
                len(values),
                fmt(safe_mean(values)),
                fmt(sum(values), 1),
                fmt(safe_pstdev(values)),
                pct(sum(1 for value in values if value >= args.facet_ceiling_threshold), len(values)),
                pct(sum(1 for value in values if value == 5), len(values)),
            ]
        )

    difficulty_rows = []
    difficulties = [difficulty for difficulty, _count in summarize_distribution(tasks, "difficulty")]
    for difficulty in difficulties:
        row = [difficulty]
        for model in models:
            row.append(fmt(safe_mean(by_difficulty[(model, difficulty)])))
        difficulty_rows.append(row)

    category_rows = [
        [category, category_counter.get(category, 0), pct(category_counter.get(category, 0), len(task_ids))]
        for category in FAILURE_CATEGORIES
    ]

    sparse_reference_rows = []
    for task_id in task_ids:
        reference = refs_by_id.get(task_id, {})
        traps = len(reference.get("failure_traps", []) or [])
        caps = len(reference.get("facet_cap_rules", []) or [])
        if traps < args.min_failure_traps or caps < args.min_cap_rules:
            task = tasks_by_id[task_id]
            sparse_reference_rows.append(
                [
                    task_id,
                    task.get("difficulty", "unknown"),
                    task.get("pde_system", "unknown"),
                    traps,
                    caps,
                ]
            )

    recommendations = []
    if len(ceiling_rows) / max(1, len(scores)) >= 0.35:
        recommendations.append(
            "High ceiling rate: add or rewrite hard-trap variants where generic PINN workflows are capped below full credit."
        )
    if saturated_tasks:
        recommendations.append(
            "Inspect saturated tasks first; require more explicit decisions about missing information, failure traps, or unsuitable baseline PINNs."
        )
    if low_discrimination_task_rows:
        recommendations.append(
            "Review low-discrimination tasks; either tighten the private reference/cap rules or replace with variants that force model-specific choices."
        )
    weak_categories = [category for category, count in category_counter.items() if count <= 2]
    absent_categories = [category for category in FAILURE_CATEGORIES if category_counter.get(category, 0) == 0]
    if weak_categories or absent_categories:
        recommendations.append(
            "Broaden failure-trap coverage for weak categories: "
            + compact_list(absent_categories + weak_categories, 12)
            + "."
        )
    if unscored_public_tasks:
        recommendations.append(
            f"Current score CSV does not cover {len(unscored_public_tasks)} public task(s); score all public tasks before paper claims."
        )
    if len(models) < 4:
        recommendations.append(
            "Only three scored models are present; score the existing fourth normalized run or add another weaker baseline for clearer model separation."
        )
    if not recommendations:
        recommendations.append("No blocking audit issue detected, but add inter-annotator agreement before paper release.")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report: list[str] = [
        "# PIM-PlanBench Benchmark Readiness Audit v0.3",
        "",
        f"Generated: {generated_at}",
        "",
        "## Inputs",
        "",
        markdown_table(
            ["Input", "Path"],
            [
                ["Public tasks", display_path(args.tasks, root)],
                ["Private references", display_path(args.references, root)],
                ["Score CSV", display_path(args.scores, root)],
            ],
        ),
        "",
        "## Executive Summary",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Public tasks", len(tasks)],
                ["Private references", len(references)],
                ["Scored tasks", len(scored_task_ids)],
                ["Scored models", len(models)],
                ["Score rows", len(scores)],
                ["Expected score rows for scored tasks", expected_score_rows],
                ["Missing score rows", len(missing_score_rows)],
                ["Facet ceiling rows >= " + str(args.facet_ceiling_threshold), f"{len(ceiling_rows)} ({pct(len(ceiling_rows), len(scores))})"],
                ["Exact 5.0 rows", f"{len(max_score_rows)} ({pct(len(max_score_rows), len(scores))})"],
                ["Ceiling task totals >= " + str(args.task_ceiling_threshold), len(ceiling_task_rows)],
                ["Low-discrimination tasks, range <= " + str(args.low_task_range_threshold), len(low_discrimination_task_rows)],
                ["Low-discrimination task-facets, range <= " + str(args.low_facet_range_threshold), len(low_discrimination_facet_rows)],
            ],
        ),
        "",
        "## Recommendations",
        "",
    ]
    report.extend(f"- {item}" for item in recommendations)

    report.extend(
        [
            "",
            "## Dataset Taxonomy",
            "",
            "### By Difficulty",
            "",
            markdown_table(["Difficulty", "Tasks"], summarize_distribution(tasks, "difficulty")),
            "",
            "### By Task Type",
            "",
            markdown_table(["Task type", "Tasks"], summarize_distribution(tasks, "task_type")),
            "",
            "### By Domain",
            "",
            markdown_table(["Domain", "Tasks"], summarize_distribution(tasks, "domain")),
            "",
            "## Score Coverage Checks",
            "",
            markdown_table(
                ["Check", "Count", "Examples"],
                [
                    ["Unscored public tasks", len(unscored_public_tasks), compact_list(unscored_public_tasks, 10)],
                    ["Scored task IDs not in public tasks", len(scored_unknown_tasks), compact_list(scored_unknown_tasks, 10)],
                    ["Public tasks missing private references", len(missing_references), compact_list(missing_references, 10)],
                    [
                        "Missing task/model/facet score rows",
                        len(missing_score_rows),
                        compact_list((f"{task}/{model}/{facet}" for task, model, facet in missing_score_rows), 5),
                    ],
                ],
            ),
            "",
            "## Overall Model Scores",
            "",
            markdown_table(["Model", "Rows", "Avg facet score", "Total facet points", "Std", "Ceiling rate", "5.0 rate"], model_rows),
            "",
            "## Average Score By Difficulty",
            "",
            markdown_table(["Difficulty", *models], difficulty_rows),
            "",
            "## Facet Discrimination",
            "",
            markdown_table(
                [
                    "Facet",
                    "Avg score",
                    "Score std",
                    "Avg model range per task",
                    "Min range",
                    "Max range",
                    "Ceiling rate",
                ],
                facet_summary_rows,
            ),
            "",
            "## Task Discrimination",
            "",
            "### Highest Model Separation",
            "",
            markdown_table(
                ["Task", "Difficulty", "Type", "PDE/system", "Mean total", "Range", "Std", "Ceiling models"],
                [
                    [
                        row["task_id"],
                        row["difficulty"],
                        row["task_type"],
                        row["pde_system"],
                        fmt(row["mean_total"]),
                        fmt(row["range_total"]),
                        fmt(row["std_total"]),
                        row["ceiling_models"],
                    ]
                    for row in top_task_discrimination
                ],
            ),
            "",
            "### Lowest Model Separation",
            "",
            markdown_table(
                ["Task", "Difficulty", "Type", "PDE/system", "Mean total", "Range", "Std", "Ceiling models"],
                [
                    [
                        row["task_id"],
                        row["difficulty"],
                        row["task_type"],
                        row["pde_system"],
                        fmt(row["mean_total"]),
                        fmt(row["range_total"]),
                        fmt(row["std_total"]),
                        row["ceiling_models"],
                    ]
                    for row in weakest_task_discrimination
                ],
            ),
            "",
            "### Most Saturated Tasks",
            "",
            markdown_table(
                ["Task", "Difficulty", "Type", "PDE/system", "Mean total", "Range", "Ceiling models"],
                [
                    [
                        row["task_id"],
                        row["difficulty"],
                        row["task_type"],
                        row["pde_system"],
                        fmt(row["mean_total"]),
                        fmt(row["range_total"]),
                        row["ceiling_models"],
                    ]
                    for row in saturated_tasks
                ],
            ),
            "",
            "## Failure-Trap Coverage",
            "",
            markdown_table(["Category", "Tasks hit", "Task coverage"], category_rows),
            "",
            "### Task-Level Reference Coverage",
            "",
            markdown_table(
                ["Task", "Difficulty", "Task type", "Failure traps", "Cap rules", "Detected categories"],
                task_category_rows,
            ),
            "",
            "### Sparse Private References To Inspect",
            "",
            markdown_table(["Task", "Difficulty", "PDE/system", "Failure traps", "Cap rules"], sparse_reference_rows),
            "",
            "### Review Flags Present In Private References",
            "",
            markdown_table(["Task", "Review flags"], review_flag_rows),
            "",
            "## Score Distribution",
            "",
            markdown_table(
                ["Score", "Rows"],
                [[fmt(score, 1), count] for score, count in sorted(score_counter.items())],
            ),
            "",
            "## Interpretation Notes",
            "",
            "- This audit detects saturation and coverage patterns; it does not replace human scoring.",
            "- A high score ceiling is not automatically bad, but it weakens model ranking claims if many tasks have low model separation.",
            "- Failure-trap categories are keyword-based diagnostics over private references and task text.",
            "- Before paper release, add inter-annotator agreement and an execution-validation subset.",
            "",
        ]
    )

    return "\n".join(report)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Audit PIM-PlanBench readiness for paper-facing benchmark use.")
    parser.add_argument("--tasks", type=Path, default=root / "dataset" / "tasks_public_v0.3.jsonl")
    parser.add_argument("--references", type=Path, default=root / "dataset" / "references_private_v0.3.jsonl")
    parser.add_argument("--scores", type=Path, default=root / "scores" / "pilot_v0.3" / "ModelOutput_all_existing_scored_v0.3.csv")
    parser.add_argument("--output", type=Path, default=root / "docs" / "benchmark_readiness_audit_v0.3.md")
    parser.add_argument("--facet-ceiling-threshold", type=float, default=4.5)
    parser.add_argument("--task-ceiling-threshold", type=float, default=22.5)
    parser.add_argument("--low-task-range-threshold", type=float, default=3.0)
    parser.add_argument("--low-facet-range-threshold", type=float, default=0.5)
    parser.add_argument("--min-failure-traps", type=int, default=4)
    parser.add_argument("--min-cap-rules", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tasks = read_jsonl(args.tasks)
    references = read_jsonl(args.references)
    scores = read_scores(args.scores)
    report = build_audit(tasks=tasks, references=references, scores=scores, args=args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    print(f"Tasks={len(tasks)} references={len(references)} score_rows={len(scores)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
