# update_v04 —— 回应 ARR 评审的 v0.4 修订工作区

本目录汇集 v0.4 修订的新增材料，与既有 v0.3 冻结基线隔离。

## 目录

```
update_v04/
├── README.md                                本文件
├── revision_plan_v0.4.md                    修订总路线（6 项优先级 × 评审映射 × rebuttal 口径）
├── docs/
│   ├── execution_validation_protocol_v0.4.md   执行效度验证协议（预注册文档，含实例化表）
│   └── plan_to_config_checklist_v0.4.md         计划→配置盲转写清单 + 消融臂撰写规则
└── execution_validation/                    执行效度子集代码（已冒烟验证）
    ├── references.py                        5 题参考解（含 Sod 精确 Riemann 解），缓存 npz
    ├── pinn_harness.py                      统一 PINN 训练 harness（菜单化组件，YAML 驱动）
    ├── run_validation.py                    批量运行（断点续跑）
    ├── analyze_validity.py                  统计分析（任务内 Spearman + 配对 Wilcoxon + 散点图）
    ├── configs/
    │   ├── defaults_v0.4.yaml               预注册默认值表（跑前冻结）
    │   ├── smoke/*.yaml                     5 个 harness 冒烟配置（非正式实验臂）
    │   └── arms/                            正式实验臂配置（待盲转写产出）
    └── reference_data/                      参考解缓存（可由 references.py 重建）
```

## 快速开始

```bash
cd execution_validation
python3 references.py --self-test                 # 构建/校验参考解
python3 run_validation.py --configs configs/smoke --seeds 0 \
    --max-adam-steps 300 --out /tmp/smoke.csv     # harness 冒烟
python3 analyze_validity.py --demo --outdir /tmp/demo  # 分析管线自检
```

依赖：python3 + torch / numpy / scipy / pandas / matplotlib / pyyaml（本机已验证可用）。

## 当前状态（2026-07-10）

- [x] 代码全部就绪并通过冒烟（参考解自检、5 题训练管线、分析管线）
- [x] harness 增加 `pde.*` 系数覆盖与 `data.enabled` 旋钮（D2/D3 消融可真实执行，已冒烟）；
      协议补预注册条款：H4a 只用自然臂 + CI 判定规则、消融可执行性边界、旋钮塌缩预案
- [ ] 撰写 T 臂与 D1–D3 消融臂文本，全部臂过自动评分器 → `arms_v0.4.csv`
- [ ] 按清单盲转写 → `configs/arms/`，冻结 defaults + 协议（git commit 预注册）
- [ ] Euler 题可行性门 → 全量运行（1–2 GPU·天）→ `analyze_validity.py` 出图表
- [ ] 修订路线其余 5 项见 `revision_plan_v0.4.md`
