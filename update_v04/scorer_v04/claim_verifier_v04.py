#!/usr/bin/env python3
"""断言核验层 v0.4 —— 通用加载器（schema §3.2/§3.4，取代 v0.3 的硬编码 SPECS）。

数据驱动（决定 D1）：全部任务特异断言存于 references_private_v0.4.jsonl 的
`verifiable_claims` 字段；本模块只实现 7 种 claim 类型的判定语义 + 两个全局
检查（任务类型声明、编造组件），不含任何逐题内容。

claim 类型 → finding kind：
  param_value            → numeric_contradiction
  asserted_known_unknown → wrong_task_type
  sign_relation          → numeric_contradiction
  arithmetic_consistency → internal_inconsistency
  co_occurrence          → structural_contradiction
  claim_without_support  → unsupported_claim
  forbidden_assertion    → spec_contradiction
全局：task_type_decl → wrong_task_type；fabrication → fabricated_component。

设计约束沿 v0.3：精确率优先，cap 只在断言无歧义矛盾时触发；每参数/每 claim
取首个命中模式。cap 应用完全由数据侧 facet_cap_rules 驱动（决定 D2）：
finding.rule_id → 规则的 affected_facets 封顶 max_score；affected_facets=[]
表示封顶检出所在 facet。

用法（库）：
    ref = load_references(path)[task_id]
    findings = verify_entry(ref, {facet_display_name: text})
    capped, hit = apply_caps(facet_scores, findings, ref)   # facet_scores 键为 facet_id
用法（CLI）：
    python3 claim_verifier_v04.py --references <jsonl> --arms-csv <csv>
    python3 claim_verifier_v04.py --references <jsonl> --selftest   # 金/篡改自测
"""
import argparse
import json
import re
from dataclasses import dataclass

# ── facet 命名（schema §2.2 唯一映射表）─────────────────────────────────
FACET_DISPLAY = {
    "problem_formalization": "Problem Formalization",
    "physics_constraints": "Physics Constraints",
    "model_choice": "Model Choice",
    "training_strategy": "Training Strategy",
    "validation_failure_risks": "Validation Failure Risks",
}
FACET_ID = {v: k for k, v in FACET_DISPLAY.items()}
FACET_ORDER = list(FACET_DISPLAY)

# ── 全局模式（任务无关，留在代码；schema §3.2）──────────────────────────
INVERSE_DECL = [
    r"^\s*Inverse\b",
    r"\binverse\s+[\w-]*\s*(?:problem|calibration)\b",
    r"\b(?:estimate|recover|infer)\s+the\s+unknown\b",
]
FORWARD_DECL = [
    r"^\s*Forward\s+problem\b",
    r"\bthis\s+is\s+a\s+forward\s+problem\b",
]
FABRICATION_PATTERN = re.compile(
    r"\b(?:standard|classical|well-known|widely[- ]used)\b[^.]{0,80}\bloss\b"
    r"[^.]{0,150}\b(?:known to (?:guarantee|ensure)|guarantees)\b",
    re.IGNORECASE)

GREEK = {
    "π": "pi", "γ": "gamma", "ν": "nu", "κ": "kappa", "θ": "theta", "μ": "mu",
    "ε": "epsilon", "α": "alpha", "β": "beta", "ρ": "rho", "Δ": "delta",
    "∇": "nabla", "∂": "d", "²": "^2", "³": "^3", "−": "-", "×": "*", "·": "·",
}


@dataclass
class Finding:
    task: str
    facet_id: str          # 检出所在 facet（plan 作用域时为 claim 首个 facet）
    claim_id: str          # 全局检查为 "task_type_decl" / "fabrication"
    kind: str
    rule_id: str           # 对应 facet_cap_rules；全局检查用标准规则 id
    detail: str
    snippet: str


def _norm(text):
    t = text
    for k, v in GREEK.items():
        t = t.replace(k, v)
    return re.sub(r"[ \t]+", " ", t)


