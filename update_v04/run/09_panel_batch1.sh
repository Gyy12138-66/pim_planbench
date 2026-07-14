#!/usr/bin/env bash
# 批次 1（验收，决议 2026-07-14）：原 6 模型 ×1、T=0.2、v0.4 题集（25+canary）
# → build rows → score_v04 评分 → 06 指标 → 09b 预注册验收判据。
# 需要环境变量 SILICONFLOW_API_KEY 与 OPENROUTER_API_KEY。
# 断点续跑：中断后重复同一命令（runner 自动跳过 normalized 已有任务）。
# 题集冻结（验收通过）后才跑批次 2（9 模型 ×5 + 温度敏感性，另行脚本）。
set -euo pipefail
cd "$(dirname "$0")/../.."

: "${SILICONFLOW_API_KEY:?需要 SILICONFLOW_API_KEY（4 个模型走 siliconflow）}"
: "${OPENROUTER_API_KEY:?需要 OPENROUTER_API_KEY（deepseek-v4-pro 与 qwen3.7-max）}"

run () {
  python3 scripts/run_llm_planner.py \
    --tasks dataset/tasks_public_v0.4.jsonl \
    --out-dir runs/pilot_v0.4 \
    --prompt-setting canonical_v0.4 \
    --provider "$1" --model "$2" \
    --temperature 0.2 --max-tokens 6000 --timeout 240 --retries 3 --sleep 1
}
run siliconflow Pro/moonshotai/Kimi-K2.6
run siliconflow Pro/zai-org/GLM-4.7
run siliconflow Pro/zai-org/GLM-5.1
run siliconflow deepseek-ai/DeepSeek-V4-Flash
run openrouter  deepseek/deepseek-v4-pro
run openrouter  qwen/qwen3.7-max

python3 scripts/build_model_output_rows_v03.py \
  --tasks dataset/tasks_public_v0.4.jsonl \
  --references dataset/references_private_v0.4.jsonl \
  --normalized-dir runs/pilot_v0.4/normalized \
  --output scores/pilot_v0.4/ModelOutput_batch1_v0.4.csv \
  --quality-output scores/pilot_v0.4/model_output_quality_batch1_v0.4.csv

python3 update_v04/scorer_v04/score_v04.py \
  --input scores/pilot_v0.4/ModelOutput_batch1_v0.4.csv \
  --output scores/pilot_v0.4/ModelOutput_batch1_scored_v0.4.csv \
  --summary scores/pilot_v0.4/score_summary_by_model_batch1_v0.4.csv \
  --task-summary scores/pilot_v0.4/score_summary_by_task_model_batch1_v0.4.csv

python3 update_v04/run/06_item_metrics.py \
  --scored-csv scores/pilot_v0.4/ModelOutput_batch1_scored_v0.4.csv \
  --out update_v04/docs/item_metrics_batch1_v0.4.csv

python3 update_v04/run/09b_acceptance_batch1.py
