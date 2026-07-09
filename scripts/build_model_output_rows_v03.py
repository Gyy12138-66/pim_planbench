#!/usr/bin/env python3
"""Build facet-level scoring rows from all normalized v0.3 model outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from build_manual_scoring_facet_rows_v03 import (
    FACET_ORDER,
    FIELDNAMES,
    SCORING_STANDARDS,
    make_assistant_view,
    reference_for_facet,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "dataset/tasks_public_v0.3.jsonl"
DEFAULT_REFERENCES = ROOT / "dataset/references_private_v0.3.jsonl"
DEFAULT_NORMALIZED_DIR = ROOT / "runs/pilot_v0.3/normalized"
DEFAULT_OUTPUT = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv"
DEFAULT_QUALITY_OUTPUT = ROOT / "scores/pilot_v0.3/model_output_quality_v0.3.csv"

EXTRA_FIELDNAMES = [
    "schema_valid",
    "parse_error",
    "normalized_file",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--normalized-dir", type=Path, default=DEFAULT_NORMALIZED_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quality-output", type=Path, default=DEFAULT_QUALITY_OUTPUT)
    parser.add_argument(
        "--require-schema-valid",
        action="store_true",
        help="Drop model files with any schema-invalid task. By default, complete but partially invalid models are kept and invalid facets score as empty.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def model_from_records(path: Path, records: list[dict[str, Any]]) -> str:
    for record in records:
        model = record.get("model")
        if isinstance(model, str) and model:
            return model
    return path.stem.split("__", 1)[0].replace("_", "/")


def prompt_settings(records: list[dict[str, Any]]) -> str:
    values = sorted({str(row.get("prompt_setting", "")) for row in records if row.get("prompt_setting")})
    return "; ".join(values)


def providers(records: list[dict[str, Any]]) -> str:
    values = sorted({str(row.get("provider", "")) for row in records if row.get("provider")})
    return "; ".join(values)


def audit_file(path: Path, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    records = read_jsonl(path)
    expected_ids = [str(task["id"]) for task in tasks]
    expected_set = set(expected_ids)
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    invalid: list[str] = []

    for record in records:
        task_id = str(record.get("id", ""))
        if task_id in seen:
            duplicates.append(task_id)
        seen[task_id] = seen.get(task_id, 0) + 1
        if record.get("schema_valid") is not True:
            invalid.append(task_id)

    missing = [task_id for task_id in expected_ids if task_id not in seen]
    extra = sorted(task_id for task_id in seen if task_id not in expected_set)

    return {
        "path": path,
        "records": records,
        "model": model_from_records(path, records),
        "total_rows": len(records),
        "valid_rows": sum(1 for row in records if row.get("schema_valid") is True),
        "invalid_rows": len(invalid),
        "missing_task_ids": missing,
        "duplicate_task_ids": sorted(set(duplicates)),
        "extra_task_ids": extra,
        "prompt_settings": prompt_settings(records),
        "providers": providers(records),
    }


def write_quality(path: Path, audits: list[dict[str, Any]], included_models: set[str]) -> None:
    fieldnames = [
        "model",
        "normalized_file",
        "total_rows",
        "valid_rows",
        "invalid_rows",
        "missing_task_count",
        "duplicate_task_count",
        "extra_task_count",
        "include_in_scoring",
        "prompt_settings",
        "providers",
        "invalid_task_ids",
        "missing_task_ids",
        "duplicate_task_ids",
        "extra_task_ids",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for audit in sorted(audits, key=lambda item: item["model"]):
            invalid_task_ids = [
                str(row.get("id", ""))
                for row in audit["records"]
                if row.get("schema_valid") is not True
            ]
            writer.writerow(
                {
                    "model": audit["model"],
                    "normalized_file": display_path(audit["path"]),
                    "total_rows": audit["total_rows"],
                    "valid_rows": audit["valid_rows"],
                    "invalid_rows": audit["invalid_rows"],
                    "missing_task_count": len(audit["missing_task_ids"]),
                    "duplicate_task_count": len(audit["duplicate_task_ids"]),
                    "extra_task_count": len(audit["extra_task_ids"]),
                    "include_in_scoring": "yes" if audit["model"] in included_models else "no",
                    "prompt_settings": audit["prompt_settings"],
                    "providers": audit["providers"],
                    "invalid_task_ids": "; ".join(sorted(invalid_task_ids)),
                    "missing_task_ids": "; ".join(audit["missing_task_ids"]),
                    "duplicate_task_ids": "; ".join(audit["duplicate_task_ids"]),
                    "extra_task_ids": "; ".join(audit["extra_task_ids"]),
                }
            )


def row_answer(record: dict[str, Any], facet_name: str) -> str:
    answer = record.get("answer")
    if isinstance(answer, dict):
        value = answer.get(facet_name, "")
        return "" if value is None else str(value)
    return ""


def build_rows(
    tasks: list[dict[str, Any]],
    references: dict[str, dict[str, Any]],
    audits: list[dict[str, Any]],
    require_schema_valid: bool,
) -> tuple[list[dict[str, str]], set[str]]:
    rows: list[dict[str, str]] = []
    included_models: set[str] = set()

    for audit in sorted(audits, key=lambda item: item["model"]):
        if audit["missing_task_ids"] or audit["duplicate_task_ids"]:
            continue
        if require_schema_valid and audit["invalid_rows"]:
            continue

        included_models.add(audit["model"])
        records_by_id = {str(record["id"]): record for record in audit["records"] if "id" in record}

        for task in tasks:
            task_id = str(task["id"])
            reference = references.get(task_id)
            if reference is None:
                raise ValueError(f"Missing private reference for {task_id}")
            record = records_by_id[task_id]

            for facet_name, facet_id in FACET_ORDER:
                answer = row_answer(record, facet_name)
                rows.append(
                    {
                        "task_id": task_id,
                        "difficulty": str(task.get("difficulty", "")),
                        "domain": str(task.get("domain", "")),
                        "task_type": str(task.get("task_type", "")),
                        "pde_system": str(task.get("pde_system", "")),
                        "model": str(record.get("model") or audit["model"]),
                        "prompt_setting": str(record.get("prompt_setting", "")),
                        "facet": facet_name,
                        "facet_id": facet_id,
                        "model_answer": answer,
                        "reference_answer": reference_for_facet(reference, facet_id),
                        "assistant_view": make_assistant_view(answer, facet_id, record),
                        "scoring_standard": SCORING_STANDARDS[facet_id],
                        "human_score_0_5": "",
                        "human_error_tags": "",
                        "human_notes": "",
                        "schema_valid": str(record.get("schema_valid", "")),
                        "parse_error": str(record.get("parse_error", "")),
                        "normalized_file": display_path(audit["path"]),
                    }
                )

    return rows, included_models


def main() -> int:
    args = parse_args()
    tasks = read_jsonl(args.tasks)
    references = {row["id"]: row for row in read_jsonl(args.references)}

    files = sorted(args.normalized_dir.glob("*.jsonl"))
    if not files:
        raise ValueError(f"No normalized JSONL files found in {args.normalized_dir}")

    audits = [audit_file(path, tasks) for path in files]
    rows, included_models = build_rows(tasks, references, audits, args.require_schema_valid)
    if not rows:
        raise ValueError("No model rows were included after quality filtering.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = FIELDNAMES + EXTRA_FIELDNAMES
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    write_quality(args.quality_output, audits, included_models)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "quality_output": str(args.quality_output),
                "normalized_files": len(files),
                "included_models": sorted(included_models),
                "rows": len(rows),
                "require_schema_valid": args.require_schema_valid,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
