#!/usr/bin/env bash
# 评分器 v0.4 对抗回归套件（R1-R5 发布门）：任何评分器改动后必须重跑并 PASS。
set -euo pipefail
cd "$(dirname "$0")/../scorer_v04"
python3 run_regression.py
