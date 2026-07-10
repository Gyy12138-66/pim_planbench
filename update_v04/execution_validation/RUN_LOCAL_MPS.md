# 本机全量运行手册（Mac MPS，无外部 GPU 时的方案）

前提：外部 GPU 不可用。实测基准（2026-07-10，本机）：
- MPS 可用且二阶自动微分正常；300 步冒烟 rel_l2 与 CPU 一致（Burgers
  0.0214 vs 0.0223、Euler 0.3884 vs 0.3894）
- 023 冒烟 MPS 比 CPU 快 3×（13.6s vs 40.8s）；小任务加速比 ~1.2×
- 估算全量 150 次：**MPS ≈ 2.5–3 天连续**（CPU ≈ 6 天）

## 设备一致性决策（重要，预注册纪律）

**全部 150 次（含 023 金计划臂）统一在 MPS 上重跑。** gate_023.csv 的
CUDA 结果只作可行性门证据，不并入 results_v0.4.csv——H4b 配对比较
（D 臂 vs parent 同种子）必须同设备，跨设备混跑会把设备数值差混进 Δ。
若改走云 CUDA 方案（见文末），同理全量统一 CUDA，gate 行亦可并入
（同后端；GPU 型号差异在论文注明）。

## 步骤

```bash
cd update_v04/execution_validation
python3 references.py --self-test          # 参考解自检（本机已通过可跳过）
python3 make_mps_configs.py                # 生成 configs_mps/arms/（派生目录）
nohup python3 run_validation.py --configs configs_mps/arms --seeds 0 1 2 \
    --out results_v0.4.csv > run_mps.log 2>&1 &
tail -f run_mps.log
```

- **断点续跑**：中断（合盖/重启/手动 kill）后重复同一条 nohup 命令，
  已完成的 (config, seed) 自动跳过。
- **散热**：连续三天满载，建议外接电源、保证通风；夜间跑白天停完全可行
  （续跑机制承担）。
- 首个 run 结束时核对：`head -2 results_v0.4.csv`——若首臂 rel_l2 量级
  与其冒烟/门参考严重偏离（如 db5c98 应在 0.08–0.09 附近），停下报告，
  不要调参。
- 完成判据：`wc -l results_v0.4.csv` = 151（表头 + 150 行）。
- 之后：`python3 analyze_validity.py --results results_v0.4.csv
  --arms arms_v0.4.csv --outdir analysis_v0.4`（解盲与辅助输入自动探测）。

## 备选：云 CUDA（更快更省心，约 $10–15）

vast.ai / runpod 租 RTX 4090/5080 级 spot（~$0.3–0.5/时 × 15–20 GPU·时）：
按 `RUN_ON_GPU.md` 第 1–3、5–6 步执行即可（门已通过，跳过第 4 步；
全量统一在租用机上跑，gate 行可并入）。回传只需 results_v0.4.csv 与
run.log 两个文件。

## 故障处置

同 `RUN_ON_GPU.md` §7：发散是合法结果不重跑；异常报告不改配置。
MPS 特有：若出现 MPS 后端不支持的算子报错（理论上冒烟已排除），全量
退回 CPU（同一命令换 configs 目录前先重新生成镜像为 `device: cpu`），
并把预计时长 ×2。
