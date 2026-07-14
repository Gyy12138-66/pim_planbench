#!/usr/bin/env python3
"""冻结评分器（scripts/score_3modeloutput_v03.py）的参数化镜像（修订项 #2 专用）。

冻结评分器只被 import，绝不修改。镜像的可信度由守卫断言保证：
默认常数下逐行复现冻结评分器的 raw 分与 capped 分（verify_against_frozen），
不等即中止——这条是 cap 开/关与 Eq.5 敏感性两项分析可信度的根。

结构：build_features 先把与常数无关的行级特征一次性抽出（线索覆盖率、
参考匹配率、长度、PF/VFR 门控布尔、外部 cap 上限），score_from_features
再做纯算术打分——200 次联合扰动不必重复正则匹配。

Eq.5 常数（评审 PdEo 点名"unexplained with no ablation"）即 DEFAULT_PARAMS
的 9 个数值；门槛阈值（220/450/350 字长、0.55/0.72 等）与 facet 规则逻辑
视为规则结构，不在 Eq.5 常数扰动范围内（联合扰动一并覆盖 9 常数）。
"""
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN_PATH = ROOT / "scripts" / "score_3modeloutput_v03.py"
PANEL_SCORED = ROOT / "scores" / "pilot_v0.3" / "ModelOutput_all_existing_scored_v0.3.csv"


