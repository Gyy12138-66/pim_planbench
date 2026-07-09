#!/usr/bin/env python3
"""批量执行效度实验：configs 目录 × 种子列表 -> 结果 CSV（支持断点续跑）。

用法：
  python run_validation.py --configs configs/arms --seeds 0 1 2 --out results_v0.4.csv
  python run_validation.py --configs configs/smoke --seeds 0 --max-adam-steps 300 \
      --out smoke_results.csv        # harness 冒烟
"""
import argparse
import csv
import glob
import os
import traceback

import pinn_harness as H


def done_keys(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {(r["config"], r["seed"]) for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True, help="配置目录或 glob")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-adam-steps", type=int, default=None)
    args = ap.parse_args()

    pattern = args.configs
    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*.yaml")
    cfgs = sorted(glob.glob(pattern))
    if not cfgs:
        raise SystemExit(f"no configs matched: {args.configs}")

    done = done_keys(args.out)
    total = len(cfgs) * len(args.seeds)
    i = 0
    for cfg in cfgs:
        for seed in args.seeds:
            i += 1
            key = (os.path.basename(cfg), str(seed))
            if key in done:
                print(f"[{i}/{total}] skip (done): {key}")
                continue
            print(f"[{i}/{total}] run: {key}")
            try:
                row = H.run_from_config(cfg, seed=seed,
                                        max_adam_steps=args.max_adam_steps)
            except Exception as e:
                traceback.print_exc()
                row = {"task": "?", "arm": "?", "config": os.path.basename(cfg),
                       "seed": seed, "diverged": 1, "eval_error": repr(e)}
            H.append_csv(args.out, row)
    print("all done ->", args.out)


if __name__ == "__main__":
    main()
