# Scripts

## `build_selected_manual_scoring.mjs`

Builds the selected-task manual scoring workbook at:

- `outputs/scoring_v0.3/manual_scoring_selected_001_009_012_017_020_025_v0.3.xlsx`

This builder targets the current PlanScore v0.3 0-5 score sheet. It reads:

- `dataset/tasks_public_v0.3.jsonl`
- `dataset/references_private_v0.3.jsonl`
- normalized model outputs under `runs/pilot_v0.1/normalized/`

It depends on `@oai/artifact-tool`; in the Codex desktop workspace this is provided through the ignored local `scripts/node_modules` symlink.

Run it with:

```powershell
node scripts/build_selected_manual_scoring.mjs
```

## `run_llm_planner.py`

By default, runs `dataset/tasks_public_v0.1.jsonl` with `prompts/planner_prompt.md` and writes:

- raw API responses to `runs/pilot_v0.1/raw/`
- normalized scoring records to `runs/pilot_v0.1/normalized/`
- rendered prompts to `runs/pilot_v0.1/rendered_prompts/` when `--dry-run` is used

For the current v0.3 task wording, pass the task file and a separate run directory:

```powershell
python scripts/run_llm_planner.py --tasks dataset/tasks_public_v0.3.jsonl --out-dir runs/pilot_v0.3 --provider siliconflow --model Pro/zai-org/GLM-4.7
```

### Dry run

```powershell
python scripts/run_llm_planner.py --model dry-run-model --dry-run --limit 2
```

### OpenAI

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
python scripts/run_llm_planner.py --provider openai --model gpt-4.1 --limit 2
```

### DeepSeek

```powershell
$env:DEEPSEEK_API_KEY="YOUR_KEY"
python scripts/run_llm_planner.py --provider deepseek --model deepseek-chat --limit 2
```

### Qwen / DashScope compatible mode

```powershell
$env:DASHSCOPE_API_KEY="YOUR_KEY"
python scripts/run_llm_planner.py --provider qwen --model qwen-plus --limit 2
```


### SiliconFlow

```powershell
$env:SILICONFLOW_API_KEY="YOUR_KEY"
python scripts/run_llm_planner.py --provider siliconflow --model Pro/zai-org/GLM-4.7 --limit 2
```

If the provider times out, resume without `--overwrite` and increase the timeout/retry settings:

```powershell
python scripts/run_llm_planner.py --provider siliconflow --model Pro/zai-org/GLM-4.7 --timeout 300 --retries 4 --retry-sleep 10 --sleep 1
```
### Custom OpenAI-compatible endpoint

```powershell
$env:OPENAI_COMPATIBLE_API_KEY="YOUR_KEY"
$env:OPENAI_COMPATIBLE_BASE_URL="https://your-endpoint.example.com/v1"
python scripts/run_llm_planner.py --provider custom --model your-model-name --limit 2
```

Use `--task-id TASK_ID` to run a specific task, repeatable. Use `--overwrite` to rerun tasks already present in the normalized output file.

### Normalize an existing raw output file

```powershell
python scripts/run_llm_planner.py --normalize-raw runs/pilot_v0.1/raw/GPT-5.5-Thinking__canonical_v0.1__answers_public.jsonl --overwrite
```

By default, a raw filename ending in `__answers_public` is written to the matching normalized path without that suffix, for example `runs/pilot_v0.1/normalized/GPT-5.5-Thinking__canonical_v0.1.jsonl`. Use `--normalized-output` to choose a different destination.

## `audit_benchmark_readiness.py`

Builds a diagnostic readiness report for the current paper baseline:

- task taxonomy coverage
- score coverage and model/facet/task discrimination
- score ceiling indicators
- private reference failure-trap and cap-rule coverage
- suggested next benchmark edits

```powershell
python scripts/audit_benchmark_readiness.py
```

Default output:

- `docs/benchmark_readiness_audit_v0.2.md`

The current scoring rubric is `docs/rubric_v0.3.md`; `docs/rubric.md` is kept as its alias.
