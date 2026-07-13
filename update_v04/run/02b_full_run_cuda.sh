#!/usr/bin/env bash
# 全量执行运行（云 CUDA 路线）：在租用机（vast.ai/runpod，RTX 4090/5080 级）执行。
# 环境准备见 execution_validation/RUN_ON_GPU.md §1-2；本脚本 = 手册第 3+5 步。
# 跑完回传 results_v0.4.csv 与 run.log 两个文件（手册第 6 步）。
set -euo pipefail
cd "$(dirname "$0")/../execution_validation"

python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA 不可用——本脚本用于租用 GPU 机'"
python3 references.py --self-test

nohup python3 run_validation.py --configs configs/arms --seeds 0 1 2 \
    --out results_v0.4.csv > run.log 2>&1 &
echo "已后台启动 (PID $!)。预计 15-20 GPU·时。监控：tail -f run.log"
