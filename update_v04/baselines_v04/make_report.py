#!/usr/bin/env python3
"""汇总 generated/sections/*.md → baselines_report.md（修订项 #2 报告）。"""
from __future__ import annotations

from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECTIONS = HERE / "generated" / "sections"

HEADER = f"""# 基线与消融报告（修订项 #2，v0.4）

生成：`update_v04/run/08_baselines_v04.sh`（确定性，可复现）；日期 {date.today().isoformat()}。

回应评审：PdEo（"rubric-matching text" 可套分、"Eq. 5's constants are unexplained
with no ablation"）、d2gd（缺 expert-written / template baseline）。

## 臂定义与威胁模型

| 臂 | 威胁模型 | 可见信息 |
|---|---|---|
| T | 表述胜任但零任务特异的通用模板计划 | 无（一份文本全题复用） |
| S1 | 黑盒关键词堆砌：读过公开 rubric 来套分的对手 | 公开题面 + `docs/rubric_v0.3.md` |
| S2 | 白盒关键词堆砌（最坏情形）：读过评分器源码的对手 | 评分器内部线索词表与门控词 |
| GOLD | oracle 天花板：私有参考字段的确定性渲染 | 私有参考全部字段（**不冒充专家手写计划**） |

S1/S2 均为无结构关键词罗列（非连贯计划）；GOLD 渲染复用评分器
`reference_items()` 的字段→facet 映射，参考项逐条拼接，无人工润色。
所有重打分基于冻结评分器 `scripts/score_3modeloutput_v03.py`（只调用，未改动）；
cap 消融与 Eq.5 敏感性使用参数化镜像，默认参数下与冻结评分器逐行等值
（守卫断言，见 `scorer_mirror.py`）。

"""


def main() -> int:
    parts = [HEADER]
    for sec in sorted(SECTIONS.glob("*.md")):
        parts.append(sec.read_text(encoding="utf-8"))
    out = HERE / "baselines_report.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"报告 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
