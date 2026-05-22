#!/usr/bin/env python3
"""Build an HTML score report for PIM-PlanBench model outputs."""

from __future__ import annotations

import argparse
import csv
import html
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


FACET_ORDER = [
    "Problem Formalization",
    "Physics Constraints",
    "Model Choice",
    "Training Strategy",
    "Validation Failure Risks",
]

MODEL_LABELS = {
    "deepseek-ai/DeepSeek-V4-Flash": "DeepSeek-V4-Flash",
    "Pro/moonshotai/Kimi-K2.6": "Kimi-K2.6",
    "Pro/zai-org/GLM-4.7": "GLM-4.7",
}

MODEL_COLORS = {
    "deepseek-ai/DeepSeek-V4-Flash": "#2563eb",
    "Pro/moonshotai/Kimi-K2.6": "#16a34a",
    "Pro/zai-org/GLM-4.7": "#dc2626",
}


@dataclass(frozen=True)
class ScoreRow:
    task_id: str
    model: str
    facet: str
    score: float


def infer_difficulty(task_id: str) -> str:
    if task_id.startswith("hard_plus_"):
        return "hard_plus"
    if task_id.startswith("hard_"):
        return "hard"
    if task_id.startswith("medium_"):
        return "medium"
    if task_id.startswith("easy_"):
        return "easy"
    return "unknown"


def task_number(task_id: str) -> int:
    suffix = task_id.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else 10_000


