# PIM-PlanBench

This repository contains a pilot benchmark for evaluating whether language agents can plan physics-informed modeling workflows from natural-language physics problems.

## Current Paper Baseline

The current paper baseline is frozen as:

- Public task set: `dataset/tasks_public_v0.3.jsonl`
- Private scoring references: `dataset/references_private_v0.3.jsonl`
- Canonical prompt: `prompts/planner_prompt.md`
- Scoring rubric: `docs/rubric_v0.3.md`
- Score scale: 0-5 per facet, 25 points per task
- Required facets: `Problem Formalization`, `Physics Constraints`, `Model Choice`, `Training Strategy`, `Validation Failure Risks`

The public v0.3 task set contains 26 tasks. Private references must not be included in model prompts.

Existing `runs/pilot_v0.1/` outputs and `scores/pilot_v0.1/` scores were generated from the v0.1 public task wording. Rerun models on `dataset/tasks_public_v0.3.jsonl` before reporting v0.3 results.

## Supporting Inputs

- `dataset/tasks_pool_v0.1.csv`: task construction ledger for researchers.
- `dataset/tasks_public_v0.1.jsonl`: archived pilot public task wording used for the first runs.
- `docs/rubric.md`: alias copy of the current 0-5 scoring rubric.
- `docs/rubric_v0.1.md`: archived original 0-2 pilot rubric.
- `docs/rubric_v0.2.md`: pilot 0-5 PlanScore rubric before v0.3 hard-trap cap rules.
- `docs/rubric_v0.3.md`: current 0-5 PlanScore rubric with general and task-specific cap rules.
- `dataset/references_private_v0.1.jsonl` and `dataset/references_private_v0.2.jsonl`: archived private reference drafts.
- `archive/legacy_inputs/`: legacy root-level input files retained for comparison.

## Working Directories

- `runs/pilot_v0.1/raw/`: raw API responses.
- `runs/pilot_v0.1/normalized/`: normalized model answers.
- `runs/pilot_v0.1/reports/`: generated run summaries.
- `scores/pilot_v0.1/`: legacy pilot scoring CSVs and preliminary 0-5 score reports.
- `outputs/pilot_v0.1/`: archived original pilot review workbooks.
- `outputs/scoring_v0.3/`: current 0-5 manual scoring workbooks.
- `scripts/`: benchmark runners, translation helpers, and scoring workbook builders.
- `docs/`: run plans, annotation notes, and rubric versions.

## Human Review Markers

- `TODO_REVIEW`: a field that should be checked before final benchmark release.
- `TODO_FILL`: a field that needs concrete values before automatic checking or execution validation.

## Next Paper-Readiness Steps

1. Rerun the selected models on `dataset/tasks_public_v0.3.jsonl` before scoring the updated benchmark.
2. Use only the 0-5 rubric in `docs/rubric_v0.3.md` for new scoring passes.
3. Keep new 0-5 scoring workbooks and exports separate from the old v0.1 pilot outputs.
4. Treat old 0-2 artifacts as pilot history, not as current paper results.
5. Add inter-annotator agreement and execution-validation subsets before final paper release.
