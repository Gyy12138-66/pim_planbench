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

### Overseas OpenAI-compatible APIs through HTTP

The runner sends direct HTTP POST requests to `{base_url}/chat/completions`.
Use this path for OpenRouter, OpenAI-compatible gateways, or overseas model APIs
that expose the OpenAI chat-completions protocol.

OpenRouter example:

```powershell
$env:OPENROUTER_API_KEY="YOUR_KEY"
python scripts/run_llm_planner.py `
  --tasks dataset/tasks_public_v0.3.jsonl `
  --out-dir runs/pilot_v0.3 `
  --provider openrouter `
  --model openai/gpt-4.1 `
  --prompt-setting canonical_v0.3 `
  --max-tokens 6000 `
  --timeout 240 `
  --sleep 1
```

Custom overseas gateway example:

```powershell
$env:OPENAI_COMPATIBLE_API_KEY="YOUR_KEY"
$env:OPENAI_COMPATIBLE_BASE_URL="https://your-overseas-gateway.example.com/v1"
python scripts/run_llm_planner.py `
  --tasks dataset/tasks_public_v0.3.jsonl `
  --out-dir runs/pilot_v0.3_custom `
  --provider custom `
  --model provider/model-name `
  --prompt-setting canonical_v0.3 `
  --max-tokens 6000
```

If the gateway requires additional HTTP headers, repeat `--header`:

```powershell
python scripts/run_llm_planner.py `
  --provider custom `
  --base-url https://your-overseas-gateway.example.com/v1 `
  --api-key-env OPENAI_COMPATIBLE_API_KEY `
  --model provider/model-name `
  --header "HTTP-Referer=https://local.pim-planbench" `
  --header "X-Title=PIM-PlanBench" `
  --limit 2
```

If your network requires an explicit proxy:

```powershell
python scripts/run_llm_planner.py `
  --provider openrouter `
  --model openai/gpt-4.1 `
  --proxy-url http://127.0.0.1:7890 `
  --limit 2
```

Use `--task-id TASK_ID` to run a specific task, repeatable. Use `--overwrite` to rerun tasks already present in the normalized output file.

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
