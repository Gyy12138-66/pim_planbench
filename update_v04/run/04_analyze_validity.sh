#!/usr/bin/env bash
# 执行效度分析：解盲 + H4a/H4b/H4c + 010 ν表 + facet 相关（协议 §6 全条款）。
# 辅助输入（code map/configs/facet 分/多样性表）自动探测。
set -euo pipefail
cd "$(dirname "$0")/../execution_validation"

[ -f results_v0.4.csv ] || { echo "缺 results_v0.4.csv——先完成全量运行（02/02b）"; exit 1; }
n=$(($(wc -l < results_v0.4.csv) - 1))
[ "$n" -lt 150 ] && echo "警告：仅 $n/150 个 run，分析将按不完整数据出告警"

python3 analyze_validity.py --results results_v0.4.csv --arms arms_v0.4.csv \
    --outdir analysis_v0.4
echo "报告：execution_validation/analysis_v0.4/validity_summary.md"
