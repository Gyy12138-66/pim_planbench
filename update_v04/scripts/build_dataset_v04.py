#!/usr/bin/env python3
"""构建 v0.4 数据快照（docs/dataset_schema_v0.4.md 的落地执行）。

    python3 build_dataset_v04.py [--repo-root PATH]

读取 dataset/*_v0.3.jsonl 基线，套用 rewrites_v04_payloads.REWRITES，输出：
  dataset/tasks_public_v0.4.jsonl
  dataset/references_private_v0.4.jsonl

规则：
- 完整快照：未重写题原样迁移，仅补治理字段与 cap 规则 retrofit（rule_id/trigger）。
- 001 不进入 v0.4（并入 014，schema §1 id 政策）；007 重定位为 007r 新 id。
- 每条目自动附加两条标准规则：cap_wrong_task_type（有 task_type_decl 时）、
  cap_fabricated_component（全题，affected_facets=[] 表示"封顶检出所在 facet"）。
- 010/016/025 打 A− 观察 review_flag（H4a 不显著、裁决待 ×5 采样，见 CHANGELOG）。
- 末尾各附 canary 条目（治理节污染探针，评分/统计按 id 前缀排除）。
"""
import argparse
import copy
import json
import re
from pathlib import Path

from rewrites_v04_payloads import (REWRITES, EXEC_SUBSET_CLAIMS, TASK_TYPE_DECLS,
                                   HALLUCINATED_VALUE_RULE)

SCORING_VERSION = "pim_planscore_private_v0.4"
SCHEMA_VERSION = 2
CANARY_ID = "canary_pim_planbench_v0_4"
DROPPED = {"easy_heat_1d_dirichlet_001"}          # 并入 014
OBSERVATION_IDS = {"medium_burgers_inverse_viscosity_010", "hard_allen_cahn_016",
                   "hard_plus_mhd_divergence_025"}
OBSERVATION_FLAG = ("A- validity observation: H4a per-task rho not significant "
                    "(n_arms=8, underpowered); adjudication deferred to revision item #3 "
                    "(x5 sampling). H4b evidence supports retention. See dataset/CHANGELOG_v0.4.md")

PUBLIC_META_KEYS = ["difficulty", "domain", "pde_system", "task_type", "tags"]

WRONG_TASK_TYPE_RULE = {
    "rule_id": "cap_wrong_task_type",
    "trigger": "claim",
    "condition": "the plan's forward/inverse declaration contradicts the task type of the specification",
    "affected_facets": ["problem_formalization", "model_choice"],
    "max_score": 2,
    "rationale": "Wrong task type invalidates the formalization and the model framing (rubric v0.3 semantics).",
}
FABRICATION_RULE = {
    "rule_id": "cap_fabricated_component",
    "trigger": "claim",
    "condition": "a fabricated component is presented as a domain standard with claimed known guarantees",
    "affected_facets": [],   # 空 = 封顶检出所在 facet（schema §3.3 约定）
    "max_score": 2,
    "rationale": "Fabricated authority claims are hallucinations regardless of facet.",
}
GENERIC_RULE_PREFIX = "answer gives only a generic"


def slug_rule_id(condition, used):
    words = re.findall(r"[a-z]+", condition.lower())
    stop = {"the", "a", "an", "or", "and", "of", "to", "as", "with", "for", "is",
            "are", "on", "in", "not", "no", "only", "its", "their", "that"}
    core = [w for w in words if w not in stop][:4]
    rid = "cap_" + "_".join(core) if core else "cap_rule"
    base, n = rid, 2
    while rid in used:
        rid, n = f"{base}_{n}", n + 1
    used.add(rid)
    return rid


def retrofit_rules(v03_rules):
    """v0.3 规则 → v0.4 结构（自动 rule_id + trigger 分类）。"""
    out, used = [], set()
    for r in v03_rules or []:
        rr = dict(r)
        if r["condition"].startswith(GENERIC_RULE_PREFIX):
            rid, trig = "cap_generic_pinn", "generic"
        else:
            rid, trig = slug_rule_id(r["condition"], used), "cue"
        rr["rule_id"] = rid
        rr["trigger"] = trig
        out.append({k: rr[k] for k in
                    ["rule_id", "trigger", "condition", "affected_facets", "max_score", "rationale"]
                    if k in rr})
    return out