def load_frozen():
    spec = importlib.util.spec_from_file_location("score_v03_frozen", FROZEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FROZEN = load_frozen()

DEFAULT_PARAMS = {
    "BASE": 1.0,      # 基分
    "W_SPEC": 2.2,    # specificity（参考项匹配率）权重
    "W_CORE": 1.25,   # core cue 覆盖权重
    "CORE_NORM": 0.45,  # core 覆盖归一化分母
    "LEN_B1": 0.35,   # 长度加分（≥220 字符）
    "LEN_B2": 0.25,   # 长度加分（≥450 字符）
    "MISS_B": 0.20,   # missing 信息处理加分
    "DET_B1": 0.25,   # 细节加分档 1（spec≥0.55 & core≥0.35 & len≥350）
    "DET_B2": 0.35,   # 细节加分档 2（spec≥0.72 & core≥0.45 & len≥450）
}

# ---- 以下门控词表逐条转录自冻结 raw_score()（正确性由守卫断言背书） ----

_PF_GOVERNING = ["pde", "equation", "governing", "system"]
_PF_KNOWN = ["known", "given", "prescribed", "available", "user input"]
_PF_TARGET = ["unknown", "target", "output", "approximate", "solve", "estimate",
              "infer", "recover", "identify"]
_PF_DOMAIN = ["domain", "omega", "boundary", "geometry", "x", "t", "field", "coordinates"]
_PF_TASK_TYPE = ["forward", "inverse", "data assimilation", "sparse", "observation",
                 "sensor", "surrogate", "operator", "reusable", "single-instance",
                 "single instance", "boundary-value", "initial-boundary", "solve",
                 "recover", "infer", "estimate"]
_PF_HANDLES_MISSING = ["missing", "unspecified", "not specified", "not provided",
                       "not explicitly", "must be specified", "must be supplied",
                       "must be provided", "requires", "need to specify", "user input",
                       "if available", "if specified"]
_PF_NEEDS_TYPE_MARKERS = ["inverse", "recovery", "sparse", "noisy", "periodic",
                          "helmholtz", "euler", "mhd", "darcy"]
_MISS_BONUS_CUES = ["missing", "unspecified", "not specified", "must be specified",
                    "if available"]
_VFR_RISK_MARKERS = ["risk", "failure", "non-uniqueness", "overfitting", "noise",
                     "stiff", "sharp", "spectral", "drift", "shock", "instability",
                     "bias", "convergence"]
_VFR_VALIDATION_MARKERS = ["validate", "validation", "compare", "reference", "residual",
                           "error", "metric", "held-out", "cross-validation"]


def _pf_task_specific_cues(task_id: str) -> list[str]:
    cues: list[str] = []
    if "inverse" in task_id or "recovery" in task_id:
        cues.extend(["inverse", "infer", "estimate", "identify", "recover",
                     "unknown parameter", "unknown source"])
    if "sparse" in task_id or "noisy" in task_id:
        cues.extend(["sparse", "observation", "sensor", "data", "noise", "noisy"])
    if "periodic" in task_id:
        cues.extend(["periodic", "endpoint", "topology", "identified"])
    if "cahn_hilliard" in task_id:
        cues.extend(["cahn-hilliard", "chemical", "potential", "mass", "conserved"])
    if "helmholtz" in task_id:
        cues.extend(["helmholtz", "complex", "frequency", "phase", "amplitude"])
    if "euler_shock" in task_id:
        cues.extend(["euler", "conservative", "conservation", "density", "momentum",
                     "energy", "shock"])
    if "mhd" in task_id:
        cues.extend(["magnetic", "velocity", "coupled", "induction", "divergence"])
    if "multiscale_darcy" in task_id:
        cues.extend(["single-instance", "single instance", "surrogate", "operator",
                     "high-contrast", "permeability"])
    if "acoustic" in task_id:
        cues.extend(["acoustic", "scattering", "geometry", "boundary", "frequency"])
    if "rayleigh_benard" in task_id:
        cues.extend(["rayleigh", "boussinesq", "temperature", "velocity", "pressure"])
    return cues


def build_features(row: dict[str, str], reference: dict[str, Any]) -> dict[str, Any]:
    fs = FROZEN
    facet_id = row["facet_id"] or fs.FACET_IDS[row["facet"]]
    answer = fs.norm(row["model_answer"])
    f: dict[str, Any] = {"task_id": row["task_id"], "model": row["model"],
                         "facet_id": facet_id, "empty": not answer,
                         "cap_min": None, "cap_reasons": []}
    if not answer:
        return f

    f["core"] = fs.cue_ratio(answer, fs.FACET_CORE_CUES[facet_id])
    spec, matched, total = fs.specificity_ratio(answer, reference, facet_id)
    f["spec"] = spec
    f["length"] = len(answer)
    f["miss_bonus"] = fs.contains_any(answer, _MISS_BONUS_CUES)

    if facet_id == "problem_formalization":
        task_id = row["task_id"]
        f["pf_governing"] = fs.contains_any(answer, _PF_GOVERNING)
        f["pf_known"] = fs.contains_any(answer, _PF_KNOWN)
        f["pf_target"] = fs.contains_any(answer, _PF_TARGET)
        f["pf_domain"] = fs.contains_any(answer, _PF_DOMAIN)
        f["pf_task_type"] = fs.contains_any(answer, _PF_TASK_TYPE)
        f["pf_handles_missing"] = fs.contains_any(answer, _PF_HANDLES_MISSING)
        cues = _pf_task_specific_cues(task_id)
        f["pf_task_specific_ok"] = not cues or fs.contains_any(answer, cues)
        f["pf_needs_type"] = any(m in task_id for m in _PF_NEEDS_TYPE_MARKERS)

    if facet_id == "validation_failure_risks":
        f["vfr_risk_count"] = sum(1 for cue in _VFR_RISK_MARKERS if cue in answer)
        f["vfr_val_plan"] = fs.contains_any(answer, _VFR_VALIDATION_MARKERS)

    caps: list[tuple[int, str]] = []
    g_cap, g_reason = fs.generic_cap(answer, facet_id)
    if g_cap is not None:
        caps.append((g_cap, g_reason or "generic cap"))
    caps.extend(fs.hard_trap_caps(row["task_id"], facet_id, answer))
    if caps:
        f["cap_min"] = min(c for c, _ in caps)
        f["cap_reasons"] = [r for _, r in caps]
    return f


def score_from_features(f: dict[str, Any], params: dict[str, float] = DEFAULT_PARAMS,
                        pf_strict_caps: bool = True, external_caps: bool = True) -> int:
    if f["empty"]:
        return 0
    p = params
    s = p["BASE"]
    s += min(p["W_SPEC"], p["W_SPEC"] * f["spec"])
    s += min(p["W_CORE"], p["W_CORE"] * (f["core"] / p["CORE_NORM"]))
    if f["length"] >= 220:
        s += p["LEN_B1"]
    if f["length"] >= 450:
        s += p["LEN_B2"]
    if f["miss_bonus"]:
        s += p["MISS_B"]
    if f["spec"] >= 0.55 and f["core"] >= 0.35 and f["length"] >= 350:
        s += p["DET_B1"]
    if f["spec"] >= 0.72 and f["core"] >= 0.45 and f["length"] >= 450:
        s += p["DET_B2"]
    score = max(0, min(5, int(round(s))))

    if f["facet_id"] == "problem_formalization":
        has_split = f["pf_known"] and f["pf_target"]
        if f["pf_governing"] and f["pf_known"] and f["pf_domain"] and f["length"] >= 250:
            score = max(score, 4)
        qualifies_for_5 = (has_split and f["pf_task_type"] and f["pf_handles_missing"]
                           and f["pf_task_specific_ok"] and f["spec"] >= 0.70
                           and f["length"] >= 350)
        if qualifies_for_5:
            score = max(score, 5)
        elif pf_strict_caps and score > 4:
            score = 4
        if pf_strict_caps:
            if f["pf_needs_type"] and not f["pf_task_type"] and score > 3:
                score = 3
            if not has_split and score > 4:
                score = 4

    if f["facet_id"] == "validation_failure_risks":
        if f["vfr_risk_count"] >= 3 and f["length"] >= 250:
            score = max(score, 3)
        if f["vfr_risk_count"] >= 3 and f["vfr_val_plan"] and f["spec"] >= 0.30:
            score = max(score, 4)
        if (f["vfr_risk_count"] >= 4 and f["vfr_val_plan"] and f["spec"] >= 0.55
                and f["length"] >= 450):
            score = max(score, 5)

    if external_caps and f["cap_min"] is not None and score > f["cap_min"]:
        score = f["cap_min"]
    return score


def load_references() -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in FROZEN.read_jsonl(FROZEN.REFERENCES_PATH)}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def verify_against_frozen(rows: list[dict[str, str]],
                          references: dict[str, dict[str, Any]]) -> int:
    """守卫断言：镜像默认参数逐行复现冻结评分器；有存量 score 列时一并核对。"""
    for row in rows:
        ref = references[row["task_id"]]
        raw, _ = FROZEN.raw_score(row, ref)
        capped, _ = FROZEN.apply_caps(raw, row, FROZEN.norm(row["model_answer"]))
        f = build_features(row, ref)
        m_raw = score_from_features(f, external_caps=False)
        m_cap = score_from_features(f)
        if m_raw != raw or m_cap != capped:
            raise SystemExit(
                f"镜像漂移: {row['task_id']} / {row['model']} / {f['facet_id']} "
                f"frozen=({raw},{capped}) mirror=({m_raw},{m_cap})")
        stored = row.get("score", "")
        if stored != "" and int(float(stored)) != capped:
            raise SystemExit(
                f"存量 CSV 与冻结评分器不一致: {row['task_id']} / {row['model']} / "
                f"{f['facet_id']} stored={stored} recomputed={capped}")
    return len(rows)


def kendall_tau(x: dict[str, float], y: dict[str, float]) -> float:
    """Kendall tau-b（并列校正：自身对自身 = 1.0），键集合须一致。"""
    keys = sorted(x)
    conc = disc = tie_x = tie_y = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            dx = x[keys[i]] - x[keys[j]]
            dy = y[keys[i]] - y[keys[j]]
            if dx == 0:
                tie_x += 1
            if dy == 0:
                tie_y += 1
            if dx * dy > 0:
                conc += 1
            elif dx * dy < 0:
                disc += 1
    n0 = len(keys) * (len(keys) - 1) / 2
    denom = ((n0 - tie_x) * (n0 - tie_y)) ** 0.5
    return (conc - disc) / denom if denom else 1.0


def strict_inversions(x: dict[str, float], y: dict[str, float]) -> int:
    """x 中严格有序的对在 y 中反转的数目（并列对脱离并列不计为逆序）。"""
    keys = sorted(x)
    inv = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if (x[keys[i]] - x[keys[j]]) * (y[keys[i]] - y[keys[j]]) < 0:
                inv += 1
    return inv
