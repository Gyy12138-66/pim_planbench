#!/usr/bin/env bash
# 全量运行进度看板：已完成 run 数 / 151、发散计数、最近日志。
set -euo pipefail
cd "$(dirname "$0")/../execution_validation"

if [ -f results_v0.4.csv ]; then
  done_n=$(($(wc -l < results_v0.4.csv) - 1))
  div_n=$(awk -F, 'NR>1 && $6==1' results_v0.4.csv | wc -l | tr -d ' ')
  echo "进度：$done_n / 150 完成（发散 $div_n 个——发散是合法结果）"
else
  echo "results_v0.4.csv 尚不存在——运行未开始或未产出首行"
fi

log=$(ls -t run_mps.log run.log 2>/dev/null | head -1 || true)
if [ -n "${log:-}" ]; then
  echo "--- 最近日志（$log）："
  tail -5 "$log"
fi
pgrep -fl "run_validation.py" >/dev/null 2>&1 && echo "--- 进程：在跑" || echo "--- 进程：未在跑"