def _to_float(s):
    s = s.replace(",", "").strip()
    if "/" in s:
        a, b = s.split("/", 1)
        return float(a.strip()) / float(b.strip())
    return float(s)


def _first_match(patterns, text):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m
    return None


def _scope_text(claim, facet_texts_norm):
    """返回 [(facet_id, text)]：facet 作用域逐 facet 查；plan 作用域合并全文。"""
    if claim.get("scope", "facet") == "plan":
        joined = "\n".join(facet_texts_norm.get(f, "") for f in FACET_ORDER)
        return [(claim["facets"][0], joined)]
    return [(f, facet_texts_norm.get(f, "")) for f in claim["facets"]]


# ── 各 claim 类型判定 ────────────────────────────────────────────────────
def _check_claim(task, claim, facet_texts_norm):
    ctype = claim["type"]
    out = []
    for facet_id, text in _scope_text(claim, facet_texts_norm):
        if not text.strip():
            continue
        f = None
        if ctype == "param_value":
            m = _first_match(claim["patterns"], text)
            if m:
                try:
                    claimed = _to_float(m.group(1))
                except ValueError:
                    continue
                true, rtol = claim["true_value"], claim["rtol"]
                if abs(claimed - true) > rtol * abs(true):
                    f = ("numeric_contradiction",
                         f"{claim['param']}: 断言 {claimed} vs 规格 {true}", m.group(0))
        elif ctype == "asserted_known_unknown":
            m = _first_match(claim["patterns"], text)
            if m:
                f = ("wrong_task_type",
                     f"{claim['param']}: 待估未知量被断言为已知值", m.group(0))
        elif ctype == "sign_relation":
            m = _first_match(claim["sign_patterns"], text)
            if m:
                s = 1
                for g in m.groups():
                    if g == "-":
                        s = -s
                canonical = 1 if claim["canonical"] == "+" else -1
                if s != canonical:
                    f = ("numeric_contradiction",
                         f"{claim['quantity']}: 符号与规范式 ({claim['canonical']}) 矛盾",
                         m.group(0))
        elif ctype == "arithmetic_consistency":
            vals, snippets = {}, []
            for name, pats in claim["quantities"].items():
                m = _first_match(pats, text)
                if not m:
                    vals = None
                    break
                try:
                    vals[name] = _to_float(m.group(1))
                except ValueError:
                    vals = None
                    break
                snippets.append(m.group(0))
            if vals:  # 全部量抽到才判（precision 优先）
                ns = dict(vals)
                ns.update({"abs": abs, "min": min, "max": max, "__builtins__": {}})
                if not eval(claim["expression"], ns):  # noqa: S307 受控表达式
                    f = ("internal_inconsistency",
                         f"{claim['expression']} 不成立: {vals}", " | ".join(snippets))
        elif ctype == "co_occurrence":
            ma = re.search(claim["pattern_a"], text, re.IGNORECASE)
            mb = re.search(claim["pattern_b"], text, re.IGNORECASE)
            if ma and mb:
                f = ("structural_contradiction", claim["description"], ma.group(0))
        elif ctype == "claim_without_support":
            ma = re.search(claim["pattern"], text, re.IGNORECASE)
            if ma and not any(re.search(p, text, re.IGNORECASE)
                              for p in claim["support_patterns"]):
                f = ("unsupported_claim", claim["description"], ma.group(0))
        elif ctype == "forbidden_assertion":
            m = _first_match(claim["patterns"], text)
            if m:
                f = ("spec_contradiction", claim["description"], m.group(0))
        else:
            raise ValueError(f"unknown claim type: {ctype}")
        if f:
            kind, detail, snippet = f
            out.append(Finding(task, facet_id, claim["claim_id"], kind,
                               claim["on_contradiction"], detail, snippet[:120]))
            break  # 每 claim 至多一条 finding
    return out


