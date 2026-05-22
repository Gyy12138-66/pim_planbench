# PIM-PlanBench

This repository contains a pilot benchmark for evaluating whether language agents can plan physics-informed modeling workflows from natural-language physics problems.

## Current Inputs

- `dataset/tasks_public_v0.1.jsonl`: public benchmark inputs shown to models.
- `dataset/references_private_v0.1.jsonl`: private reference facets, expected losses, failure traps, and rubric fields for scoring.
- `dataset/tasks_pool_v0.1.csv`: task construction ledger for researchers.
- `prompts/planner_prompt.md`: canonical planner prompt template.
- `docs/rubric.md`: current scoring rubric.
- `docs/rubric_v0.1.md`: original 0-2 pilot rubric.
- `docs/rubric_v0.2.md`: expanded 0-5 pilot rubric.

The current v0.1 task set contains 26 tasks. Legacy root-level input files, if needed for comparison, live under `archive/legacy_inputs/`.

## Working Directories

- `runs/pilot_v0.1/raw/`: raw API responses.
- `runs/pilot_v0.1/normalized/`: normalized model answers.
- `runs/pilot_v0.1/reports/`: generated run summaries.
- `scores/pilot_v0.1/`: manual scoring CSVs for the original 0-2 rubric.
- `outputs/pilot_v0.1/`: generated review workbooks and other exported artifacts.
- `scripts/`: benchmark runners, translation helpers, and scoring workbook builders.
- `docs/`: run plans, annotation notes, and rubric versions.

## Human Review Markers

- `TODO_REVIEW`: a field that should be checked before final benchmark release.
- `TODO_FILL`: a field that needs concrete values before automatic checking or execution validation.

## Recommended Next Step

Use `docs/rubric_v0.2.md` for the next manual scoring pass. If the old v0.1 score sheets are reused, create a separate `scores/pilot_v0.2/` copy with 0-5 score columns instead of mixing 0-2 and 0-5 scores in the same files.
