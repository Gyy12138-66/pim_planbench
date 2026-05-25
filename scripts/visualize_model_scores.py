#!/usr/bin/env python3
"""Create a static HTML report for v0.3 automatic model scores."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORED = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_scored_v0.3.csv"
DEFAULT_SUMMARY = ROOT / "scores/pilot_v0.3/score_summary_by_model_all_existing_v0.3.csv"
DEFAULT_TASK_SUMMARY = ROOT / "scores/pilot_v0.3/score_summary_by_task_model_all_existing_v0.3.csv"
DEFAULT_QUALITY = ROOT / "scores/pilot_v0.3/model_output_quality_v0.3.csv"
DEFAULT_OUTPUT = ROOT / "scores/pilot_v0.3/model_score_report_all_existing_v0.3.html"

FACETS = [
    "Problem Formalization",
    "Physics Constraints",
    "Model Choice",
    "Training Strategy",
    "Validation Failure Risks",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored", type=Path, default=DEFAULT_SCORED)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--task-summary", type=Path, default=DEFAULT_TASK_SUMMARY)
    parser.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def short_model(model: str) -> str:
    replacements = {
        "Pro/moonshotai/Kimi-K2.6": "Kimi-K2.6",
        "Pro/zai-org/GLM-4.7": "GLM-4.7",
        "Pro/zai-org/GLM-5.1": "GLM-5.1",
        "deepseek-ai/DeepSeek-V4-Flash": "DeepSeek-V4-Flash",
        "deepseek/deepseek-v4-pro": "DeepSeek-V4-Pro",
        "qwen/qwen3.7-max": "Qwen3.7-Max",
    }
    return replacements.get(model, model.split("/")[-1])


def number(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bar_chart(summary: list[dict[str, str]]) -> str:
    ordered = sorted(summary, key=lambda row: number(row.get("avg_task_score_out_of_25", "")), reverse=True)
    max_value = 25.0
    row_h = 34
    label_w = 172
    chart_w = 540
    height = 34 + len(ordered) * row_h
    parts = [
        f'<svg viewBox="0 0 {label_w + chart_w + 92} {height}" role="img" aria-label="Average task score by model">',
        '<line x1="{0}" y1="20" x2="{1}" y2="20" class="axis" />'.format(label_w, label_w + chart_w),
    ]
    for tick in range(0, 26, 5):
        x = label_w + chart_w * tick / max_value
        parts.append(f'<line x1="{x:.1f}" y1="16" x2="{x:.1f}" y2="{height - 8}" class="grid" />')
        parts.append(f'<text x="{x:.1f}" y="12" text-anchor="middle" class="tick">{tick}</text>')
    for i, row in enumerate(ordered):
        y = 32 + i * row_h
        value = number(row.get("avg_task_score_out_of_25", ""))
        width = chart_w * value / max_value
        parts.append(f'<text x="0" y="{y + 18}" class="ylabel">{esc(short_model(row["model"]))}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{width:.1f}" height="22" rx="4" class="bar" />')
        parts.append(f'<text x="{label_w + width + 8:.1f}" y="{y + 16}" class="value">{value:.2f}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def score_class(value: float, max_value: float) -> str:
    ratio = value / max_value if max_value else 0
    if ratio >= 0.86:
        return "score-hi"
    if ratio >= 0.72:
        return "score-midhi"
    if ratio >= 0.55:
        return "score-mid"
    return "score-low"


def facet_table(summary: list[dict[str, str]]) -> str:
    ordered = sorted(summary, key=lambda row: number(row.get("avg_task_score_out_of_25", "")), reverse=True)
    header = "".join(f"<th>{esc(facet)}</th>" for facet in FACETS)
    rows = []
    for row in ordered:
        cells = []
        for facet in FACETS:
            value = number(row.get(f"avg_{facet}", ""))
            cells.append(f'<td class="{score_class(value, 5)}">{value:.2f}</td>')
        rows.append(
            "<tr>"
            f"<th>{esc(short_model(row['model']))}</th>"
            f"<td>{number(row.get('avg_task_score_out_of_25', '')):.2f}</td>"
            + "".join(cells)
            + "</tr>"
        )
    return (
        '<table class="matrix"><thead><tr><th>Model</th><th>Avg /25</th>'
        + header
        + "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def difficulty_table(task_summary: list[dict[str, str]]) -> str:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    difficulties = []
    for row in task_summary:
        diff = row.get("difficulty", "")
        if diff not in difficulties:
            difficulties.append(diff)
        grouped[(row["model"], diff)].append(number(row.get("task_score_out_of_25", "")))

    model_order = sorted(
        {row["model"] for row in task_summary},
        key=lambda model: mean(
            number(row.get("task_score_out_of_25", ""))
            for row in task_summary
            if row["model"] == model
        ),
        reverse=True,
    )
    diff_order = [diff for diff in ["easy", "medium", "hard", "hard_plus"] if diff in difficulties]
    diff_order.extend(diff for diff in difficulties if diff not in diff_order)

    header = "".join(f"<th>{esc(diff)}</th>" for diff in diff_order)
    rows = []
    for model in model_order:
        cells = []
        for diff in diff_order:
            vals = grouped.get((model, diff), [])
            value = mean(vals) if vals else 0.0
            cells.append(f'<td class="{score_class(value, 25)}">{value:.2f}</td>')
        rows.append(f"<tr><th>{esc(short_model(model))}</th>{''.join(cells)}</tr>")
    return '<table class="matrix"><thead><tr><th>Model</th>' + header + "</tr></thead><tbody>" + "\n".join(rows) + "</tbody></table>"


def quality_table(quality: list[dict[str, str]]) -> str:
    if not quality:
        return "<p>No quality audit file found.</p>"
    rows = []
    for row in sorted(quality, key=lambda item: item.get("model", "")):
        include = row.get("include_in_scoring", "")
        invalid = int(number(row.get("invalid_rows", "0")))
        cls = "quality-ok" if invalid == 0 and include == "yes" else "quality-warn"
        rows.append(
            "<tr>"
            f"<th>{esc(short_model(row.get('model', '')))}</th>"
            f"<td>{esc(row.get('total_rows', ''))}</td>"
            f"<td>{esc(row.get('valid_rows', ''))}</td>"
            f'<td class="{cls}">{esc(row.get("invalid_rows", ""))}</td>'
            f"<td>{esc(include)}</td>"
            f"<td>{esc(row.get('invalid_task_ids', ''))}</td>"
            "</tr>"
        )
    return (
        '<table class="quality"><thead><tr><th>Model</th><th>Rows</th><th>Valid</th>'
        "<th>Invalid</th><th>Included</th><th>Invalid Task IDs</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def top_bottom_tasks(task_summary: list[dict[str, str]]) -> str:
    by_task: dict[str, list[float]] = defaultdict(list)
    meta: dict[str, str] = {}
    for row in task_summary:
        task_id = row["task_id"]
        by_task[task_id].append(number(row.get("task_score_out_of_25", "")))
        meta[task_id] = row.get("difficulty", "")
    averages = sorted(
        ((task_id, meta[task_id], mean(vals)) for task_id, vals in by_task.items()),
        key=lambda item: item[2],
    )
    rows = []
    for task_id, difficulty, value in averages[:6] + averages[-6:]:
        rows.append(
            f"<tr><th>{esc(task_id)}</th><td>{esc(difficulty)}</td><td>{value:.2f}</td></tr>"
        )
    return '<table class="compact"><thead><tr><th>Task</th><th>Difficulty</th><th>Mean /25</th></tr></thead><tbody>' + "\n".join(rows) + "</tbody></table>"


def main() -> int:
    args = parse_args()
    scored = read_csv(args.scored)
    summary = read_csv(args.summary)
    task_summary = read_csv(args.task_summary)
    quality = read_csv(args.quality) if args.quality.exists() else []

    total_models = len(summary)
    total_rows = len(scored)
    total_tasks = len({row["task_id"] for row in scored})
    avg = mean(number(row.get("score", "")) for row in scored)
    best = max(summary, key=lambda row: number(row.get("avg_task_score_out_of_25", "")))

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PIM-PlanBench v0.3 Model Score Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5c6670;
      --line: #d8dee6;
      --panel: #f7f8fa;
      --accent: #2666cf;
      --accent-2: #14866d;
      --warn: #b05200;
      --low: #f9d8d3;
      --mid: #fee7b7;
      --midhi: #cce7d8;
      --hi: #9bd0c4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 24px 56px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 28px 0 12px; font-size: 18px; letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.5; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 20px 0 8px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      background: var(--panel);
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; margin-top: 5px; font-size: 22px; }}
    .chart {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      overflow-x: auto;
    }}
    svg {{ min-width: 760px; width: 100%; height: auto; }}
    .axis {{ stroke: #77808a; stroke-width: 1; }}
    .grid {{ stroke: #e8ebef; stroke-width: 1; }}
    .bar {{ fill: var(--accent); }}
    .ylabel {{ font-size: 13px; fill: var(--ink); }}
    .tick, .value {{ font-size: 12px; fill: var(--muted); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
    }}
    thead th {{ background: #eef2f6; color: #26323f; }}
    tbody tr:last-child th, tbody tr:last-child td {{ border-bottom: 0; }}
    .matrix td {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .matrix th:first-child {{ min-width: 150px; }}
    .score-hi {{ background: var(--hi); }}
    .score-midhi {{ background: var(--midhi); }}
    .score-mid {{ background: var(--mid); }}
    .score-low {{ background: var(--low); }}
    .quality td:last-child {{
      max-width: 480px;
      font-size: 12px;
      color: var(--muted);
    }}
    .quality-ok {{ color: var(--accent-2); font-weight: 700; }}
    .quality-warn {{ color: var(--warn); font-weight: 700; }}
    .compact {{ max-width: 720px; }}
    @media (max-width: 780px) {{
      main {{ padding: 20px 14px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ display: block; overflow-x: auto; white-space: nowrap; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>PIM-PlanBench v0.3 Model Score Report</h1>
  <p>Automatic deterministic scoring over the currently normalized model outputs. Schema-invalid task answers are kept as empty facet answers, so they receive zero in the automatic score.</p>
  <section class="metrics">
    <div class="metric"><span>Models</span><strong>{total_models}</strong></div>
    <div class="metric"><span>Tasks</span><strong>{total_tasks}</strong></div>
    <div class="metric"><span>Facet Rows</span><strong>{total_rows}</strong></div>
    <div class="metric"><span>Best Avg /25</span><strong>{esc(short_model(best["model"]))}: {number(best.get("avg_task_score_out_of_25", "")):.2f}</strong></div>
  </section>

  <h2>Overall Ranking</h2>
  <div class="chart">{bar_chart(summary)}</div>

  <h2>Facet Breakdown</h2>
  {facet_table(summary)}

  <h2>Difficulty Breakdown</h2>
  {difficulty_table(task_summary)}

  <h2>Output Quality Audit</h2>
  {quality_table(quality)}

  <h2>Easiest And Hardest Tasks By Mean Score</h2>
  {top_bottom_tasks(task_summary)}

  <script type="application/json" id="report-metadata">
  {json.dumps({"average_facet_score": round(avg, 3), "scored": str(args.scored), "summary": str(args.summary)}, ensure_ascii=False)}
  </script>
</main>
</body>
</html>
"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_doc, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "models": total_models,
                "tasks": total_tasks,
                "facet_rows": total_rows,
                "best_model": best["model"],
                "best_avg_task_score_out_of_25": number(best.get("avg_task_score_out_of_25", "")),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
