#!/usr/bin/env bash
# 全量执行运行（本机 MPS 路线）：150 次训练，后台 nohup，断点续跑。
# 设备一致性决策与散热注意见 execution_validation/RUN_LOCAL_MPS.md。
# 中断后重复本命令即可续跑（已完成的 (config,seed) 自动跳过）。
set -euo pipefail
cd "$(dirname "$0")/../execution_validation"

python3 make_mps_configs.py

if pgrep -f "run_validation.py --configs configs_mps/arms" >/dev/null; then
  echo "已有全量运行在跑，勿重复启动。查看进度：bash update_v04/run/03_status.sh"
  exit 1
fi

nohup python3 run_validation.py --configs configs_mps/arms --seeds 0 1 2 \
    --out results_v0.4.csv > run_mps.log 2>&1 &
echo "已后台启动 (PID $!)。预计 2.5-3 天。"
echo "监控：bash update_v04/run/03_status.sh"
echo "完成判据：results_v0.4.csv 达到 151 行（表头+150）"
