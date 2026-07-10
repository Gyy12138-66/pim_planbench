#!/usr/bin/env python3
"""盲化准备（转写清单 §0）：给全部可执行臂分配随机码，产出无身份线索的转写包。

- 码 = sha1("pim-v0.4::" + task + "::" + arm)[:6]，确定性可复现；
- arms_blind/<code>.json 只含 {code, task_id, facets}，不含臂身份与模型名；
- analysis_only/arm_code_map.csv 为码↔臂映射，转写者不得读取，分析阶段合并；
- scorer_only 臂（D2 x4、D3_010）不执行，不生成转写包。
"""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BLIND = HERE / "arms_blind"
ANALYSIS = HERE / "analysis_only"
ARMS_TEXT = HERE / "arms_text"
GEN = ARMS_TEXT / "generated"
NATURAL_CSV = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv"

TASKS = [
    "easy_poisson_2d_source_003",
    "easy_advection_1d_periodic_005",
    "medium_burgers_inverse_viscosity_010",
    "hard_allen_cahn_016",
    "hard_plus_euler_shock_023",
]


def code_for(task: str, arm: str) -> str:
    return "arm_" + hashlib.sha1(f"pim-v0.4::{task}::{arm}".encode()).hexdigest()[:6]


def main() -> int:
    BLIND.mkdir(exist_ok=True)
    ANALYSIS.mkdir(exist_ok=True)

    bundles = []  # (task, arm, label, code, facets)
    with NATURAL_CSV.open(encoding="utf-8-sig", newline="") as f:
        natural = [r for r in csv.DictReader(f) if r["task_id"] in TASKS]
    n_map = {m: f"N{i+1}" for i, m in enumerate(sorted({r["model"] for r in natural}))}
    facets: dict = {}
    for r in natural:
        facets.setdefault((r["task_id"], n_map[r["model"]]), {})[r["facet"]] = r["model_answer"]
    for (task, arm), fx in facets.items():
        bundles.append((task, arm, [m for m, n in n_map.items() if n == arm][0], fx))

    template = json.loads((ARMS_TEXT / "T_template.json").read_text(encoding="utf-8"))
    for task in TASKS:
        gold = json.loads((ARMS_TEXT / f"G_{task}.json").read_text(encoding="utf-8"))
        bundles.append((task, "G", "gold_reference", gold["facets"]))
        bundles.append((task, "T", "generic_template", template["facets"]))
    for spec in json.loads((ARMS_TEXT / "ablations_v0.4.json").read_text(
            encoding="utf-8"))["ablations"]:
        if spec["scorer_only"]:
            continue
        gen = json.loads((GEN / f"{spec['task_id']}__{spec['arm']}.json").read_text(
            encoding="utf-8"))
        bundles.append((spec["task_id"], spec["arm"], "ablation", gen["facets"]))

    with (ANALYSIS / "arm_code_map.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task", "arm", "label", "code"])
        for task, arm, label, fx in sorted(bundles, key=lambda b: (b[0], b[1])):
            code = code_for(task, arm)
            w.writerow([task, arm, label, code])
            (BLIND / f"{code}.json").write_text(
                json.dumps({"code": code, "task_id": task, "facets": fx},
                           ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(bundles)} blind bundles -> {BLIND}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
