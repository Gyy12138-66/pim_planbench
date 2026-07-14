#!/usr/bin/env bash
# 批次 1（验收，决议 2026-07-14）：原 6 模型 ×1、T=0.2、v0.4 题集（25+canary）
# → build rows → score_v04 评分 → 06 指标 → 09b 预注册验收判据。
# 需要环境变量 SILICONFLOW_API_KEY、DEEPSEEK_API_KEY、OPENROUTER_API_KEY（.env 亦可）。
# 断点续跑：中断后重复同一命令（runner 自动跳过 normalized 已有任务）。
# 题集冻结（验收通过）后才跑批次 2（9 模型 ×5 + 温度敏感性，另行脚本）。
#
# 渠道变更（2026-07-14，实跑与留档一致）：DeepSeek 两模型改走官方 API
# （provider=deepseek），替代原 openrouter/siliconflow 渠道——模型名随渠道变化，
# 混跑会导致同模型双名入库。注意官方渠道 max_tokens 含思考 token（SiliconFlow
# 只封顶回答），触顶失败条目按批次文档以 max_tokens=16000 单题重跑替换。
# 重试参数加固（timeout 360/retries 5/retry-sleep 30）：SiliconFlow 长思考
# 非流式生成曾遇网关瞬断，密集重试会全部撞进同一故障窗口。
set -euo pipefail
cd "$(dirname "$0")/../.."

: "${SILICONFLOW_API_KEY:?需要 SILICONFLOW_API_KEY（Kimi 与 GLM 走 siliconflow）}"
: "${DEEPSEEK_API_KEY:?需要 DEEPSEEK_API_KEY（deepseek-v4-flash/pro 走官方 API）}"
: "${OPENROUTER_API_KEY:?需要 OPENROUTER_API_KEY（qwen3.7-max）}"

run () {
  python3 scripts/run_llm_planner.py \
    --tasks dataset/tasks_public_v0.4.jsonl \
    --out-dir runs/pilot_v0.4 \
    --prompt-setting canonical_v0.4 \
    --provider "$1" --model "$2" \
    --temperature 0.2 --max-tokens 6000 \
    --timeout 360 --retries 5 --retry-sleep 30 --sleep 1
}
# GLM-4.7 渠道再变更（2026-07-14 深夜）：siliconflow 已下架该模型
# （HTTP 403 Model disabled），改走 OpenRouter（z-ai/glm-4.7，路由 Novita）。
# OpenRouter 的 max_tokens 含思考 token（同 DeepSeek 官方语义），触顶按批次
# 文档 fixup 协议处理。qwen3.7-max 与 v0.3 同渠道同 ID，零偏差。
run siliconflow Pro/moonshotai/Kimi-K2.6
run siliconflow Pro/zai-org/GLM-5.1
run openrouter  z-ai/glm-4.7
run deepseek    deepseek-v4-flash
run deepseek    deepseek-v4-pro
run openrouter  qwen/qwen3.7-max

# 每模型跑完后的体检（finish_reason=length / schema_valid=false 计数）
python3 - <<'PYEOF'
import json, glob
bad = 0
for f in sorted(glob.glob('runs/pilot_v0.4/normalized/*.jsonl')):
    rows = [json.loads(l) for l in open(f, encoding='utf-8')]
    invalid = [r['id'] for r in rows if not r.get('schema_valid')]
    if invalid:
        bad += len(invalid)
        print(f"[体检] {f}: schema_valid=false -> {invalid}")
for f in sorted(glob.glob('runs/pilot_v0.4/raw/*.jsonl')):
    for l in open(f, encoding='utf-8'):
        r = json.loads(l)
        fr = r['response_payload'].get('choices', [{}])[0].get('finish_reason')
        if fr not in (None, 'stop'):
            bad += 1
            print(f"[体检] {f}: {r['id']} finish_reason={fr}")
if bad:
    raise SystemExit(f"体检未通过：{bad} 条异常，处理后再进评分（勿带截断/空答案进 09b）")
print("[体检] 全部通过：schema_valid 全真、finish_reason 全 stop")
PYEOF

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
