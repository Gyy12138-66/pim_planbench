#!/usr/bin/env python3
"""评分器 v0.4 对抗回归套件：55 臂（5 题 × N1–N6/G/T/D1–D3）。

任何评分器（v0.4 断言核验层）候选版本必须全部通过：
  R1  D3 篡改臂（003/005/016/023）→ 必须检出 numeric_contradiction
  R2  D3 幻觉组件臂（010）        → 必须检出 fabricated_component
  R3  D2 任务类型臂（全部 5 题）  → 必须检出 wrong_task_type
  R4  G / T / N1–N6 / D1          → 零检出（误伤门：金计划/模板/自然臂不许误 cap）
  R5  cap 后 D2/D3 总分必须低于同题 G（v0.3 里 D3 与 G 同分即动机缺陷）

输出：regression_report.md（含 v0.3 vs v0.4 分数对照）；exit 0 = 全部通过。
用法：python run_regression.py [--arms-dir ../execution_validation/arms_text/generated]
"""
import argparse
import os
import sys

import pandas as pd

from claim_verifier import verify_arm, apply_caps

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(HERE, "..", "execution_validation", "arms_text", "generated")
FACETS = ["Problem Formalization", "Physics Constraints", "Model Choice",
          "Training Strategy", "Validation Failure Risks"]


def arm_id(model):
    return model.split("/", 1)[1] if model.startswith("ARM/") else model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms-dir", default=DEFAULT_DIR)
    ap.add_argument("--out", default=os.path.join(HERE, "regression_report.md"))
    args = ap.parse_args()

    texts = pd.read_csv(os.path.join(args.arms_dir, "arms_input_v0.4.csv"))
    scored = pd.read_csv(os.path.join(args.arms_dir, "arms_scored_v0.4.csv"))

    rows, failures = [], []
    for (task, model), sub in texts.groupby(["task_id", "model"]):
        aid = arm_id(model)
        ftexts = dict(zip(sub["facet"], sub["model_answer"]))
        findings = verify_arm(task, ftexts)
        kinds = {f.kind for f in findings}

        ssub = scored[(scored["task_id"] == task) & (scored["model"] == model)]
        fscores = dict(zip(ssub["facet"], ssub["score"]))
        capped, hit = apply_caps(fscores, findings)
        v03 = sum(fscores.values())
        v04 = sum(capped.values())
        rows.append(dict(task=task, arm=aid, kinds="|".join(sorted(kinds)) or "-",
                         n_findings=len(findings), v03=v03, v04=v04,
                         capped_facets="|".join(sorted(hit)) or "-"))

        # 期望检查
        is_ablation_target = aid in ("D2", "D3")
        if aid == "D3":
            if task == "medium_burgers_inverse_viscosity_010":
                if "fabricated_component" not in kinds:
                    failures.append(f"R2 未检出: {task}/D3 幻觉组件")
            elif "numeric_contradiction" not in kinds:
                failures.append(f"R1 未检出: {task}/D3 数值篡改")
        elif aid == "D2":
            if "wrong_task_type" not in kinds:
                failures.append(f"R3 未检出: {task}/D2 任务类型")
        elif findings:
            for f in findings:
                failures.append(f"R4 误伤: {task}/{aid} {f.kind} ({f.detail}) [{f.snippet[:60]}]")

    df = pd.DataFrame(rows)

    # R5: cap 后 D2/D3 < 同题 G
    for task, sub in df.groupby("task"):
        g = sub[sub["arm"] == "G"]["v04"]
        if not len(g):
            continue
        for _, r in sub[sub["arm"].isin(["D2", "D3"])].iterrows():
            if r["v04"] >= float(g.iloc[0]):
                failures.append(f"R5 未分离: {task}/{r['arm']} v0.4={r['v04']} >= G={float(g.iloc[0])}")

    ok = not failures
    lines = ["# 评分器 v0.4 回归套件报告", "",
             f"**结论：{'全部通过' if ok else f'{len(failures)} 项失败'}**", ""]
    if failures:
        lines += ["## 失败项", ""] + [f"- {f}" for f in failures] + [""]
    lines += ["## 55 臂明细（v0.3 总分 vs v0.4 cap 后总分）", "",
              df.sort_values(["task", "arm"]).to_markdown(index=False), "",
              "## 判据", "",
              "R1 D3 数值篡改检出（003/005/016/023）；R2 D3 幻觉组件检出（010）；",
              "R3 D2 任务类型检出（5 题）；R4 G/T/N/D1 零误伤；R5 cap 后 D2/D3 < G。", ""]
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{'PASS' if ok else 'FAIL'} -> {args.out}")
    for fl in failures:
        print("FAIL:", fl)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
