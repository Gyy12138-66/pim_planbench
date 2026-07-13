#!/usr/bin/env bash
# 参考解自检：Sod 星区 p*=0.30313/u*=0.92745、Burgers 奇对称 ~1e-9、AC 值域。
# 全量运行(02/02b)前必须 PASS。
set -euo pipefail
cd "$(dirname "$0")/../execution_validation"
python3 references.py --self-test
