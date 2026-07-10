# GPU 机器运行手册（执行效度子集 v0.4）

预注册冻结 commit：`7ca7937`。**运行期间不得改动** `configs/arms/`、
`configs/defaults_v0.4.yaml`、协议与清单文档；如必须改 harness（发现 bug），
记录改动并通知——按协议 §5.3 需重跑全部臂。

## 1. 环境

```bash
# Python 3.10+，安装 CUDA 版 torch 及依赖
pip install torch numpy scipy pandas matplotlib pyyaml
python3 -c "import torch; print(torch.cuda.is_available())"   # 应为 True
```

设备自动选择（defaults 里 `device: auto`，有 CUDA 就用 CUDA），无需改配置。

## 2. 取码

```bash
git clone https://github.com/Gyy12138-66/pim_planbench && cd pim_planbench
git log --oneline -1   # 应为 7ca7937 或更新
cd update_v04/execution_validation
```

## 3. 构建参考解（一次性，约 5–15 分钟，CPU 即可）

```bash
python3 references.py --self-test
```

全部自检通过（Sod 星区 p*=0.30313/u*=0.92745、Burgers 奇对称 ~1e-9）再继续。

## 4. 可行性门（先跑这个，GPU 上约 15–30 分钟）

只跑 023 金计划臂（盲码 arm_db5c98）3 个种子：

```bash
for s in 0 1 2; do
  python3 pinn_harness.py --config configs/arms/arm_db5c98.yaml --seed $s --out gate_023.csv
done
cat gate_023.csv
```

**预注册判据**：三种子 `diverged=0` 且 `rel_l2` 显著 < 1（0.3–0.8 量级即通过）。

- **通过** → 直接进入第 5 步全量运行。
- **不通过**（rel_l2 ≥ 1 或发散）→ 023 从执行子集剔除（协议 §2 已预注册此分支），
  把 023 的 10 个臂移出后再跑全量：

```bash
mkdir -p configs/arms_excluded_023
grep -l "task: hard_plus_euler_shock_023" configs/arms/*.yaml | xargs -I{} mv {} configs/arms_excluded_023/
```

  （替补题 008 的臂需回到主工作机撰写转写后补充，先跑其余 4 题不受影响。）

## 5. 全量运行（约 0.5–1 GPU·天，断点续跑）

```bash
nohup python3 run_validation.py --configs configs/arms --seeds 0 1 2 \
    --out results_v0.4.csv > run.log 2>&1 &
tail -f run.log
```

- 50 臂 × 3 种子 = 150 次训练（含门里已跑的 db5c98——run_validation 会重跑，无妨；
  或先把 gate_023.csv 的行手工并入亦可）。
- **断点续跑**：中断后重复同一命令，已完成的 (config, seed) 会自动跳过。
- 种子说明：协议最低要求自然/G/T 臂 2 种子、消融臂 3 种子；统一跑 3 种子是
  预注册要求的超集，分析阶段按协议取用，多出的种子只会增加稳健性。

## 6. 回传结果

需要带回的文件（.gitignore 排除了 csv，用 `-f` 强制提交，或直接拷贝）：

```bash
git add -f gate_023.csv results_v0.4.csv
git add run.log 2>/dev/null; git commit -m "execution validation raw results (GPU run)" && git push
```

回传后在主工作机做分析（analyze_validity.py 需要与 `analysis_only/arm_code_map.csv`、
`arms_v0.4.csv` 合并，盲码在分析阶段才解盲）。

## 7. 故障处置

- 单臂发散（`diverged=1`）是**合法结果**（rel_l2 记 10），不要调参重跑；
- CUDA OOM 几乎不可能（网络 ≤128×6、配点 ≤2 万）；若出现，报告而非改配置；
- 中途断电/断线：直接重复第 5 步命令续跑。
