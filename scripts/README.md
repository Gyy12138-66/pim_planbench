# Scripts

These scripts now default to the v0.3 baseline unless a command explicitly passes older archived paths.

## Run Or Normalize Model Outputs

`run_llm_planner.py` defaults to:

- tasks: `dataset/tasks_public_v0.3.jsonl`
- prompt: `prompts/planner_prompt.md`
- output directory: `runs/pilot_v0.3/`
- prompt setting: `canonical_v0.3`

Example:

```powershell
python scripts/run_llm_planner.py --provider siliconflow --model Pro/zai-org/GLM-4.7
```

Dry run:

```powershell
python scripts/run_llm_planner.py --model dry-run-model --dry-run --limit 2
```

Normalize an existing raw v0.3 output file:

```powershell
python scripts/run_llm_planner.py --normalize-raw runs/pilot_v0.3/raw/Pro_zai-org_GLM-4.7__canonical_v0.3.jsonl --overwrite
```

## Build Model-Output Rows

`build_model_output_rows_v03.py` builds the all-existing v0.3 facet table from normalized outputs:

- input tasks: `dataset/tasks_public_v0.3.jsonl`
- input references: `dataset/references_private_v0.3.jsonl`
- input normalized directory: `runs/pilot_v0.3/normalized/`
- output: `scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv`
- quality output: `scores/pilot_v0.3/model_output_quality_v0.3.csv`

```powershell
python scripts/build_model_output_rows_v03.py
```

`build_manual_scoring_facet_rows_v03.py` builds the three-model manual scoring CSV:

- output: `outputs/scoring_v0.3/manual_scoring_facet_rows_v0.3.csv`

```powershell
python scripts/build_manual_scoring_facet_rows_v03.py
```

## Score Outputs

`score_3modeloutput_v03.py` scores a facet-row CSV with the v0.3 private references.

Default three-model subset:

```powershell
python scripts/score_3modeloutput_v03.py
```

All-existing v0.3 scoring:

```powershell
python scripts/score_3modeloutput_v03.py --input scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv --output scores/pilot_v0.3/ModelOutput_all_existing_scored_v0.3.csv --summary scores/pilot_v0.3/score_summary_by_model_all_existing_v0.3.csv --task-summary scores/pilot_v0.3/score_summary_by_task_model_all_existing_v0.3.csv
```

## Visualize Scores

`visualize_model_scores.py` builds the all-existing v0.3 HTML score report:

- output: `scores/pilot_v0.3/model_score_report_all_existing_v0.3.html`

```powershell
python scripts/visualize_model_scores.py
```

The old three-model visualizer from `scores/visualize_model_scores.py` has been archived under `archive/unused_code/`.

## Manual Review Workbooks

`build_selected_manual_scoring.mjs` builds the fixed selected-task workbook for v0.3.

```powershell
node scripts/build_selected_manual_scoring.mjs
```

`build_random_manual_scoring_v03.mjs` builds the reproducible second selected-task workbook for v0.3.

```powershell
node scripts/build_random_manual_scoring_v03.mjs
```

Both builders depend on `@oai/artifact-tool`; in the Codex desktop workspace this is usually provided through the ignored local `scripts/node_modules` symlink.

## Compare Manual And Auto Scores

`compare_manual_auto_scores_v03.py` compares the v0.3 manual scoring workbooks against `scores/pilot_v0.3/3ModelOutput_scored.csv` and writes summaries to:

- `outputs/scoring_v0.3/manual_auto_comparison_v0.3/`

```powershell
python scripts/compare_manual_auto_scores_v03.py
```

## Readiness Audit

`audit_benchmark_readiness.py` defaults to the v0.3 public tasks, v0.3 private references, and all-existing v0.3 scored output.

Default output:

- `docs/benchmark_readiness_audit_v0.3.md`

```powershell
python scripts/audit_benchmark_readiness.py
```