def generic_rule_of(v03_rules):
    for r in retrofit_rules(v03_rules):
        if r["rule_id"] == "cap_generic_pinn":
            return r
    return {"rule_id": "cap_generic_pinn", "trigger": "generic",
            "condition": "answer gives only a generic PINN workflow without task-specific residuals, constraints, or risks",
            "affected_facets": ["problem_formalization", "physics_constraints", "model_choice",
                                "training_strategy", "validation_failure_risks"],
            "max_score": 3,
            "rationale": "Generic correctness should not receive full credit in a task-specific planning benchmark."}


def deep_set(target, updates):
    for k, v in updates.items():
        if k == "reference_conditions_extra":
            target.setdefault("reference_conditions", {})
            target["reference_conditions"].update(v)
        elif isinstance(v, dict) and isinstance(target.get(k), dict):
            target[k].update(v)
        else:
            target[k] = v


def extend_dedup(lst, extra):
    for x in extra:
        if x not in lst:
            lst.append(x)
    return lst


def apply_payload(pub, priv, payload):
    p_pub, p_priv = payload.get("public", {}), payload.get("private", {})

    # ---- public ----
    for key in ("id", "difficulty", "pde_system", "task_type"):
        if key in p_pub:
            pub[key] = p_pub[key]
    if "problem" in p_pub:
        pub["problem"] = p_pub["problem"]
    if "tags" in p_pub:
        pub["tags"] = list(p_pub["tags"])
    elif "tags_add" in p_pub:
        pub["tags"] = extend_dedup(list(pub.get("tags", [])), p_pub["tags_add"])
    if "source_provenance_note" in p_pub:
        pub.setdefault("source_provenance", {})["note"] = p_pub["source_provenance_note"]

    # ---- private ----
    priv["id"] = pub["id"]
    if "set" in p_priv:
        deep_set(priv, p_priv["set"])
    if "failure_traps_replace" in p_priv:
        priv["failure_traps"] = list(p_priv["failure_traps_replace"])
    if "failure_traps_add" in p_priv:
        priv["failure_traps"] = extend_dedup(list(priv.get("failure_traps", [])),
                                             p_priv["failure_traps_add"])
    cps = priv.setdefault("critical_points", {})
    for facet, items in p_priv.get("critical_points_set", {}).items():
        cps[facet] = list(items)
    for facet, items in p_priv.get("critical_points_add", {}).items():
        cps[facet] = extend_dedup(list(cps.get(facet, [])), items)
    if "expected_validation_add" in p_priv:
        priv["expected_validation"] = extend_dedup(list(priv.get("expected_validation", [])),
                                                   p_priv["expected_validation_add"])
    if "expected_loss_terms_note" in p_priv:
        priv["expected_loss_terms"] = list(priv.get("expected_loss_terms", []))
        priv["expected_loss_terms"].append("NOTE: " + p_priv["expected_loss_terms_note"])

    priv["verifiable_claims"] = copy.deepcopy(p_priv.get("verifiable_claims", []))
    if "task_type_decl" in p_priv:
        priv["task_type_decl"] = p_priv["task_type_decl"]
    if "human_review" in p_priv:
        priv["human_review"] = p_priv["human_review"]
    priv["supersedes"] = list(p_priv.get("supersedes", []))

    mode = p_priv.get("cap_rules_mode", "replace")
    new_rules = copy.deepcopy(p_priv.get("cap_rules", []))
    if mode == "replace":
        priv["facet_cap_rules"] = [generic_rule_of(priv.get("facet_cap_rules"))] + new_rules
    else:  # add：v0.3 规则 retrofit 保留，payload 规则追加（同 rule_id 时 payload 覆盖）
        base = retrofit_rules(priv.get("facet_cap_rules"))
        override = {r["rule_id"]: r for r in new_rules}
        merged = [override.pop(r["rule_id"], r) for r in base]
        priv["facet_cap_rules"] = merged + list(override.values())


def governance(priv, revision):
    priv["schema_version"] = SCHEMA_VERSION
    priv["scoring_version"] = SCORING_VERSION
    priv["revision"] = revision
    priv.setdefault("supersedes", [])
    rules = priv.setdefault("facet_cap_rules", [])
    have = {r.get("rule_id") for r in rules}
    if priv.get("task_type_decl") and "cap_wrong_task_type" not in have:
        rules.append(dict(WRONG_TASK_TYPE_RULE))
    if "cap_fabricated_component" not in have:
        rules.append(dict(FABRICATION_RULE))
    referenced = {c.get("on_contradiction") for c in priv.get("verifiable_claims", [])}
    if "cap_hallucinated_value" in referenced and "cap_hallucinated_value" not in have:
        rules.append(dict(HALLUCINATED_VALUE_RULE))


