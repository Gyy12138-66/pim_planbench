# PIM-PlanBench

This repository contains the v0.3 baseline of PIM-PlanBench, a pilot benchmark for evaluating whether language agents can plan physics-informed modeling workflows from natural-language physics problems.

## Final Baseline

The repository root is organized around v0.3 as the current paper-facing baseline:

- Public task set: `dataset/tasks_public_v0.3.jsonl`
- Private scoring references: `dataset/references_private_v0.3.jsonl`
- Canonical prompt: `prompts/planner_prompt.md`
- Scoring rubric: `docs/rubric_v0.3.md`
- Rubric alias: `docs/rubric.md`
- Score scale: 0-5 per facet, 25 points per task
- Required facets: `Problem Formalization`, `Physics Constraints`, `Model Choice`, `Training Strategy`, `Validation Failure Risks`

The public v0.3 task set contains 26 tasks. Private references must not be included in model prompts.

## Active Directories

- `dataset/`: v0.3 public tasks and private scoring references.
- `docs/`: v0.3 rubric, task revision notes, and readiness audits.
- `prompts/`: canonical planner prompt template.
- `runs/pilot_v0.3/`: raw and normalized v0.3 model outputs used by current scoring files.
- `scores/pilot_v0.3/`: v0.3 model-output tables, deterministic first-pass scores, summaries, and HTML reports.
- `outputs/scoring_v0.3/`: v0.3 manual scoring workbooks and manual-vs-auto comparison exports.
- `scripts/`: v0.3 runners, scoring table builders, report generators, and audit helpers.

## Archive

Older or non-final materials are kept under `archive/` instead of the active root:

- `archive/v0.1_results/`: v0.1 raw runs, normalized outputs, reports, score CSVs, and pilot review workbook.
- `archive/v0.1_inputs/`: v0.1 public tasks, task pool, private references, pilot run plan, and original rubric.
- `archive/v0.2_inputs/`: v0.2 private reference and rubric drafts.
- `archive/v0.2_outputs/`: v0.2 readiness audit and manual scoring workbook.
- `archive/v0.3_superseded_results/`: v0.3 retry outputs not used by the final scoring tables.
- `archive/unused_code/`: scripts not used by the v0.3 pipeline.
- `archive/legacy_inputs/`: early root-level input files retained for comparison.

## Current Workflow

1. Run or normalize models with `scripts/run_llm_planner.py`. Defaults target `dataset/tasks_public_v0.3.jsonl`, `runs/pilot_v0.3/`, and `canonical_v0.3`.
2. Build all-existing v0.3 model-output rows with `scripts/build_model_output_rows_v03.py`.
3. Score the model-output rows with `scripts/score_3modeloutput_v03.py` for the three-model subset or the all-existing score inputs when provided explicitly.
4. Build the v0.3 HTML score report with `scripts/visualize_model_scores.py`.
5. Use `scripts/build_selected_manual_scoring.mjs`, `scripts/build_random_manual_scoring_v03.mjs`, and `scripts/compare_manual_auto_scores_v03.py` for human review sheets and calibration summaries.
6. Run `scripts/audit_benchmark_readiness.py` for the v0.3 readiness audit.

## Human Review Markers

- `TODO_REVIEW`: a field that should be checked before final benchmark release.
- `TODO_FILL`: a field that needs concrete values before automatic checking or execution validation.

## Paper-Readiness Notes

- Use only the v0.3 task wording, private references, and 0-5 rubric for new paper-facing claims.
- Treat all archived v0.1/v0.2 artifacts as development history, not current results.
- Add inter-annotator agreement and execution-validation subsets before final paper release.
