#!/usr/bin/env bash
# 修订项 #2 基线与消融包：T/S1/S2/GOLD 全题投放 + cap 开/关 + Eq.5 敏感性。
# 纯本地重打分（分钟级），不依赖 API，不触碰 task_rewrites_v0.4 与 dataset。
set -euo pipefail
cd "$(dirname "$0")/../baselines_v04"
python3 build_baseline_arms.py
python3 score_baselines.py
python3 cap_onoff_rescore.py
python3 eq5_sensitivity.py
python3 make_report.py
echo "OK: update_v04/baselines_v04/baselines_report.md"
