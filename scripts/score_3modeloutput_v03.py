#!/usr/bin/env python3
"""Create a rubric-assisted score file for scores/pilot_v0.3/3ModelOutput.csv.

This is a deterministic first-pass scorer. It is intended for screening,
visualization, and audit preparation; final paper numbers should still be
reviewed or adjudicated on a representative subset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "scores/pilot_v0.3/3ModelOutput.csv"
DEFAULT_OUTPUT = ROOT / "scores/pilot_v0.3/3ModelOutput_scored.csv"
DEFAULT_SUMMARY = ROOT / "scores/pilot_v0.3/score_summary_by_model.csv"
DEFAULT_TASK_SUMMARY = ROOT / "scores/pilot_v0.3/score_summary_by_task_model.csv"
REFERENCES_PATH = ROOT / "dataset/references_private_v0.3.jsonl"

FACET_IDS = {
    "Problem Formalization": "problem_formalization",
    "Physics Constraints": "physics_constraints",
    "Model Choice": "model_choice",
    "Training Strategy": "training_strategy",
    "Validation Failure Risks": "validation_failure_risks",
}

FACET_CORE_CUES = {
    "problem_formalization": [
        "unknown",
        "known",
        "domain",
        "objective",
        "field",
        "variable",
        "parameter",
        "forward",
        "inverse",
        "missing",
        "given",
        "governing",
        "pde",
        "equation",
        "prescribed",
        "source",
        "sensor",
        "observation",
        "input",
    ],
    "physics_constraints": [
        "pde",
        "residual",
        "equation",
        "constraint",
        "condition",
        "boundary",
        "initial",
        "conservation",
        "periodic",
        "flux",
        "divergence",
        "positive",
        "regularity",
        "weak",
        "strong",
        "observation",
        "data",
    ],
    "model_choice": [
        "pinn",
        "physics-informed",
        "network",
        "architecture",
        "input",
        "output",
        "fourier",
        "siren",
        "operator",
        "domain decomposition",
        "weak",
        "because",
        "justif",
    ],
    "training_strategy": [
        "loss",
        "residual",
        "sample",
        "sampling",
        "collocation",
        "optimizer",
        "adam",
        "l-bfgs",
        "weight",
        "adaptive",
        "normalize",
        "curriculum",
        "regularization",
        "gradient",
        "early stopping",
    ],
    "validation_failure_risks": [
        "validation",
        "validate",
        "risk",
        "failure",
        "error",
        "residual",
        "compare",
        "reference",
        "conservation",
        "boundary",
        "stability",
        "identifiability",
        "non-uniqueness",
        "overfitting",
        "noise",
        "stiff",
        "sharp",
        "spectral",
        "drift",
        "shock",
        "bias",
        "convergence",
    ],
}

STOPWORDS = {
    "about",
    "across",
    "after",
    "against",
    "also",
    "and",
    "another",
    "because",
    "been",
    "being",
    "between",
    "both",
    "cannot",
    "central",
    "check",
    "correctly",
    "data",
    "does",
    "each",
    "enforce",
    "enforces",
    "equation",
    "error",
    "expected",
    "field",
    "from",
    "gives",
    "includes",
    "input",
    "into",
    "loss",
    "main",
    "model",
    "must",
    "only",
    "output",
    "points",
    "problem",
    "reference",
    "required",
    "requires",
    "residual",
    "sample",
    "score",
    "solution",
    "states",
    "such",
    "task",
    "than",
    "that",
    "their",
    "these",
    "this",
    "through",
    "uses",
    "using",
    "when",
    "where",
    "with",
    "without",
}

SYNONYMS = {
    "admissibility": ["admissibility", "admissible", "entropy"],
    "allen-cahn": ["allen-cahn", "allen cahn"],
    "boundary": ["boundary", "bc", "dirichlet", "neumann", "periodic"],
    "cahn-hilliard": ["cahn-hilliard", "cahn hilliard"],
    "chemical": ["chemical", "mu", "μ", "potential"],
    "complex": ["complex", "real", "imag", "imaginary", "phase"],
    "conservative": ["conservative", "conservation", "divergence form"],
    "darcy": ["darcy", "hydraulic", "permeability", "head"],
    "derivative": ["derivative", "gradient", "u_x", "u x", "ux", "partial", "c 1", "c1", "c^1", "flux"],
    "divergence": ["divergence", "divergence-free", "solenoidal", "∇·b", "nabla"],
    "energy": ["energy", "free energy", "dissipation"],
    "euler": ["euler", "mass", "momentum", "energy", "shock"],
    "flux": ["flux", "normal flux", "mass balance"],
    "fourth": ["fourth", "4th", "second-order", "second order", "split", "mixed"],
    "helmholtz": ["helmholtz", "frequency-domain", "frequency domain", "wavenumber"],
    "initial": ["initial", "ic", "t=0"],
    "interface": ["interface", "jump", "continuity", "facies"],
    "magnetic": ["magnetic", "mhd", "induction", "lorentz"],
    "mass": ["mass", "conservation", "conserved"],
    "periodic": ["periodic", "endpoint", "identified", "seam", "topology"],
    "positivity": ["positivity", "positive", "negative density", "negative pressure"],
    "rankine": ["rankine", "hugoniot", "jump"],
    "shock": ["shock", "front", "discontinu", "contact", "weak"],
    "surrogate": ["surrogate", "operator", "many", "realizations", "coefficient fields"],
    "weak": ["weak", "integral", "finite volume", "control-volume", "control volume"],
    "wavelength": ["wavelength", "points per wavelength", "wavenumber", "phase", "aliasing"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--task-summary", type=Path, default=DEFAULT_TASK_SUMMARY)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def norm(text: str) -> str:
    text = text.lower()
    text = text.replace("\x0c", " ")
    text = text.replace("\\n", " ")
    text = re.sub(r"[_{}$^]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, cues: list[str]) -> bool:
    return any(cue in text for cue in cues)


def token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9-]{3,}", norm(text))
        if token not in STOPWORDS and not token.replace("-", "").isdigit()
    }


def point_matched(answer: str, point: str) -> bool:
    point_norm = norm(point)
    for key, cues in SYNONYMS.items():
        if key in point_norm and contains_any(answer, cues):
            return True

    tokens = token_set(point)
    if not tokens:
        return False
    matched = sum(1 for token in tokens if token in answer)
    threshold = 0.34 if len(tokens) <= 5 else 0.28
    return matched / len(tokens) >= threshold


def reference_items(reference: dict[str, Any], facet_id: str) -> list[str]:
    points = list(reference.get("critical_points", {}).get(facet_id, []))
    if facet_id == "physics_constraints":
        points.extend(reference.get("failure_traps", []))
    elif facet_id == "model_choice":
        points.extend(reference.get("acceptable_model_choices", []))
    elif facet_id == "training_strategy":
        points.extend(reference.get("expected_loss_terms", []))
        points.extend(reference.get("expected_training_strategy", []))
    elif facet_id == "validation_failure_risks":
        points.extend(reference.get("expected_validation", []))
        points.extend(reference.get("failure_traps", []))
    return [str(point) for point in points if str(point).strip()]


def cue_ratio(answer: str, cues: list[str]) -> float:
    if not cues:
        return 0.0
    target = min(5, len(cues))
    return min(1.0, sum(1 for cue in cues if cue in answer) / target)


def specificity_ratio(answer: str, reference: dict[str, Any], facet_id: str) -> tuple[float, int, int]:
    items = reference_items(reference, facet_id)
    if not items:
        return 0.0, 0, 0
    matched = sum(1 for item in items if point_matched(answer, item))
    return matched / len(items), matched, len(items)


def generic_cap(answer: str, facet_id: str) -> tuple[int | None, str | None]:
    has_pinn = contains_any(answer, ["pinn", "physics-informed", "neural network", "network"])
    has_detail = cue_ratio(answer, FACET_CORE_CUES[facet_id]) >= 0.25
    if has_pinn and not has_detail and len(answer) < 350:
        return 3, "generic PINN/template answer with limited facet-specific detail"
    return None, None


def hard_trap_caps(task_id: str, facet_id: str, answer: str) -> list[tuple[int, str]]:
    caps: list[tuple[int, str]] = []

    if task_id == "medium_periodic_advdiff_015":
        if facet_id in {"physics_constraints", "training_strategy"} and contains_any(answer, ["dirichlet", "fixed endpoint"]):
            caps.append((2, "periodic domain treated as fixed/Dirichlet boundary"))
        if facet_id in {"physics_constraints", "training_strategy", "validation_failure_risks"}:
            if "periodic" in answer and not contains_any(answer, SYNONYMS["derivative"] + ["diffusive"]):
                caps.append((3, "mentions value periodicity but not derivative or diffusive-flux periodicity"))

    if task_id == "hard_cahn_hilliard_017":
        if facet_id in {"problem_formalization", "physics_constraints", "model_choice"} and contains_any(answer, SYNONYMS["allen-cahn"]):
            caps.append((2, "Cahn-Hilliard treated as Allen-Cahn"))
        if facet_id in {"model_choice", "training_strategy"} and not contains_any(answer, SYNONYMS["chemical"] + SYNONYMS["fourth"]):
            caps.append((3, "missing chemical-potential or fourth-order burden handling"))
        if facet_id in {"physics_constraints", "validation_failure_risks"} and not contains_any(answer, SYNONYMS["mass"]):
            caps.append((2, "missing mass conservation"))
        if facet_id == "validation_failure_risks" and not contains_any(answer, SYNONYMS["energy"] + ["long-time", "long time", "drift"]):
            caps.append((4, "missing free-energy or long-time drift validation"))

    if task_id == "hard_helmholtz_high_frequency_020":
        if facet_id in {"problem_formalization", "physics_constraints"} and contains_any(answer, ["time-domain", "time domain", "time-dependent"]):
            caps.append((2, "Helmholtz treated as time-domain wave propagation"))
        if facet_id in {"problem_formalization", "physics_constraints", "validation_failure_risks"}:
            if not contains_any(answer, SYNONYMS["complex"]):
                caps.append((3, "missing complex-valued/phase handling"))
        if facet_id in {"model_choice", "training_strategy", "validation_failure_risks"}:
            if contains_any(answer, ["fourier", "siren", "sinusoidal"]) and not contains_any(answer, SYNONYMS["complex"] + SYNONYMS["wavelength"]):
                caps.append((3, "high-frequency architecture named without complex, wavelength, or phase detail"))
        if facet_id in {"training_strategy", "validation_failure_risks"} and not contains_any(answer, SYNONYMS["wavelength"]):
            caps.append((3, "sampling/validation does not scale with wavelength or wavenumber"))

    if task_id == "hard_plus_euler_shock_023":
        if facet_id in {"problem_formalization", "physics_constraints"} and not contains_any(answer, SYNONYMS["conservative"] + SYNONYMS["euler"]):
            caps.append((2, "missing conservative variables or conservation form"))
        if facet_id in {"model_choice", "training_strategy", "validation_failure_risks"}:
            shock_aware = contains_any(answer, SYNONYMS["weak"] + SYNONYMS["rankine"] + ["conservative", "cpinn", "domain decomposition", "finite volume"])
            if not shock_aware:
                caps.append((2, "smooth strong-form PINN without weak/integral/conservative shock-aware treatment"))
        if facet_id in {"physics_constraints", "validation_failure_risks"} and not contains_any(answer, SYNONYMS["admissibility"] + SYNONYMS["positivity"]):
            caps.append((3, "missing entropy/admissibility or positivity considerations"))

    if task_id == "hard_plus_mhd_divergence_025":
        if facet_id in {"physics_constraints", "model_choice", "validation_failure_risks"} and not contains_any(answer, ["∇·b", "div b", "divergence", "solenoidal", "monopole"]):
            caps.append((2, "missing magnetic divergence control"))
        if facet_id in {"model_choice", "training_strategy", "validation_failure_risks"}:
            soft_only = contains_any(answer, ["penalty", "soft"]) and not contains_any(answer, ["potential", "projection", "stream", "divergence-free", "solenoidal", "drift"])
            if soft_only:
                caps.append((3, "only soft divergence penalty without constrained parameterization/projection/drift validation"))
        if facet_id in {"problem_formalization", "physics_constraints", "model_choice"}:
            if not contains_any(answer, SYNONYMS["magnetic"]) or not contains_any(answer, ["velocity", "fluid", "momentum"]):
                caps.append((2, "does not model coupled velocity and magnetic induction fields"))

    if task_id == "hard_plus_multiscale_darcy_026":
        if facet_id in {"problem_formalization", "model_choice", "training_strategy"} and not contains_any(answer, ["single-instance", "single instance", "surrogate", "operator", "many", "reusable"]):
            caps.append((3, "does not distinguish single solve from reusable surrogate/operator setting"))
        if facet_id in {"model_choice", "training_strategy"}:
            if contains_any(answer, ["operator", "deeponet", "fno"]) and not contains_any(answer, ["many", "realizations", "dataset", "training pairs", "generalization"]):
                caps.append((3, "neural operator suggested without many coefficient fields or generalization protocol"))
        if facet_id in {"physics_constraints", "training_strategy", "validation_failure_risks"}:
            if not contains_any(answer, ["high-contrast", "high contrast", "flux", "mass balance", "interface", "channel"]):
                caps.append((2, "ignores high-contrast coefficient effects, flux continuity, or mass balance"))
        if facet_id == "validation_failure_risks" and contains_any(answer, ["mse"]) and not contains_any(answer, ["flux", "mass balance", "coefficient", "channel"]):
            caps.append((3, "validation is only head MSE without flux/mass/coefficient robustness"))

    return caps


def raw_score(row: dict[str, str], reference: dict[str, Any]) -> tuple[int, str]:
    facet_id = row["facet_id"] or FACET_IDS[row["facet"]]
    answer = norm(row["model_answer"])
    if not answer:
        return 0, "empty or missing facet answer"

    core = cue_ratio(answer, FACET_CORE_CUES[facet_id])
    specificity, matched, total = specificity_ratio(answer, reference, facet_id)
    length = len(answer)

    score_float = 1.0
    score_float += min(2.2, 2.2 * specificity)
    score_float += min(1.25, 1.25 * (core / 0.45))
    if length >= 220:
        score_float += 0.35
    if length >= 450:
        score_float += 0.25
    if contains_any(answer, ["missing", "unspecified", "not specified", "must be specified", "if available"]):
        score_float += 0.20

    # Reward high-detail task-aware answers that mention subtle physical risks.
    if specificity >= 0.55 and core >= 0.35 and length >= 350:
        score_float += 0.25
    if specificity >= 0.72 and core >= 0.45 and length >= 450:
        score_float += 0.35

    score = max(0, min(5, int(round(score_float))))

    if facet_id == "problem_formalization":
        has_governing_setup = contains_any(answer, ["pde", "equation", "governing", "system"])
        has_known_or_given = contains_any(answer, ["known", "given", "prescribed", "available", "user input"])
        has_domain_or_variables = contains_any(answer, ["domain", "omega", "boundary", "x", "t", "field"])
        handles_missing = contains_any(answer, ["missing", "unspecified", "not specified", "not explicitly", "must be specified"])
        if has_governing_setup and has_known_or_given and has_domain_or_variables and length >= 250:
            score = max(score, 4)
        if handles_missing and specificity >= 0.45 and length >= 350:
            score = max(score, 5)

    if facet_id == "validation_failure_risks":
        risk_markers = [
            "risk",
            "failure",
            "non-uniqueness",
            "overfitting",
            "noise",
            "stiff",
            "sharp",
            "spectral",
            "drift",
            "shock",
            "instability",
            "bias",
            "convergence",
        ]
        validation_markers = ["validate", "validation", "compare", "reference", "residual", "error", "metric", "held-out", "cross-validation"]
        risk_count = sum(1 for cue in risk_markers if cue in answer)
        has_validation_plan = contains_any(answer, validation_markers)
        if risk_count >= 3 and length >= 250:
            score = max(score, 3)
        if risk_count >= 3 and has_validation_plan and specificity >= 0.30:
            score = max(score, 4)
        if risk_count >= 4 and has_validation_plan and specificity >= 0.55 and length >= 450:
            score = max(score, 5)

    rationale = f"core_cue_ratio={core:.2f}; reference_item_match={matched}/{total}"
    return score, rationale


def apply_caps(score: int, row: dict[str, str], answer: str) -> tuple[int, list[str]]:
    facet_id = row["facet_id"] or FACET_IDS[row["facet"]]
    caps = []
    generic = generic_cap(answer, facet_id)
    if generic[0] is not None:
        caps.append((generic[0], generic[1] or "generic cap"))
    caps.extend(hard_trap_caps(row["task_id"], facet_id, answer))

    notes = []
    capped_score = score
    for cap, reason in caps:
        if capped_score > cap:
            capped_score = cap
            notes.append(f"cap<= {cap}: {reason}")
    return capped_score, notes


def score_rows(input_path: Path) -> list[dict[str, str]]:
    references = {row["id"]: row for row in read_jsonl(REFERENCES_PATH)}
    scored_rows: list[dict[str, str]] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"task_id", "model", "facet", "facet_id", "model_answer"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {input_path}: {sorted(missing)}")

        for line_no, row in enumerate(reader, start=2):
            reference = references.get(row["task_id"])
            if reference is None:
                raise ValueError(f"No v0.3 private reference for {row['task_id']} at line {line_no}")
            score, rationale = raw_score(row, reference)
            capped_score, cap_notes = apply_caps(score, row, norm(row["model_answer"]))
            row["human_score_0_5"] = str(capped_score)
            row["score"] = str(capped_score)
            row["score_rationale"] = rationale
            if cap_notes:
                row["score_rationale"] += "; " + "; ".join(cap_notes)
            scored_rows.append(row)
    return scored_rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    by_model: dict[str, list[float]] = defaultdict(list)
    by_model_facet: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        score = float(row["score"])
        by_model[row["model"]].append(score)
        by_model_facet[(row["model"], row["facet"])].append(score)

    fieldnames = ["model", "scored_facets", "total_points", "avg_facet_score", "avg_task_score_out_of_25"]
    facet_names = sorted({row["facet"] for row in rows})
    fieldnames.extend(f"avg_{facet}" for facet in facet_names)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for model in sorted(by_model):
            scores = by_model[model]
            out = {
                "model": model,
                "scored_facets": len(scores),
                "total_points": f"{sum(scores):.1f}",
                "avg_facet_score": f"{mean(scores):.3f}",
                "avg_task_score_out_of_25": f"{mean(scores) * 5:.3f}",
            }
            for facet in facet_names:
                vals = by_model_facet.get((model, facet), [])
                out[f"avg_{facet}"] = f"{mean(vals):.3f}" if vals else ""
            writer.writerow(out)


def write_task_summary(path: Path, rows: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    metadata: dict[str, dict[str, str]] = {}
    for row in rows:
        grouped[(row["task_id"], row["model"])].append(float(row["score"]))
        metadata[row["task_id"]] = {
            "difficulty": row["difficulty"],
            "domain": row["domain"],
            "task_type": row["task_type"],
            "pde_system": row["pde_system"],
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["task_id", "difficulty", "domain", "task_type", "pde_system", "model", "task_score_out_of_25", "avg_facet_score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (task_id, model), vals in sorted(grouped.items()):
            writer.writerow(
                {
                    **metadata[task_id],
                    "task_id": task_id,
                    "model": model,
                    "task_score_out_of_25": f"{sum(vals):.1f}",
                    "avg_facet_score": f"{mean(vals):.3f}",
                }
            )


def main() -> int:
    args = parse_args()
    rows = score_rows(args.input)
    write_rows(args.output, rows)
    write_summary(args.summary, rows)
    write_task_summary(args.task_summary, rows)

    scores = [float(row["score"]) for row in rows]
    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "rows": len(rows),
                "min_score": min(scores),
                "max_score": max(scores),
                "avg_score": round(mean(scores), 3),
                "summary": str(args.summary),
                "task_summary": str(args.task_summary),
            },
            ensure_ascii=False,
        )
    )
    if any(math.isnan(score) for score in scores):
        raise ValueError("NaN score detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
