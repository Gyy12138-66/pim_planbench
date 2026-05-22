# PIM-PlanBench Pilot

This folder contains a pilot task pool for evaluating whether language agents can plan physics-informed modeling workflows from natural-language physics problems.

## Files

- `tasks_pool.csv`: English CSV source table for the 20 pilot tasks.
- `tasks_public.jsonl`: public benchmark inputs that may be shown to models.
- `references_private.jsonl`: private reference facets, expected losses, failure traps, and rubric fields for scoring.
- `prompts/`: prompt templates for model runs.
- `runs/`: raw model outputs.
- `scores/`: automatic and human scoring outputs.
- `docs/`: notes, annotation guidelines, and paper planning documents.

## Human Review Markers

- `TODO_REVIEW`: a field that should be checked before final benchmark release.
- `TODO_FILL`: a field that needs concrete values before automatic checking or execution validation.

## Recommended Next Step

Review `tasks_pool.csv` first. After the task wording and provenance look correct, update `references_private.jsonl` to remove or resolve the `TODO_REVIEW` and `TODO_FILL` markers for tasks selected for execution validation.
