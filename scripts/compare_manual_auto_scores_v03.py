#!/usr/bin/env python3
"""Compare v0.3 manual scoring workbooks against automatic scores.

The script uses only the Python standard library so it can run without
openpyxl. It reads the first/specified scoring sheet from each XLSX file,
joins rows to scores/pilot_v0.3/3ModelOutput_scored.csv, and writes row-level
differences plus mean/variance summaries by workbook, facet, model, and
facet-model combinations.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, variance
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUAL_GLOB = "outputs/scoring_v0.3/manual_scoring_selected_*_v0.3_compare.xlsx"
DEFAULT_AUTO_CSV = ROOT / "scores/pilot_v0.3/3ModelOutput_scored.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs/scoring_v0.3/manual_auto_comparison_v0.3"

NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

SUMMARY_FIELDS = [
    "n_rows",
    "n_compared",
    "missing_manual",
    "missing_auto",
    "human_mean",
    "human_variance",
    "auto_mean",
    "auto_variance",
    "diff_mean_human_minus_auto",
    "diff_variance",
    "abs_diff_mean",
    "abs_diff_max",
    "exact_match_rate",
    "within_0_5_rate",
    "within_1_0_rate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manual-workbook",
        action="append",
        type=Path,
        help="Manual scoring workbook. Repeat to compare multiple files. Defaults to the v0.3 compare glob.",
    )
    parser.add_argument("--manual-glob", default=DEFAULT_MANUAL_GLOB)
    parser.add_argument("--auto-csv", type=Path, default=DEFAULT_AUTO_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sheet-name", default="人工评分")
    return parser.parse_args()


def col_to_index(col: str) -> int:
    n = 0
    for char in col:
        n = n * 26 + ord(char) - 64
    return n - 1


def cell_ref_parts(ref: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    if not match:
        return None
    return int(match.group(2)), col_to_index(match.group(1))


def shared_strings(zip_file: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    values = []
    for si in root.findall("x:si", NS):
        values.append("".join(t.text or "" for t in si.findall(".//x:t", NS)))
    return values


def worksheet_path(zip_file: ZipFile, sheet_name: str) -> str:
    names = set(zip_file.namelist())
    if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
        return "xl/worksheets/sheet1.xml"

    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels_root = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    rels = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall("rel:Relationship", NS)
    }
    sheets = workbook.findall(".//x:sheet", NS)
    selected = None
    for sheet in sheets:
        if sheet.attrib.get("name") == sheet_name:
            selected = sheet
            break
    if selected is None and sheets:
        selected = sheets[0]
    if selected is None:
        raise ValueError("Workbook has no sheets")

    target = rels.get(selected.attrib[REL_ID])
    if not target:
        return "xl/worksheets/sheet1.xml"
    if target.startswith("/"):
        return target.lstrip("/")
    return "xl/" + target.lstrip("/")


def read_xlsx_rows(path: Path, sheet_name: str) -> list[dict[str, str]]:
    with ZipFile(path) as zip_file:
        strings = shared_strings(zip_file)
        sheet_path = worksheet_path(zip_file, sheet_name)
        root = ET.fromstring(zip_file.read(sheet_path))

        row_values: dict[int, dict[int, str]] = defaultdict(dict)
        max_col_by_row: dict[int, int] = defaultdict(int)
        for cell in root.findall(".//x:c", NS):
            ref = cell.attrib.get("r", "")
            parts = cell_ref_parts(ref)
            if parts is None:
                continue
            row_idx, col_idx = parts
            cell_type = cell.attrib.get("t")
            value_el = cell.find("x:v", NS)
            if cell_type == "inlineStr":
                value = "".join(t.text or "" for t in cell.findall(".//x:t", NS))
            elif value_el is None:
                value = ""
            elif cell_type == "s":
                value = strings[int(value_el.text or "0")]
            else:
                value = value_el.text or ""
            row_values[row_idx][col_idx] = value
            max_col_by_row[row_idx] = max(max_col_by_row[row_idx], col_idx)

    if 1 not in row_values:
        raise ValueError(f"No header row found in {path}")
    max_header_col = max(row_values[1])
    headers = [row_values[1].get(index, "") for index in range(max_header_col + 1)]

    rows: list[dict[str, str]] = []
    for row_idx in sorted(idx for idx in row_values if idx != 1):
        if not any(value != "" for value in row_values[row_idx].values()):
            continue
        row = {
            header: row_values[row_idx].get(index, "")
            for index, header in enumerate(headers)
            if header
        }
        rows.append(row)
    return rows


def parse_score(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    score = float(match.group(0))
    if math.isnan(score):
        return None
    return score


def auto_score_column(row: dict[str, str]) -> str:
    for column in ["初步评分参考", "初步评分标准0-5", "自动评分", "auto_score", "score"]:
        if column in row:
            return column
    return ""


def row_key(task_id: str, model: str, facet: str) -> tuple[str, str, str]:
    return task_id.strip(), model.strip(), facet.strip()


def load_auto_rows(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"task_id", "model", "facet", "score"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")
        return {
            row_key(row["task_id"], row["model"], row["facet"]): row
            for row in reader
        }


def comparable_rows(manual_paths: list[Path], auto_rows: dict[tuple[str, str, str], dict[str, str]], sheet_name: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for manual_path in manual_paths:
        rows = read_xlsx_rows(manual_path, sheet_name)
        for row in rows:
            task_id = row.get("任务ID", "")
            model = row.get("模型原名") or row.get("模型", "")
            facet = row.get("评价角度英文") or row.get("评价角度", "")
            key = row_key(task_id, model, facet)
            auto_row = auto_rows.get(key)

            human_score = parse_score(row.get("你的评分0-5"))
            auto_score = parse_score(auto_row.get("score") if auto_row else None)
            workbook_initial_col = auto_score_column(row)
            workbook_initial_score = parse_score(row.get(workbook_initial_col)) if workbook_initial_col else None

            diff = None
            abs_diff = None
            if human_score is not None and auto_score is not None:
                diff = human_score - auto_score
                abs_diff = abs(diff)

            out.append(
                {
                    "manual_file": manual_path.name,
                    "task_id": task_id,
                    "difficulty": row.get("难度", ""),
                    "domain": row.get("领域", ""),
                    "task_type": row.get("任务类型", ""),
                    "pde_system": row.get("PDE/系统", ""),
                    "model": model,
                    "model_display": row.get("模型", ""),
                    "facet": facet,
                    "facet_id": row.get("Facet ID", ""),
                    "human_score": "" if human_score is None else f"{human_score:g}",
                    "auto_score": "" if auto_score is None else f"{auto_score:g}",
                    "workbook_initial_score": "" if workbook_initial_score is None else f"{workbook_initial_score:g}",
                    "manual_minus_auto": "" if diff is None else f"{diff:g}",
                    "abs_diff": "" if abs_diff is None else f"{abs_diff:g}",
                    "human_notes": row.get("备注", ""),
                    "auto_rationale": auto_row.get("score_rationale", "") if auto_row else "",
                    "matched_auto": "yes" if auto_row else "no",
                }
            )
    return out


def numeric(row: dict[str, str], key: str) -> float | None:
    return parse_score(row.get(key, ""))


def sample_variance(values: list[float]) -> float:
    return variance(values) if len(values) >= 2 else 0.0


def summarize(rows: list[dict[str, str]], group_keys: list[str]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in group_keys)].append(row)

    summaries: list[dict[str, str]] = []
    for group, group_rows in sorted(grouped.items()):
        compared = [
            row for row in group_rows
            if numeric(row, "human_score") is not None and numeric(row, "auto_score") is not None
        ]
        human = [numeric(row, "human_score") for row in compared]
        auto = [numeric(row, "auto_score") for row in compared]
        diffs = [numeric(row, "manual_minus_auto") for row in compared]
        abs_diffs = [numeric(row, "abs_diff") for row in compared]
        assert all(value is not None for value in human + auto + diffs + abs_diffs)
        human_f = [float(value) for value in human if value is not None]
        auto_f = [float(value) for value in auto if value is not None]
        diff_f = [float(value) for value in diffs if value is not None]
        abs_diff_f = [float(value) for value in abs_diffs if value is not None]

        summary = {key: value for key, value in zip(group_keys, group)}
        n_compared = len(compared)
        missing_manual = sum(numeric(row, "human_score") is None for row in group_rows)
        missing_auto = sum(numeric(row, "auto_score") is None for row in group_rows)
        exact = sum(abs(float(row["manual_minus_auto"])) == 0 for row in compared)
        within_0_5 = sum(float(row["abs_diff"]) <= 0.5 for row in compared)
        within_1_0 = sum(float(row["abs_diff"]) <= 1.0 for row in compared)

        summary.update(
            {
                "n_rows": str(len(group_rows)),
                "n_compared": str(n_compared),
                "missing_manual": str(missing_manual),
                "missing_auto": str(missing_auto),
                "human_mean": f"{mean(human_f):.3f}" if human_f else "",
                "human_variance": f"{sample_variance(human_f):.3f}" if human_f else "",
                "auto_mean": f"{mean(auto_f):.3f}" if auto_f else "",
                "auto_variance": f"{sample_variance(auto_f):.3f}" if auto_f else "",
                "diff_mean_human_minus_auto": f"{mean(diff_f):.3f}" if diff_f else "",
                "diff_variance": f"{sample_variance(diff_f):.3f}" if diff_f else "",
                "abs_diff_mean": f"{mean(abs_diff_f):.3f}" if abs_diff_f else "",
                "abs_diff_max": f"{max(abs_diff_f):.3f}" if abs_diff_f else "",
                "exact_match_rate": f"{exact / n_compared:.3f}" if n_compared else "",
                "within_0_5_rate": f"{within_0_5 / n_compared:.3f}" if n_compared else "",
                "within_1_0_rate": f"{within_1_0 / n_compared:.3f}" if n_compared else "",
            }
        )
        summaries.append(summary)
    return summaries


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, str]], columns: list[str], limit: int | None = None) -> str:
    show_rows = rows[:limit] if limit else rows
    if not show_rows:
        return "_No rows._\n"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in show_rows:
        values = [str(row.get(column, "")).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_report(
    path: Path,
    manual_paths: list[Path],
    row_diffs: list[dict[str, str]],
    summaries: dict[str, list[dict[str, str]]],
) -> None:
    compared = [row for row in row_diffs if row["manual_minus_auto"] != ""]
    abs_diffs = [float(row["abs_diff"]) for row in compared]
    large = sorted(compared, key=lambda row: float(row["abs_diff"]), reverse=True)[:20]
    contents = [
        "# Manual vs Auto Score Comparison v0.3",
        "",
        "Positive `diff_mean_human_minus_auto` means the manual score is higher than the automatic score.",
        "Variance columns use sample variance; singleton groups use 0.000.",
        "",
        "## Inputs",
        "",
        *[f"- `{path}`" for path in manual_paths],
        f"- auto score CSV: `{DEFAULT_AUTO_CSV.relative_to(ROOT)}`",
        "",
        "## Overall",
        "",
        md_table(summaries["overall"], ["n_rows", "n_compared", "missing_manual", "missing_auto", "human_mean", "auto_mean", "diff_mean_human_minus_auto", "abs_diff_mean", "exact_match_rate", "within_0_5_rate"]),
        "## By Manual Workbook",
        "",
        md_table(summaries["by_workbook"], ["manual_file", *SUMMARY_FIELDS]),
        "## By Facet",
        "",
        md_table(summaries["by_facet"], ["facet", *SUMMARY_FIELDS]),
        "## By Model",
        "",
        md_table(summaries["by_model"], ["model", *SUMMARY_FIELDS]),
        "## By Facet And Model",
        "",
        md_table(summaries["by_facet_model"], ["facet", "model", *SUMMARY_FIELDS]),
        "## Largest Absolute Differences",
        "",
        md_table(large, ["manual_file", "task_id", "model_display", "facet", "human_score", "auto_score", "manual_minus_auto", "abs_diff"], limit=20),
        "",
    ]
    path.write_text("\n".join(contents), encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    manual_paths = args.manual_workbook or sorted(ROOT.glob(args.manual_glob))
    if not manual_paths:
        raise FileNotFoundError(f"No manual workbooks matched {args.manual_glob!r}")
    manual_paths = [path if path.is_absolute() else ROOT / path for path in manual_paths]

    auto_rows = load_auto_rows(args.auto_csv)
    row_diffs = comparable_rows(manual_paths, auto_rows, args.sheet_name)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = {
        "overall": summarize(row_diffs, []),
        "by_workbook": summarize(row_diffs, ["manual_file"]),
        "by_facet": summarize(row_diffs, ["facet"]),
        "by_model": summarize(row_diffs, ["model"]),
        "by_workbook_facet": summarize(row_diffs, ["manual_file", "facet"]),
        "by_workbook_model": summarize(row_diffs, ["manual_file", "model"]),
        "by_facet_model": summarize(row_diffs, ["facet", "model"]),
        "by_workbook_facet_model": summarize(row_diffs, ["manual_file", "facet", "model"]),
    }

    write_csv(output_dir / "manual_auto_row_diffs.csv", row_diffs)
    for name, rows in summaries.items():
        write_csv(output_dir / f"summary_{name}.csv", rows)
    write_report(output_dir / "manual_auto_comparison_report.md", manual_paths, row_diffs, summaries)

    overall = summaries["overall"][0]
    print(
        {
            "manual_workbooks": len(manual_paths),
            "row_diffs": len(row_diffs),
            "n_compared": overall["n_compared"],
            "human_mean": overall["human_mean"],
            "auto_mean": overall["auto_mean"],
            "abs_diff_mean": overall["abs_diff_mean"],
            "output_dir": str(output_dir),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