def read_rows(path: Path) -> list[ScoreRow]:
    rows: list[ScoreRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"task_id", "model", "facet", "score"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")

        for line_no, row in enumerate(reader, start=2):
            raw_score = (row.get("score") or "").strip()
            if raw_score == "":
                raise ValueError(f"Missing score at {path}:{line_no}")
            try:
                score = float(raw_score)
            except ValueError as exc:
                raise ValueError(f"Invalid score at {path}:{line_no}: {raw_score!r}") from exc
            if score < 0 or score > 5:
                raise ValueError(f"Score out of 0-5 range at {path}:{line_no}: {score}")
            rows.append(
                ScoreRow(
                    task_id=row["task_id"].strip(),
                    model=row["model"].strip(),
                    facet=row["facet"].strip(),
                    score=score,
                )
            )
    return rows


def model_label(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def model_color(model: str) -> str:
    return MODEL_COLORS.get(model, "#64748b")


def fmt(value: float) -> str:
    return f"{value:.2f}"


def pct(value: float, max_value: float) -> str:
    return f"{max(0.0, min(100.0, value / max_value * 100.0)):.1f}%"


def heat_color(value: float, max_value: float = 5.0) -> str:
    ratio = max(0.0, min(1.0, value / max_value))
    if ratio >= 0.9:
        return "#dcfce7"
    if ratio >= 0.8:
        return "#ecfccb"
    if ratio >= 0.7:
        return "#fef9c3"
    if ratio >= 0.6:
        return "#ffedd5"
    return "#fee2e2"


def bar(value: float, max_value: float, color: str) -> str:
    return (
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width:{pct(value, max_value)};background:{color}"></div>'
        "</div>"
    )


def section(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body}</section>"


def build_overall_table(models: list[str], by_model: dict[str, list[float]]) -> str:
    rows = []
    for model in models:
        vals = by_model[model]
        avg = mean(vals)
        total = sum(vals)
        rows.append(
            "<tr>"
            f"<td>{html.escape(model_label(model))}</td>"
            f"<td>{fmt(avg)}</td>"
            f"<td>{fmt(total)}</td>"
            f"<td>{len(vals)}</td>"
            f"<td>{bar(avg, 5, model_color(model))}</td>"
            "</tr>"
        )
    return (
        '<table class="wide"><thead><tr>'
        "<th>Model</th><th>Average facet score</th><th>Total facet points</th>"
        "<th>Scored facets</th><th>Visual</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def build_group_table(
    title_col: str,
    groups: list[str],
    models: list[str],
    values: dict[tuple[str, str], list[float]],
    max_value: float = 5.0,
) -> str:
    head = "<tr><th>{}</th>{}</tr>".format(
        html.escape(title_col),
        "".join(f"<th>{html.escape(model_label(model))}</th>" for model in models),
    )
    body_rows = []
    for group in groups:
        cells = [f"<td class=\"row-label\">{html.escape(group)}</td>"]
        for model in models:
            vals = values.get((model, group), [])
            if vals:
                value = mean(vals)
                cells.append(
                    f'<td style="background:{heat_color(value, max_value)}">'
                    f"<strong>{fmt(value)}</strong>{bar(value, max_value, model_color(model))}</td>"
                )
            else:
                cells.append("<td>-</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="wide heat"><thead>{head}</thead><tbody>{"".join(body_rows)}</tbody></table>'


def build_distribution_table(models: list[str], values: dict[str, list[float]]) -> str:
    head = "<tr><th>Model</th>" + "".join(f"<th>{score}</th>" for score in range(6)) + "</tr>"
    rows = []
    for model in models:
        counts = Counter(int(score) for score in values[model])
        cells = [f"<td class=\"row-label\">{html.escape(model_label(model))}</td>"]
        for score in range(6):
            count = counts.get(score, 0)
            cells.append(f"<td>{count}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="wide"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table>'


def build_task_total_table(
    task_ids: list[str],
    models: list[str],
    task_totals: dict[tuple[str, str], float],
) -> str:
    head = "<tr><th>Task</th><th>Difficulty</th>" + "".join(
        f"<th>{html.escape(model_label(model))}</th>" for model in models
    ) + "</tr>"
    rows = []
    for task_id in task_ids:
        cells = [
            f"<td class=\"row-label\">{html.escape(task_id)}</td>",
            f"<td>{html.escape(infer_difficulty(task_id))}</td>",
        ]
        for model in models:
            value = task_totals.get((model, task_id))
            if value is None:
                cells.append("<td>-</td>")
            else:
                cells.append(
                    f'<td style="background:{heat_color(value, 25)}">'
                    f"<strong>{fmt(value)}</strong>{bar(value, 25, model_color(model))}</td>"
                )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="wide heat task-table"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table>'


def build_html(rows: list[ScoreRow], input_path: Path) -> str:
    models = sorted({row.model for row in rows}, key=model_label)
    task_ids = sorted({row.task_id for row in rows}, key=task_number)

    by_model: dict[str, list[float]] = defaultdict(list)
    by_model_facet: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_model_difficulty: dict[tuple[str, str], list[float]] = defaultdict(list)
    task_totals: dict[tuple[str, str], float] = defaultdict(float)

    for row in rows:
        by_model[row.model].append(row.score)
        by_model_facet[(row.model, row.facet)].append(row.score)
        by_model_difficulty[(row.model, infer_difficulty(row.task_id))].append(row.score)
        task_totals[(row.model, row.task_id)] += row.score

    generated_from = html.escape(str(input_path))
    body = [
        "<header>",
        "<h1>PIM-PlanBench Score Report</h1>",
        f"<p>Generated from <code>{generated_from}</code>. Scores use the 0-5 facet rubric.</p>",
        "</header>",
        section("Overall Model Scores", build_overall_table(models, by_model)),
        section(
            "Average Score by Facet",
            build_group_table("Facet", FACET_ORDER, models, by_model_facet),
        ),
        section(
            "Average Score by Difficulty",
            build_group_table("Difficulty", ["easy", "medium", "hard", "hard_plus"], models, by_model_difficulty),
        ),
        section("Score Distribution", build_distribution_table(models, by_model)),
        section("Task Total Scores", build_task_total_table(task_ids, models, task_totals)),
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PIM-PlanBench Score Report</title>
<style>
:root {{
  color-scheme: light;
  --text: #111827;
  --muted: #6b7280;
  --line: #d1d5db;
  --panel: #ffffff;
  --bg: #f8fafc;
}}
body {{
  margin: 0;
  padding: 28px;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
header, section {{
  max-width: 1280px;
  margin: 0 auto 22px auto;
}}
h1 {{
  margin: 0 0 8px 0;
  font-size: 28px;
}}
h2 {{
  margin: 0 0 12px 0;
  font-size: 20px;
}}
p {{
  margin: 0;
  color: var(--muted);
}}
code {{
  background: #e5e7eb;
  border-radius: 4px;
  padding: 2px 5px;
}}
table {{
  border-collapse: collapse;
  background: var(--panel);
  width: 100%;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}}
th, td {{
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  vertical-align: middle;
  font-size: 13px;
}}
th {{
  background: #1f2937;
  color: #ffffff;
  font-weight: 650;
}}
.row-label {{
  font-weight: 650;
  white-space: nowrap;
}}
.bar-track {{
  height: 8px;
  margin-top: 6px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}}
.bar-fill {{
  height: 100%;
  border-radius: 999px;
}}
.task-table td:first-child {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}}
@media print {{
  body {{ background: #ffffff; padding: 12px; }}
  table {{ box-shadow: none; }}
}}
</style>
</head>
<body>
{''.join(body)}
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_input = script_dir / "pilot_v0.1" / "3ModelOutput.csv"
    default_output = script_dir / "pilot_v0.1" / "model_score_report.html"
    parser = argparse.ArgumentParser(description="Visualize model scores from 3ModelOutput.csv.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input CSV with task_id, model, facet, score columns.")
    parser.add_argument("--output", type=Path, default=default_output, help="Output HTML report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_rows(args.input)
    report = build_html(rows, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    print(f"Rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
