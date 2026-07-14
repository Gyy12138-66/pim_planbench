#!/usr/bin/env python3
"""基线臂过冻结评分器 + 与 6 模型面板对比（修订项 #2 主表）。

步骤：
  1. 冻结评分器（subprocess，不 import 不修改）给 4 臂 × 26 题打分
  2. 交叉回归：T 臂在执行子集 5 题的总分必须与既有 arms_v0.4.csv 等值
     （同文本同评分器必须同分，防输入格式漂移）
  3. 与面板 6 模型逐题对比，产出任务级汇总 CSV + 报告节

输出：generated/baseline_arms_scored_v0.4.csv
      generated/baseline_task_totals_v0.4.csv
      generated/sections/10_baselines.md
用法：python3 score_baselines.py（须先跑 build_baseline_arms.py）
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scorer_mirror as sm

ROOT = sm.ROOT
GEN = HERE / "generated"
SECTIONS = GEN / "sections"
SCORER = ROOT / "scripts/score_3modeloutput_v03.py"
ARMS_V04 = ROOT / "update_v04/execution_validation/arms_v0.4.csv"

ARMS = ["BASE/GOLD", "BASE/S2", "BASE/S1", "BASE/T"]
ARM_LABELS = {"BASE/GOLD": "GOLD", "BASE/S2": "S2", "BASE/S1": "S1", "BASE/T": "T"}


def totals_by(rows):
    agg = defaultdict(float)
    capped = defaultdict(list)
    for r in rows:
        agg[(r["task_id"], r["model"])] += float(r["score"])
        if "cap<= " in r["score_rationale"]:
            capped[(r["task_id"], r["model"])].append(r["facet_id"])
    return agg, capped


def main() -> int:
    SECTIONS.mkdir(parents=True, exist_ok=True)
    inp = GEN / "baseline_arms_input_v0.4.csv"
    scored_path = GEN / "baseline_arms_scored_v0.4.csv"
    subprocess.run(
        [sys.executable, str(SCORER), "--input", str(inp), "--output", str(scored_path),
         "--summary", str(GEN / "baseline_summary_by_model.csv"),
         "--task-summary", str(GEN / "baseline_summary_by_task.csv")],
        check=True)

    base_rows = sm.read_rows(scored_path)
    panel_rows = sm.read_rows(sm.PANEL_SCORED)
    base_tot, base_capped = totals_by(base_rows)
    panel_tot, _ = totals_by(panel_rows)

    tasks = sorted({r["task_id"] for r in base_rows})
    models = sorted({r["model"] for r in panel_rows})

    # 交叉回归：T 臂 5 题 与 execution_validation/arms_v0.4.csv 等值
    arms_ref = {(r["task"], r["arm"]): float(r["plan_score"])
                for r in sm.read_rows(ARMS_V04)}
    for (task, arm), expect in sorted(arms_ref.items()):
        if arm != "T":
            continue
        got = base_tot[(task, "BASE/T")]
        if abs(got - expect) > 1e-9:
            raise SystemExit(f"交叉回归失败: {task} T 臂 {got} != arms_v0.4.csv {expect}")
    print(f"交叉回归 PASS: T 臂 {sum(1 for k in arms_ref if k[1]=='T')} 题与既有 arms 评分等值")

    # 任务级汇总 CSV
    out_csv = GEN / "baseline_task_totals_v0.4.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "GOLD", "S2", "S1", "T",
                    "best_model", "best_model_score", "median_model_score",
                    "gold_minus_best", "s2_beats_n_models", "gold_capped_facets"])
        stats = defaultdict(list)
        for t in tasks:
            m_scores = {m: panel_tot[(t, m)] for m in models}
            best_m = max(m_scores, key=m_scores.get)
            vals = {a: base_tot[(t, a)] for a in ARMS}
            row = [t, vals["BASE/GOLD"], vals["BASE/S2"], vals["BASE/S1"], vals["BASE/T"],
                   best_m, m_scores[best_m], median(m_scores.values()),
                   round(vals["BASE/GOLD"] - m_scores[best_m], 1),
                   sum(1 for m in models if vals["BASE/S2"] >= m_scores[m]),
                   "|".join(base_capped.get((t, "BASE/GOLD"), []))]
            w.writerow(row)
            for a in ARMS:
                stats[a].append(vals[a])
            stats["best"].append(m_scores[best_m])
            stats["median"].append(median(m_scores.values()))

    # 报告节
    lines = ["## 基线臂全题投放（T / S1 / S2 / GOLD × 26 题）", ""]
    lines.append("| 臂 | 定义 | 均分/25 | 最低 | 最高 |")
    lines.append("|---|---|---|---|---|")
    defs = {
        "BASE/GOLD": "私有参考确定性渲染（oracle 天花板，见过私有参考）",
        "BASE/S2": "关键词堆砌·白盒（评分器内部词表，最坏情形）",
        "BASE/S1": "关键词堆砌·黑盒（公开题面 + 公开 rubric 词汇）",
        "BASE/T": "通用模板计划（一份文本全题复用）",
    }
    for a in ARMS:
        v = stats[a]
        lines.append(f"| {ARM_LABELS[a]} | {defs[a]} | {mean(v):.1f} | {min(v):.0f} | {max(v):.0f} |")
    lines.append(f"| （6 模型最佳） | 每题取面板最高分模型 | {mean(stats['best']):.1f} | "
                 f"{min(stats['best']):.0f} | {max(stats['best']):.0f} |")
    lines.append(f"| （6 模型中位） | 每题面板中位数 | {mean(stats['median']):.1f} | "
                 f"{min(stats['median']):.0f} | {max(stats['median']):.0f} |")
    lines.append("")

    n_gold_ge_best = sum(1 for t in tasks
                         if base_tot[(t, "BASE/GOLD")] >= max(panel_tot[(t, m)] for m in models))
    n_s2_ge_best = sum(1 for t in tasks
                       if base_tot[(t, "BASE/S2")] >= max(panel_tot[(t, m)] for m in models))
    n_s2_ge_med = sum(1 for t in tasks
                      if base_tot[(t, "BASE/S2")] >= median(panel_tot[(t, m)] for m in models))
    n_s1_ge_med = sum(1 for t in tasks
                      if base_tot[(t, "BASE/S1")] >= median(panel_tot[(t, m)] for m in models))
    n_t_ge_med = sum(1 for t in tasks
                     if base_tot[(t, "BASE/T")] >= median(panel_tot[(t, m)] for m in models))
    capped_counts = {a: sum(1 for t in tasks if base_capped.get((t, a))) for a in ARMS}

    lines += [
        f"- GOLD ≥ 当题最佳模型：{n_gold_ge_best}/26 题；"
        f"GOLD 被 cap 击中的题数：{capped_counts['BASE/GOLD']}/26"
        "（trap 描述文本触发负向规则的行数见任务级 CSV，属 oracle 渲染的已知伪影，如实报告）",
        f"- S2（白盒堆砌）≥ 当题最佳模型：{n_s2_ge_best}/26；≥ 当题中位模型：{n_s2_ge_med}/26；"
        f"被 cap 击中：{capped_counts['BASE/S2']}/26",
        f"- S1（黑盒堆砌）≥ 当题中位模型：{n_s1_ge_med}/26；被 cap 击中：{capped_counts['BASE/S1']}/26",
        f"- T（模板）≥ 当题中位模型：{n_t_ge_med}/26；被 cap 击中：{capped_counts['BASE/T']}/26",
        "",
        "### 解读（如实报告，不回避）",
        "",
        "- **模板防线有效**：连贯但零任务特异的 T 臂被稳定压制（0/26 达中位），"
        "generic cap 与 pf_strict 按设计工作。",
        "- **关键词堆砌防线失守**：S1 只用公开信息即在多数题上超过中位模型，"
        "甚至超过 oracle 渲染（题面词 + rubric 词的堆砌同时喂饱了 core cue 覆盖率、"
        "参考项 token 匹配率与全部长度/missing 加分，而作为无结构词表又几乎不踩"
        "任何负向规则）。这实证确认了 PdEo 的 rubric-matching text 质疑在 v0.3 "
        "覆盖层上成立——人类或 LLM 评审对这类无结构词表会给 0 分，纯覆盖匹配层"
        "无法分辨。",
        "- **对应的既定修订动作**：修订项 #1 的可核验断言重写（欠定规格逼真实"
        "建模决策，词表堆砌无法给出定量断言）与修订项 #2 的 scorer v0.4 断言"
        "核验层；v0.4 重打分时此表即论文的 before/after 对比列。"
        "建议（待作者确认）：S1/S2 两臂并入评分器发布门的对抗回归套件。",
        "- GOLD 被 cap 击中的 3 题源于 failure_trap 描述文本里含触发词（oracle "
        "逐条渲染的已知伪影）；GOLD 定位是自动评分口径下的天花板锚点，"
        "非人工润色的专家计划。",
        "",
        "任务级明细：`generated/baseline_task_totals_v0.4.csv`；"
        "facet 级评分：`generated/baseline_arms_scored_v0.4.csv`。",
        "",
    ]
    (SECTIONS / "10_baselines.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"任务级汇总 -> {out_csv}")
    print("\n".join(lines[-8:-3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