def verify_entry(ref, facet_texts):
    """ref: v0.4 私有参考条目；facet_texts 键可为显示名或 facet_id。"""
    task = ref["id"]
    norm = {}
    for k, v in facet_texts.items():
        fid = FACET_ID.get(k, k)
        if fid in FACET_DISPLAY and isinstance(v, str):
            norm[fid] = _norm(v)
    findings = []
    for claim in ref.get("verifiable_claims", []):
        findings.extend(_check_claim(task, claim, norm))
    decl = ref.get("task_type_decl")
    if decl:
        pf = norm.get("problem_formalization", "")
        decls = INVERSE_DECL if decl == "forward" else FORWARD_DECL
        m = _first_match(decls, pf)
        if m:
            findings.append(Finding(task, "problem_formalization", "task_type_decl",
                                    "wrong_task_type", "cap_wrong_task_type",
                                    f"声明与规格任务类型（{decl}）矛盾", m.group(0)[:120]))
    for fid, text in norm.items():
        m = FABRICATION_PATTERN.search(text)
        if m:
            findings.append(Finding(task, fid, "fabrication", "fabricated_component",
                                    "cap_fabricated_component",
                                    "杜撰组件冠以领域标准名义并声称已知保证", m.group(0)[:120]))
    return findings


def apply_caps(facet_scores, findings, ref):
    """facet_scores: {facet_id: 0-5}。返回 (capped, hit_facets)。数据侧规则驱动（D2）。"""
    rules = {r["rule_id"]: r for r in ref.get("facet_cap_rules", [])}
    capped, hit = dict(facet_scores), set()
    for f in findings:
        rule = rules.get(f.rule_id)
        if rule is None:
            raise KeyError(f"{f.task}: finding 引用未定义规则 {f.rule_id}")
        affected = rule["affected_facets"] or [f.facet_id]
        for fid in affected:
            if fid in capped and capped[fid] > rule["max_score"]:
                capped[fid] = rule["max_score"]
            hit.add(fid)
    return capped, hit


def load_references(path):
    refs = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                d = json.loads(line)
                refs[d["id"]] = d
    return refs


# ── selftest：每条 claim 的金/篡改文本回归（schema §5 步骤 3 的机器化）────
def run_selftests(refs, verbose=False):
    n_ok = n_fail = 0
    failures = []
    for ref in refs.values():
        for claim in ref.get("verifiable_claims", []):
            st = claim.get("selftest")
            if not st:
                failures.append((ref["id"], claim["claim_id"], "selftest 缺失"))
                n_fail += 1
                continue
            single = {**ref, "verifiable_claims": [claim], "task_type_decl": None}
            for label, text, expect in (("gold", st["gold"], 0), ("tamper", st["tamper"], 1)):
                texts = {fid: text for fid in claim["facets"]}
                got = [x for x in verify_entry(single, texts) if x.claim_id == claim["claim_id"]]
                if (len(got) > 0) != (expect > 0):
                    failures.append((ref["id"], claim["claim_id"],
                                     f"{label}: 期望 {'检出' if expect else '零误伤'}, 实得 {len(got)}"))
                    n_fail += 1
                else:
                    n_ok += 1
                    if verbose:
                        print(f"  ok {ref['id']}/{claim['claim_id']}/{label}")
    return n_ok, n_fail, failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--references", required=True)
    ap.add_argument("--arms-csv", help="facet 行格式 CSV（task_id, model, facet, model_answer）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    refs = load_references(args.references)

    if args.selftest:
        n_ok, n_fail, failures = run_selftests(refs, args.verbose)
        print(f"claim selftests: {n_ok} passed, {n_fail} failed")
        for t, c, msg in failures:
            print(f"  FAIL {t}/{c}: {msg}")
        raise SystemExit(1 if n_fail else 0)

    if args.arms_csv:
        import pandas as pd
        df = pd.read_csv(args.arms_csv)
        for (task, model), sub in df.groupby(["task_id", "model"]):
            ref = refs.get(task)
            if ref is None:
                continue
            texts = dict(zip(sub["facet"], sub["model_answer"]))
            for f in verify_entry(ref, texts):
                print(f"{task} | {model} | {f.facet_id} | {f.kind} | {f.rule_id} | {f.detail}")


if __name__ == "__main__":
    main()
