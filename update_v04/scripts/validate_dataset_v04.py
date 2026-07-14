#!/usr/bin/env python3
"""v0.4 数据快照校验（docs/dataset_schema_v0.4.md §6 的机械检查 + claim 自测）。

    python3 validate_dataset_v04.py [--repo-root PATH]

全部检查通过 → exit 0；任何一项失败 → 列出并 exit 1。
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scorer_v04"))
from claim_verifier_v04 import FACET_DISPLAY, FACET_ORDER, load_references, run_selftests  # noqa: E402

PUBLIC_FIELDS = {"id", "difficulty", "domain", "pde_system", "task_type", "tags",
                 "source_provenance", "problem", "output_schema"}
PRIVATE_ONLY_FIELDS = {"parameter_values", "reference_conditions", "analytic_solution",
                       "failure_traps", "facet_cap_rules", "verifiable_claims",
                       "critical_points", "canonical_pde", "human_review"}
CANONICAL_OUTPUT_SCHEMA = [FACET_DISPLAY[f] for f in FACET_ORDER]
REVISIONS = {"rewritten", "light_edit", "relocated", "new", "unchanged"}
CLAIM_TYPES = {"param_value", "asserted_known_unknown", "sign_relation",
               "arithmetic_consistency", "co_occurrence", "claim_without_support",
               "forbidden_assertion"}
TRIGGERS = {"claim", "cue", "generic"}
# 由 verifier 内建检查触发、无需 claim 显式引用的标准规则
IMPLICIT_CLAIM_RULES = {"cap_wrong_task_type", "cap_fabricated_component"}
CANARY_PREFIX = "canary_"

errors = []


def err(msg):
    errors.append(msg)


def check_regex(tid, cid, pat, want_groups, label):
    try:
        c = re.compile(pat)
    except re.error as e:
        err(f"{tid}/{cid}: {label} 正则无法编译: {e} :: {pat}")
        return
    if want_groups is not None and c.groups != want_groups:
        err(f"{tid}/{cid}: {label} 捕获组数 {c.groups} != {want_groups} :: {pat}")


def check_claim(tid, claim, rule_ids):
    cid = claim.get("claim_id", "<no-id>")
    ctype = claim.get("type")
    if ctype not in CLAIM_TYPES:
        err(f"{tid}/{cid}: 未知 claim 类型 {ctype}")
        return
    if claim.get("basis") not in ("spec", "plan_internal"):
        err(f"{tid}/{cid}: basis 缺失或非法")
    for f in claim.get("facets", []):
        if f not in FACET_DISPLAY:
            err(f"{tid}/{cid}: 非法 facet 引用 {f}")
    if not claim.get("facets"):
        err(f"{tid}/{cid}: facets 为空")
    oc = claim.get("on_contradiction")
    if oc not in rule_ids:
        err(f"{tid}/{cid}: on_contradiction 指向不存在的规则 {oc}")
    st = claim.get("selftest")
    if not (isinstance(st, dict) and st.get("gold") and st.get("tamper")):
        err(f"{tid}/{cid}: selftest.gold/tamper 缺失")

    if ctype == "param_value":
        for p in claim["patterns"]:
            check_regex(tid, cid, p, 1, "patterns")
        if not isinstance(claim.get("true_value"), (int, float)):
            err(f"{tid}/{cid}: true_value 缺失")
    elif ctype == "asserted_known_unknown":
        for p in claim["patterns"]:
            check_regex(tid, cid, p, None, "patterns")
    elif ctype == "sign_relation":
        for p in claim["sign_patterns"]:
            check_regex(tid, cid, p, 2, "sign_patterns")
        if claim.get("canonical") not in ("+", "-"):
            err(f"{tid}/{cid}: canonical 必须为 '+'/'-'")
    elif ctype == "arithmetic_consistency":
        names = set(claim["quantities"])
        for name, pats in claim["quantities"].items():
            for p in pats:
                check_regex(tid, cid, p, 1, f"quantities[{name}]")
        expr_names = set(re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*", claim["expression"]))
        unknown = expr_names - names - {"abs", "min", "max", "and", "or", "not"}
        if unknown:
            err(f"{tid}/{cid}: expression 引用未定义量 {unknown}")
    elif ctype == "co_occurrence":
        check_regex(tid, cid, claim["pattern_a"], None, "pattern_a")
        check_regex(tid, cid, claim["pattern_b"], None, "pattern_b")
    elif ctype == "claim_without_support":
        check_regex(tid, cid, claim["pattern"], None, "pattern")
        if not claim.get("support_patterns"):
            err(f"{tid}/{cid}: support_patterns 为空")
        for p in claim["support_patterns"]:
            check_regex(tid, cid, p, None, "support_patterns")
    elif ctype == "forbidden_assertion":
        for p in claim["patterns"]:
            check_regex(tid, cid, p, None, "patterns")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(HERE.parents[1]))
    args = ap.parse_args()
    root = Path(args.repo_root)
    ds = root / "dataset"

    pubs = [json.loads(l) for l in (ds / "tasks_public_v0.4.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    privs = [json.loads(l) for l in (ds / "references_private_v0.4.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    v03_ids = {json.loads(l)["id"] for l in (ds / "references_private_v0.3.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    pub_by_id = {d["id"]: d for d in pubs}
    priv_by_id = {d["id"]: d for d in privs}

    # 1. 两文件 id 集合一致
    if set(pub_by_id) != set(priv_by_id):
        err(f"id 集合不一致: 仅公开 {set(pub_by_id)-set(priv_by_id)}, 仅私有 {set(priv_by_id)-set(pub_by_id)}")

    all_new_ids = set(pub_by_id)
    for pub in pubs:
        tid = pub["id"]
        if tid.startswith(CANARY_PREFIX):
            continue
        # 2. 公开字段集合 = v0.3 schema；不含私有字段
        extra = set(pub) - PUBLIC_FIELDS
        missing = PUBLIC_FIELDS - set(pub)
        if extra:
            err(f"{tid}: 公开条目多出字段 {extra}")
        if missing:
            err(f"{tid}: 公开条目缺字段 {missing}")
        leaked = set(pub) & PRIVATE_ONLY_FIELDS
        if leaked:
            err(f"{tid}: 公开条目泄漏私有字段 {leaked}")
        # 3. output_schema 逐字一致
        if pub.get("output_schema") != CANONICAL_OUTPUT_SCHEMA:
            err(f"{tid}: output_schema 与规范显示名不一致: {pub.get('output_schema')}")

    for priv in privs:
        tid = priv["id"]
        is_canary = tid.startswith(CANARY_PREFIX)
        # 4. 治理字段
        if priv.get("schema_version") != 2:
            err(f"{tid}: schema_version != 2")
        if priv.get("scoring_version") != "pim_planscore_private_v0.4":
            err(f"{tid}: scoring_version 错误")
        if priv.get("revision") not in REVISIONS:
            err(f"{tid}: revision 非法: {priv.get('revision')}")
        # 5. supersedes 引用存在于 v0.3 且不存在于 v0.4
        for old in priv.get("supersedes", []):
            if old not in v03_ids:
                err(f"{tid}: supersedes 引用不存在于 v0.3: {old}")
            if old in all_new_ids:
                err(f"{tid}: supersedes 的 {old} 仍存在于 v0.4")
        # 6. public_metadata 与公开条目同步
        pub = pub_by_id.get(tid)
        if pub:
            for k, v in (priv.get("public_metadata") or {}).items():
                if pub.get(k) != v:
                    err(f"{tid}: public_metadata.{k} 与公开条目不同步")
        if is_canary:
            continue
        # 7. cap 规则结构
        rules = priv.get("facet_cap_rules", [])
        rule_ids = set()
        for r in rules:
            rid = r.get("rule_id")
            if not rid or rid in rule_ids:
                err(f"{tid}: rule_id 缺失或重复: {rid}")
            rule_ids.add(rid)
            if r.get("trigger") not in TRIGGERS:
                err(f"{tid}/{rid}: trigger 非法: {r.get('trigger')}")
            for f in r.get("affected_facets", []):
                if f not in FACET_DISPLAY:
                    err(f"{tid}/{rid}: 非法 facet 引用 {f}")
            if not isinstance(r.get("max_score"), int):
                err(f"{tid}/{rid}: max_score 缺失")
        # 8. claims 结构 + 引用闭合
        claims = priv.get("verifiable_claims", [])
        seen_cids = set()
        for c in claims:
            if c.get("claim_id") in seen_cids:
                err(f"{tid}: claim_id 重复 {c.get('claim_id')}")
            seen_cids.add(c.get("claim_id"))
            check_claim(tid, c, rule_ids)
        referenced = {c.get("on_contradiction") for c in claims}
        if priv.get("task_type_decl"):
            referenced.add("cap_wrong_task_type")
        referenced.add("cap_fabricated_component")
        for r in rules:
            if r.get("trigger") == "claim" and r["rule_id"] not in referenced \
                    and r["rule_id"] not in IMPLICIT_CLAIM_RULES:
                err(f"{tid}: trigger='claim' 规则 {r['rule_id']} 未被任何 claim 引用")

    # 9. CHANGELOG 逐题一致（| id | revision | 表行）
    chlog = ds / "CHANGELOG_v0.4.md"
    if not chlog.exists():
        err("dataset/CHANGELOG_v0.4.md 缺失")
    else:
        rows = dict(re.findall(r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*([a-z_]+)\s*\|",
                               chlog.read_text(encoding="utf-8"), re.MULTILINE))
        for priv in privs:
            tid = priv["id"]
            if tid.startswith(CANARY_PREFIX):
                continue
            if tid not in rows:
                err(f"CHANGELOG 缺少 {tid} 行")
            elif rows[tid] != priv["revision"]:
                err(f"CHANGELOG {tid}: {rows[tid]} != revision {priv['revision']}")
        for old in v03_ids - all_new_ids:
            if old not in rows:
                err(f"CHANGELOG 缺少被移除条目 {old} 的记录行")

    # 10. claim 自测（金零误伤 / 篡改必检出）
    refs = load_references(ds / "references_private_v0.4.jsonl")
    n_ok, n_fail, failures = run_selftests(refs)
    for t, c, msg in failures:
        err(f"selftest {t}/{c}: {msg}")

    n_claims = sum(len(p.get("verifiable_claims", [])) for p in privs)
    print(f"checked: {len(pubs)} tasks | {n_claims} claims | selftests {n_ok} ok / {n_fail} fail")
    if errors:
        print(f"\nFAIL — {len(errors)} 项:")
        for e in errors:
            print("  ✗", e)
        raise SystemExit(1)
    print("PASS — schema §6 全部检查通过")


if __name__ == "__main__":
    main()
