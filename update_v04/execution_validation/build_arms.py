#!/usr/bin/env python3
"""构建执行效度实验臂并全部过自动评分器（协议 §4 / 操作步骤 1）。

输入：
  arms_text/G_*.json            5 题金计划（facet 级文本）
  arms_text/T_template.json     通用模板计划（全题复用）
  arms_text/ablations_v0.4.json 消融臂 find/replace 规范
  scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv  六模型自然计划（N1–N6）

输出：
  arms_text/generated/<task>__<arm>.json   生成的 D/T 臂文本
  ablation_diffs/<task>__<arm>.diff        消融臂相对 G 的统一 diff（随附录发布）
  arms_text/generated/arms_input_v0.4.csv  评分器输入（N+G+T+D 全部臂）
  arms_text/generated/arms_scored_v0.4.csv 评分器逐 facet 输出
  arms_v0.4.csv                            臂级汇总（task,arm,plan_score,capped,...）

用法：python3 build_arms.py
"""
import csv
import difflib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARMS_TEXT = HERE / "arms_text"
GEN = ARMS_TEXT / "generated"
DIFFS = HERE / "ablation_diffs"
NATURAL_CSV = ROOT / "scores/pilot_v0.3/ModelOutput_all_existing_v0.3.csv"
SCORER = ROOT / "scripts/score_3modeloutput_v03.py"

TASKS = [
    "easy_poisson_2d_source_003",
    "easy_advection_1d_periodic_005",
    "medium_burgers_inverse_viscosity_010",
    "hard_allen_cahn_016",
    "hard_plus_euler_shock_023",
]
FACETS = [
    ("Problem Formalization", "problem_formalization"),
    ("Physics Constraints", "physics_constraints"),
    ("Model Choice", "model_choice"),
    ("Training Strategy", "training_strategy"),
    ("Validation Failure Risks", "validation_failure_risks"),
]


def apply_ops(gold: dict, spec: dict) -> dict:
    """对金计划文本施加最小编辑；每个 find 必须恰好命中一次。"""
    facets = dict(gold["facets"])
    for op in spec["ops"]:
        text = facets[op["facet"]]
        n = text.count(op["find"])
        if n != 1:
            raise SystemExit(
                f"[{spec['task_id']} {spec['arm']}] find 命中 {n} 次（须为 1）：{op['find'][:80]!r}")
        facets[op["facet"]] = text.replace(op["find"], op["replace"])
    return facets


def write_diff(task: str, arm: str, gold: dict, facets: dict) -> None:
    lines = []
    for fname, _ in FACETS:
        a, b = gold["facets"][fname], facets[fname]
        if a == b:
            continue
        lines += difflib.unified_diff(
            a.splitlines(keepends=True) or [a], b.splitlines(keepends=True) or [b],
            fromfile=f"G/{fname}", tofile=f"{arm}/{fname}", lineterm="")
        lines.append("")
    (DIFFS / f"{task}__{arm}.diff").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    GEN.mkdir(exist_ok=True)
    DIFFS.mkdir(exist_ok=True)

    with NATURAL_CSV.open(encoding="utf-8-sig", newline="") as f:
        natural = [r for r in csv.DictReader(f) if r["task_id"] in TASKS]
    columns = list(natural[0].keys())
    meta = {}
    for r in natural:
        meta.setdefault(r["task_id"], {k: r[k] for k in
                                       ("difficulty", "domain", "task_type", "pde_system")})
    # N1–N6 按模型名字典序固定映射（分析阶段合并用，不改 model 列本身）
    n_map = {m: f"N{i+1}" for i, m in enumerate(sorted({r["model"] for r in natural}))}

    golds = {t: json.loads((ARMS_TEXT / f"G_{t}.json").read_text(encoding="utf-8"))
             for t in TASKS}
    template = json.loads((ARMS_TEXT / "T_template.json").read_text(encoding="utf-8"))
    ablations = json.loads(
        (ARMS_TEXT / "ablations_v0.4.json").read_text(encoding="utf-8"))["ablations"]

    arms = []  # (task, arm, kind, parent, scorer_only, facets)
    for t in TASKS:
        arms.append((t, "G", "gold", "", False, golds[t]["facets"]))
        arms.append((t, "T", "template", "", False, template["facets"]))
    for spec in ablations:
        facets = apply_ops(golds[spec["task_id"]], spec)
        write_diff(spec["task_id"], spec["arm"], golds[spec["task_id"]], facets)
        out = {**{k: spec[k] for k in ("task_id", "arm", "kind", "parent_arm",
                                       "scorer_only", "target_element")},
               "facets": facets}
        (GEN / f"{spec['task_id']}__{spec['arm']}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        arms.append((spec["task_id"], spec["arm"], "ablation",
                     spec["parent_arm"], spec["scorer_only"], facets))

    rows = list(natural)
    for task, arm, kind, parent, s_only, facets in arms:
        for fname, fid in FACETS:
            row = {c: "" for c in columns}
            row.update(meta[task])
            row.update({"task_id": task, "model": f"ARM/{arm}",
                        "prompt_setting": "arms_v0.4", "facet": fname,
                        "facet_id": fid, "model_answer": facets[fname],
                        "schema_valid": "True"})
            rows.append(row)
    inp = GEN / "arms_input_v0.4.csv"
    with inp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

    scored = GEN / "arms_scored_v0.4.csv"
    subprocess.run(
        [sys.executable, str(SCORER), "--input", str(inp), "--output", str(scored),
         "--summary", str(GEN / "arms_summary_by_model.csv"),
         "--task-summary", str(GEN / "arms_summary_by_task.csv")],
        check=True)

    # 臂级汇总
    agg = {}
    with scored.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            m = r["model"]
            arm = m[4:] if m.startswith("ARM/") else n_map[m]
            key = (r["task_id"], arm)
            a = agg.setdefault(key, {"score": 0.0, "capped_facets": [], "label": m})
            a["score"] += float(r["score"])
            if "cap<= " in r["score_rationale"]:
                a["capped_facets"].append(r["facet_id"])
    info = {(s["task_id"], s["arm"]): s for s in ablations}
    out = HERE / "arms_v0.4.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task", "arm", "label", "kind", "parent_arm", "scorer_only",
                    "plan_score", "capped", "capped_facets"])
        for (task, arm), a in sorted(agg.items()):
            if arm.startswith("N"):
                kind, parent, s_only = "natural", "", False
            elif arm == "G":
                kind, parent, s_only = "gold", "", False
            elif arm == "T":
                kind, parent, s_only = "template", "", False
            else:
                spec = info[(task, arm)]
                kind, parent, s_only = "ablation", spec["parent_arm"], spec["scorer_only"]
            w.writerow([task, arm, a["label"], kind, parent, s_only,
                        a["score"], int(bool(a["capped_facets"])),
                        "|".join(a["capped_facets"])])
    print(f"arms_v0.4.csv: {len(agg)} arms -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
