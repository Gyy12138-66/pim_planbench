#!/usr/bin/env bash
# IAA 一致性分析：加权 κ / Krippendorff α / 排名 τ + 协议 §5 判定。
# 现在（无数据）自检：bash 07_analyze_iaa.sh --demo
# 数据到位后：      bash 07_analyze_iaa.sh <iaa_scores_raw.csv> [auto.csv] [code_map.csv]
set -euo pipefail
cd "$(dirname "$0")/../scripts"

if [ "${1:-}" = "--demo" ]; then
  python3 analyze_iaa.py --demo --outdir ../run/iaa_demo_check
elif [ -n "${1:-}" ]; then
  python3 analyze_iaa.py --scores "$1" ${2:+--auto "$2"} ${3:+--code-map "$3"} \
      --outdir ../docs/iaa_analysis_v0.4
else
  echo "用法见脚本头部注释"; exit 1
fi
