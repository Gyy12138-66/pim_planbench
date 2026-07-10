#!/usr/bin/env python3
"""转写产物校验（分析侧，非盲）：
1. 全部 configs/arms/*.yaml 可加载且 harness 2 步冒烟不报错；
2. 消融臂配置与 ablations_v0.4.json 的 expected_config 对照（协议 §5 审计的机器部分）；
3. 旋钮塌缩检查（协议 §5.6）：每题自然臂间取值互异的旋钮数 → config_diversity.csv；
   自然臂逐键全同的题按预注册规则从 H4a 剔除并如实报告。

用法：python3 validate_configs.py [--smoke]
"""
import argparse
import csv
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ARMS_DIR = HERE / "configs" / "arms"
MAP_CSV = HERE / "analysis_only" / "arm_code_map.csv"
ABLATIONS = HERE / "arms_text" / "ablations_v0.4.json"


def flatten(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="每配置跑 2 步 harness 冒烟")
    args = ap.parse_args()

    code_map = {r["code"]: r for r in csv.DictReader(MAP_CSV.open(encoding="utf-8"))}
    cfgs = {}
    problems = []
    for p in sorted(ARMS_DIR.glob("arm_*.yaml")):
        code = p.stem
        try:
            cfgs[code] = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            problems.append(f"YAML 解析失败 {p.name}: {e}")
    missing = set(code_map) - set(cfgs)
    if missing:
        problems.append(f"缺配置：{sorted(missing)}")

    # 消融臂 expected_config 对照
    specs = json.loads(ABLATIONS.read_text(encoding="utf-8"))["ablations"]
    by_ta = {(s["task_id"], s["arm"]): s for s in specs}
    for code, info in code_map.items():
        spec = by_ta.get((info["task"], info["arm"]))
        if not spec or spec["scorer_only"] or code not in cfgs:
            continue
        flat = flatten(cfgs[code])
        for key, want in (spec["expected_config"] or {}).items():
            got = flat.get(key)
            if got is None and want in (0, 0.0, False):
                # 期望 0/false 且未写：omitted 语义须显式写 0，提示审计
                problems.append(f"[审计] {info['task']} {info['arm']} ({code}) "
                                f"{key} 期望 {want}，配置未写该键（若 defaults 非 0 则语义错误）")
            elif got is not None and abs(float(got) - float(want)) > 1e-12 \
                    if isinstance(want, (int, float)) and not isinstance(want, bool) \
                    else (got is not None and got != want):
                problems.append(f"[审计] {info['task']} {info['arm']} ({code}) "
                                f"{key} 期望 {want}，实得 {got}")

    # 旋钮塌缩检查（仅自然臂 N1–N6）
    div_rows = []
    tasks = sorted({r["task"] for r in code_map.values()})
    for t in tasks:
        n_codes = [c for c, r in code_map.items()
                   if r["task"] == t and r["arm"].startswith("N") and c in cfgs]
        flats = [flatten({k: v for k, v in cfgs[c].items() if k not in ("task", "arm")})
                 for c in n_codes]
        keys = set().union(*[set(f) for f in flats]) if flats else set()
        diff = sorted(k for k in keys
                      if len({json.dumps(f.get(k), sort_keys=True) for f in flats}) > 1)
        div_rows.append({"task": t, "n_natural_arms": len(n_codes),
                         "n_diff_knobs": len(diff), "diff_knobs": "|".join(diff),
                         "h4a_eligible": int(len(diff) > 0)})
    with (HERE / "config_diversity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(div_rows[0].keys()))
        w.writeheader()
        w.writerows(div_rows)

    if args.smoke:
        import pinn_harness
        for code in sorted(cfgs):
            try:
                m = pinn_harness.run_from_config(str(ARMS_DIR / f"{code}.yaml"),
                                                 seed=0, max_adam_steps=2)
                if m.get("eval_error"):
                    problems.append(f"[冒烟] {code}: eval_error={m['eval_error']}")
            except Exception as e:
                problems.append(f"[冒烟] {code}: {type(e).__name__}: {e}")

    print(f"configs: {len(cfgs)}/{len(code_map)}")
    for r in div_rows:
        print(f"  diversity {r['task']}: {r['n_diff_knobs']} 个互异旋钮"
              f"{'' if r['h4a_eligible'] else '  ** 零方差，按预注册剔出 H4a **'}")
    if problems:
        print(f"\n{len(problems)} 个问题：")
        for p in problems:
            print(" -", p)
        return 1
    print("全部校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
