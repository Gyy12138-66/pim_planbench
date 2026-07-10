#!/usr/bin/env python3
"""生成 MPS 镜像配置目录（configs_mps/arms/），不触碰冻结的 configs/arms/。

每个冻结臂 YAML 复制一份并追加 `device: mps`。文件名与 arm 字段不变，
结果 CSV 与分析管线完全兼容。镜像目录是派生产物，已加入 .gitignore。

预注册合规声明：device 是执行环境而非实验旋钮——可行性门在 CUDA 上跑、
早期存档在 CPU 上跑（gate_023_cpu_seed0_archive.csv），协议未冻结设备；
冻结文件本身未被改动。本脚本与生成目录即改动记录。
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "configs", "arms")
DST = os.path.join(HERE, "configs_mps", "arms")


def main():
    os.makedirs(DST, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "*.yaml")))
    if len(files) != 50:
        sys.exit(f"预期 50 个冻结臂配置，实际 {len(files)}——目录状态异常，中止")
    for path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if "device:" in text:
            sys.exit(f"{path} 已含 device 键——冻结配置不应指定设备，中止")
        out = os.path.join(DST, os.path.basename(path))
        with open(out, "w", encoding="utf-8") as f:
            f.write(text.rstrip("\n") + "\ndevice: mps\n")
    print(f"{len(files)} 个 MPS 镜像配置 -> {DST}")


if __name__ == "__main__":
    main()
