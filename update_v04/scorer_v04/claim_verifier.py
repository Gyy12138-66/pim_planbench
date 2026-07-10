#!/usr/bin/env python3
"""断言核验层（scorer v0.4 原型）：检测计划文本中与任务规格矛盾的断言。

v0.3 评分器只做线索覆盖匹配（该提没提），本层补"提了但说错"：
  1. numeric_contradiction —— 数值断言与任务实例化规格矛盾（→ hallucination cap）
  2. wrong_task_type      —— 正/反问题声明与规格矛盾（→ wrong-task-type cap）
  3. fabricated_component —— 编造的损失组件符号（白名单外的 L_xxx，→ hallucination cap）

设计约束：精确率优先——cap 只在断言无歧义矛盾时触发，误伤金计划比漏放篡改臂更糟。
规格表目前覆盖执行效度子集 5 题（协议 §3 冻结的实例化）；扩到 26 题随修订项 #1/#3 推进。
触发的 cap 按 rubric v0.3：受影响 facet 封顶 2 分。

用法（库）：verify_arm(task_id, {facet: text}) -> [Finding]
用法（CLI）：python claim_verifier.py --arms-csv <arms_input_v0.4.csv>
"""
import argparse
import math
import re
from dataclasses import dataclass

NUM = r'([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)'
CAP_SCORE = 2

# 执行效度子集的实例化规格（协议 §3，冻结于 8e7d3aa）
SPECS = {
    "easy_advection_1d_periodic_005": {
        "task_type": "forward",
        "params": [
            # (参数名, 真值, 相对容差, 断言抽取模式列表)
            ("c", 1.0, 0.01,
             [r"(?:transport|advection)\s+speed\s+c\s*=\s*" + NUM,
              r"\bspeed\s+c\s*=\s*" + NUM,
              r"\bc\s*=\s*" + NUM]),
        ],
    },
    "easy_poisson_2d_source_003": {
        "task_type": "forward",
        "params": [
            ("source_scale", 2.0, 0.01,
             [NUM + r"\s*\*\s*pi\^2\s*\*\s*sin\(pi\*x\)"]),
        ],
    },
    "medium_burgers_inverse_viscosity_010": {
        "task_type": "inverse",
        # nu 是待估未知量：声称"已知/固定 nu=X"= 任务类型证据；初始化值合法
        "params": [
            ("nu(known)", math.nan, 0.0,
             [r"known\s+viscosity\s+nu\s*=\s*" + NUM,
              r"viscosity\s+nu\s*=\s*" + NUM + r"\s+(?:is\s+)?(?:known|given|fixed)"]),
        ],
    },
    "hard_allen_cahn_016": {
        "task_type": "forward",
        "params": [
            ("d", 1e-4, 0.01,
             [r"diffusion\s+coefficient\s+d\s*=\s*" + NUM,
              r"\bd\s*=\s*" + NUM]),
        ],
    },
    "hard_plus_euler_shock_023": {
        "task_type": "forward",
        "params": [
            ("gamma", 1.4, 0.01,
             [r"gamma\s*=\s*" + NUM]),
        ],
    },
}

# 任务类型声明模式（仅在 Problem Formalization facet 上判定，取声明性强的表述）
INVERSE_DECL = [
    r"^\s*Inverse\b",
    r"\binverse\s+[\w-]*\s*(?:problem|calibration)\b",
    r"\b(?:estimate|recover|infer)\s+the\s+unknown\b",
]
FORWARD_DECL = [
    r"^\s*Forward\s+problem\b",
    r"\bthis\s+is\s+a\s+forward\s+problem\b",
]

# 编造组件检测：自定义损失符号（L_weak 等）是合法的高分行为，符号白名单会误伤；
# 编造的判定特征是"虚假权威声明"——把杜撰方法说成领域标准并声称有已知保证。
FABRICATION_PATTERN = re.compile(
    r"\b(?:standard|classical|well-known|widely[- ]used)\b[^.]{0,80}\bloss\b"
    r"[^.]{0,150}\b(?:known to (?:guarantee|ensure)|guarantees)\b",
    re.IGNORECASE)


@dataclass
class Finding:
    task: str
    facet: str
    kind: str          # numeric_contradiction | wrong_task_type | fabricated_component
    detail: str
    snippet: str

    def capped_facets(self):
        if self.kind == "wrong_task_type":
            # rubric: PF 与 Model Choice 封顶 2
            return ["Problem Formalization", "Model Choice"]
        return [self.facet]


def _norm(text):
    t = text.replace("π", "pi").replace("γ", "gamma").replace("ν", "nu")
    t = t.replace("²", "^2").replace("−", "-")
    return re.sub(r"\s+", " ", t)


def _check_numeric(task, spec, facet, text, findings):
    for name, true_val, rtol, patterns in spec.get("params", []):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if not m:
                continue
            claimed = float(m.group(1))
            if math.isnan(true_val):
                # 待估参数被断言为已知值：本身即矛盾（无论数值）
                findings.append(Finding(task, facet, "wrong_task_type",
                                        f"{name}: 待估未知量被断言为已知 {claimed}",
                                        m.group(0)))
            elif abs(claimed - true_val) > rtol * abs(true_val):
                findings.append(Finding(task, facet, "numeric_contradiction",
                                        f"{name}: 断言 {claimed} vs 规格 {true_val}",
                                        m.group(0)))
            break  # 每参数取首个命中的模式，避免宽模式重复计
    return findings


def _check_task_type(task, spec, facet, text, findings):
    if facet != "Problem Formalization":
        return findings
    decls = INVERSE_DECL if spec["task_type"] == "forward" else FORWARD_DECL
    for pat in decls:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            findings.append(Finding(task, facet, "wrong_task_type",
                                    f"声明与规格任务类型（{spec['task_type']}）矛盾",
                                    m.group(0)))
            break
    return findings


def _check_fabricated(task, facet, text, findings):
    m = FABRICATION_PATTERN.search(text)
    if m:
        findings.append(Finding(task, facet, "fabricated_component",
                                "杜撰组件冠以领域标准名义并声称已知保证",
                                m.group(0)[:120]))
    return findings


def verify_arm(task_id, facet_texts):
    """facet_texts: {facet_name: model_answer}；返回 Finding 列表。"""
    spec = SPECS.get(task_id)
    findings = []
    for facet, raw in facet_texts.items():
        if not isinstance(raw, str) or not raw.strip():
            continue
        text = _norm(raw)
        if spec:
            _check_numeric(task_id, spec, facet, text, findings)
            _check_task_type(task_id, spec, facet, text, findings)
        _check_fabricated(task_id, facet, text, findings)
    return findings


def apply_caps(facet_scores, findings):
    """facet_scores: {facet: 0-5}；返回 (capped_scores, 受影响 facet 集合)。"""
    capped = dict(facet_scores)
    hit = set()
    for f in findings:
        for facet in f.capped_facets():
            if facet in capped and capped[facet] > CAP_SCORE:
                capped[facet] = CAP_SCORE
            hit.add(facet)
    return capped, hit


def main():
    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms-csv", required=True,
                    help="facet 行格式 CSV（task_id, model, facet, model_answer）")
    args = ap.parse_args()
    df = pd.read_csv(args.arms_csv)
    for (task, model), sub in df.groupby(["task_id", "model"]):
        texts = dict(zip(sub["facet"], sub["model_answer"]))
        for f in verify_arm(task, texts):
            print(f"{task} | {model} | {f.facet} | {f.kind} | {f.detail}")


if __name__ == "__main__":
    main()
