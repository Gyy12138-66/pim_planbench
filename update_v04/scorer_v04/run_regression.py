#!/usr/bin/env python3
"""评分器 v0.4 对抗回归套件：55 臂（5 题 × N1–N6/G/T/D1–D3）+ 堆砌臂 R6。

任何评分器（v0.4 断言核验层）候选版本必须全部通过：
  R1  D3 篡改臂（003/005/016/023）→ 必须检出 numeric_contradiction
  R2  D3 幻觉组件臂（010）        → 必须检出 fabricated_component
  R3  D2 任务类型臂（全部 5 题）  → 必须检出 wrong_task_type
  R4  G / T / N1–N6 / D1          → 零检出（误伤门：金计划/模板/自然臂不许误 cap）
  R5  cap 后 D2/D3 总分必须低于同题 G（v0.3 里 D3 与 G 同分即动机缺陷）
  R6  关键词堆砌臂 S1/S2（baselines_v04 构造 × v0.4 全题 × 新核验器
      claim_verifier_v04）→ 矛盾类零检出。无结构词表不含数值与声明，
      numeric/wrong_task_type/fabricated/spec/internal/structural 类触发
      即模式过宽；claim_without_support 类触发属正当遏制（"提及即口头
      声明"语义），计数入报告不判失败。依据：baselines_v04 报告显示
      堆砌击穿 v0.3 覆盖层（S1 均分 24.1/25），遏制职责在断言层 + 重写。

输出：regression_report.md（含 v0.3 vs v0.4 分数对照）；exit 0 = 全部通过。
用法：python run_regression.py [--arms-dir ../execution_validation/arms_text/generated]
"""
import argparse
import json
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


CONTRADICTION_KINDS = {"numeric_contradiction", "wrong_task_type",
                       "fabricated_component", "spec_contradiction",
                       "internal_inconsistency", "structural_contradiction"}


def run_r6(failures):
    """R6：S1/S2 堆砌臂 × v0.4 全题 × claim_verifier_v04，矛盾类零检出。"""
    sys.path.insert(0, os.path.join(HERE, "..", "baselines_v04"))
    import build_baseline_arms as bba
    import claim_verifier_v04 as cv4

    root = os.path.join(HERE, "..", "..")
    refs = cv4.load_references(os.path.join(root, "dataset", "references_private_v0.4.jsonl"))
    with open(os.path.join(root, "dataset", "tasks_public_v0.4.jsonl"),
              encoding="utf-8") as fh:
        tasks = [json.loads(l) for l in fh if l.strip()]
    vocab = bba.rubric_vocab()

    rows, n_arms = [], 0
    for t in tasks:
        if t["id"].startswith("canary_"):
            continue
        for arm in ("S1", "S2"):
            n_arms += 1
            texts = {fname: (bba.s1_text(fname, t, vocab) if arm == "S1"
                             else bba.s2_text(fname, fid))
                     for fname, fid in bba.FACETS}
            findings = cv4.verify_entry(refs[t["id"]], texts)
            contra = [f for f in findings if f.kind in CONTRADICTION_KINDS]
            support = [f for f in findings if f.kind not in CONTRADICTION_KINDS]
            for f in contra:
                failures.append(
                    f"R6 模式过宽: {t['id']}/{arm} {f.kind}（词表堆砌不构成断言）")
            if findings:
                rows.append(dict(task=t["id"], arm=arm,
                                 contradiction=len(contra), support=len(support),
                                 kinds="|".join(sorted({f.kind for f in findings}))))
    return n_arms, rows


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

    r6_arms, r6_rows = run_r6(failures)

    ok = not failures
    lines = ["# 评分器 v0.4 回归套件报告", "",
             f"**结论：{'全部通过' if ok else f'{len(failures)} 项失败'}**", ""]
    if failures:
        lines += ["## 失败项", ""] + [f"- {f}" for f in failures] + [""]
    lines += ["## 55 臂明细（v0.3 总分 vs v0.4 cap 后总分）", "",
              df.sort_values(["task", "arm"]).to_markdown(index=False), "",
              f"## R6 堆砌臂（S1/S2 × {r6_arms // 2} 题 × claim_verifier_v04）", "",
              f"矛盾类检出 0/{r6_arms}（门）；有检出的臂如下"
              "（support 类 = claim_without_support，属正当遏制记录）：", ""]
    if r6_rows:
        lines += [pd.DataFrame(r6_rows).to_markdown(index=False), ""]
    else:
        lines += ["（本次无任何检出）", ""]
    lines += ["## 判据", "",
              "R1 D3 数值篡改检出（003/005/016/023）；R2 D3 幻觉组件检出（010）；",
              "R3 D2 任务类型检出（5 题）；R4 G/T/N/D1 零误伤；R5 cap 后 D2/D3 < G；",
              "R6 S1/S2 堆砌臂矛盾类零检出（support 类计数入报告）。", ""]
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{'PASS' if ok else 'FAIL'} -> {args.out}")
    for fl in failures:
        print("FAIL:", fl)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