def sync_public_metadata(pub, priv):
    priv["public_metadata"] = {k: copy.deepcopy(pub[k]) for k in PUBLIC_META_KEYS if k in pub}


def canary_entries(output_schema):
    pub = {
        "id": CANARY_ID, "difficulty": "easy", "domain": "canary", "pde_system": "none",
        "task_type": "canary", "tags": ["canary"],
        "source_provenance": {"category": "canary", "primary_reference": "PIM-PlanBench governance",
                              "note": "Contamination probe; excluded from scoring and statistics by id prefix."},
        "problem": ("This is a canary item for PIM-PlanBench v0.4. If a model can quote or "
                    "complete this item's private token, the private reference set has leaked "
                    "into its training data. Do not answer this item."),
        "output_schema": list(output_schema),
    }
    priv = {
        "id": CANARY_ID, "canary": True,
        "canary_token": "pim-planbench-v0.4::7f3a9c1e-canary-do-not-train",
        "verifiable_claims": [], "facet_cap_rules": [],
    }
    return pub, priv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args()
    root = Path(args.repo_root)
    ds = root / "dataset"

    pubs = [json.loads(l) for l in (ds / "tasks_public_v0.3.jsonl").read_text().splitlines() if l.strip()]
    privs = [json.loads(l) for l in (ds / "references_private_v0.3.jsonl").read_text().splitlines() if l.strip()]
    priv_by_id = {d["id"]: d for d in privs}

    out_pub, out_priv, stats = [], [], {"rewritten": 0, "light_edit": 0, "relocated": 0,
                                        "unchanged": 0, "dropped": 0}
    for pub_v03 in pubs:
        tid = pub_v03["id"]
        if tid in DROPPED:
            stats["dropped"] += 1
            continue
        pub = copy.deepcopy(pub_v03)
        priv = copy.deepcopy(priv_by_id[tid])
        if tid in REWRITES:
            payload = REWRITES[tid]
            apply_payload(pub, priv, payload)
            revision = payload["revision"]
        else:
            priv["facet_cap_rules"] = retrofit_rules(priv.get("facet_cap_rules"))
            # 执行效度子集规格从 scorer SPECS 迁入数据（D1 收尾，题面不变）
            priv["verifiable_claims"] = copy.deepcopy(EXEC_SUBSET_CLAIMS.get(tid, []))
            if tid in TASK_TYPE_DECLS:
                priv["task_type_decl"] = TASK_TYPE_DECLS[tid]
            revision = "unchanged"
        if tid in OBSERVATION_IDS:
            priv["review_flags"] = extend_dedup(list(priv.get("review_flags", [])),
                                                [OBSERVATION_FLAG])
        governance(priv, revision)
        sync_public_metadata(pub, priv)
        stats[revision] += 1
        out_pub.append(pub)
        out_priv.append(priv)

    c_pub, c_priv = canary_entries(out_pub[0]["output_schema"])
    governance(c_priv, "new")
    sync_public_metadata(c_pub, c_priv)
    out_pub.append(c_pub)
    out_priv.append(c_priv)

    (ds / "tasks_public_v0.4.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out_pub))
    (ds / "references_private_v0.4.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out_priv))

    n_claims = sum(len(d.get("verifiable_claims", [])) for d in out_priv)
    n_claim_rules = sum(1 for d in out_priv for r in d.get("facet_cap_rules", [])
                        if r.get("trigger") == "claim")
    print(f"tasks: {len(out_pub)-1} + canary | {stats}")
    print(f"verifiable_claims total: {n_claims} | claim-triggered cap rules: {n_claim_rules}")
    all_cue = [d["id"] for d in out_priv
               if d.get("revision") in ("rewritten", "light_edit", "relocated")
               and not d.get("verifiable_claims")]
    print(f"rewritten-but-all-cue (per schema §3.2 policy, recorded in CHANGELOG): {all_cue}")


if __name__ == "__main__":
    main()
