# 执行效度验证协议 v0.4（预注册文档）

- 状态：**草案** —— 正式运行前需作者批准并 commit 冻结（git 时间戳即预注册证据）
- 代码：`update_v04/execution_validation/`
- 回应评审：PdEo 弱点 3（"无证据表明 PlanScore 预测真实建模效果"）、d2gd 弱点 4（执行验证缺失）、Ed11（可证伪假设）

## 1. 目标与假设

执行**不进入**评测流程，只作一次性效度验证，给 PlanScore 颁发"廉价代理"资格。

- **H4a（观察性）**：同一任务内，PlanScore 越高的计划，按其执行的 PINN 相对 L2 误差越低（任务内 Spearman ρ < 0）。
- **H4b（因果性）**：从高分计划中精确删除 rubric 惩罚的元素（cap 规则对应项），执行误差随之显著增大（配对 Wilcoxon，Δ log10 relL2 > 0）。
- **H4c（cap 机制）**：触发 cap 规则的计划，其执行误差系统性地高于未触发者。

论文措辞钉死定位：*"Execution is used once for validity evidence, not per-evaluation. Evaluating a model on PIM-PlanBench never requires training a PINN."*

## 2. 任务选择（预注册标准，防 cherry-pick 质疑）

入选标准：① 六模型 PlanScore 分差 ≥ 5/25（无方差则无法检验相关）；② 1D/2D 小尺度可执行；③ 有解析解或廉价高保真参考；④ 合计覆盖难度层（easy→hard_plus）与任务类型（forward/inverse/陷阱）。

| 任务 | 分差 | 角色 | 参考解 |
|---|---|---|---|
| `easy_poisson_2d_source_003` | 6.0 | easy·forward | 制造解（解析） |
| `easy_advection_1d_periodic_005` | 5.0 | easy·周期·已知失败模式 | 精确解（初值平移） |
| `medium_burgers_inverse_viscosity_010` | 5.0 | medium·inverse | 高分辨 MOL（LSODA，带状 Jacobian） |
| `hard_allen_cahn_016` | 5.0 | hard·刚性陷阱 | 谱方法 + 自适应积分 |
| `hard_plus_euler_shock_023` | 8.0 | hard_plus·激波陷阱 | Sod 精确 Riemann 解 |

**可行性门**：正式纳入 `023` 前，先只执行其金计划（G 臂）配置；若金计划在小尺度上不能收敛到明显优于平凡解的水平（rel L2 显著 < 1），则该题从主分析剔除、换入 `medium_advection_diffusion_008`（分差同为 5.0），并在论文如实报告。地板效应本身也是可报告的发现。

## 3. 数值实例化表（TODO_REVIEW：作者批准后冻结）

公开题面刻意不含具体数值（TODO_FILL 设计），执行需要一个具体实例。实例一律取社区经典设定，与 `references.py` 一一对应：

| 任务 | 实例化 |
|---|---|
| 003 | −Δu=f，f=2π²sin(πx)sin(πy)，[0,1]²，齐次 Dirichlet；u*=sin(πx)sin(πy) |
| 005 | u_t+cu_x=0，c=1，x∈[0,1) 周期，t∈[0,1]，u₀=sin(2πx) |
| 010 | u_t+uu_x=νu_xx，ν_true=0.01/π，x∈[−1,1]，t∈[0,1]，u₀=−sin(πx)，Dirichlet 0；观测 N=2000、相对噪声 1%、种子 0（Raissi 经典反问题） |
| 016 | u_t=du_xx+5(u−u³)，d=10⁻⁴，x∈[−1,1) 周期，t∈[0,1]，u₀=x²cos(πx)（经典 PINN 硬基准） |
| 023 | Sod 激波管：γ=1.4，左 (ρ,u,p)=(1,0,1)、右 (0.125,0,0.1)，x∈[0,1]，隔膜 x=0.5，t∈(0,0.2]（波未及边界，边界钉初始常态） |

## 4. 实验臂（每题 ~11 份计划）

| 臂 | 内容 | 来源 |
|---|---|---|
| N1–N6 | 六模型的自然计划 | `runs/` 已有 |
| G | 私有参考金计划 | `dataset/references_private_v0.3.jsonl`，天花板锚点 |
| T | 通用 PINN 模板计划 | 撰写一份、全部题复用；**兼任 d2gd 要求的模板基线** |
| D1 | G 删去关键物理约束/BC 项 | ↔ missing-constraint cap |
| D2 | G 的任务类型改错（如 inverse→forward） | ↔ wrong-task-type cap |
| D3 | G 中植入幻觉规格（篡改方程系数/编造组件） | ↔ hallucination cap |

规则：
- 消融臂的文本改动**最小化**——只动目标元素，其余逐字保留；改动 diff 存档。
- **全部臂都过一遍现行自动评分器**得到 plan_score 与 capped 标志（含 N1–N6 重新确认），写入 `arms_v0.4.csv`（列：task,arm,plan_score,capped,kind,parent_arm）。
- Validation/Failure Risks facet 不影响训练轨迹，**不做训练消融**。单独做"故障检出"小实验：每题诱导两个经典失败（损失失衡塌缩到平凡解；激波/界面欠分辨），盲评者按各计划 validation 清单判断能否检出，报告检出率与该 facet 分的相关。若不做，则论文明确声明 H4b 仅覆盖前四个 facet。

## 5. 执行协议（防"实现者技巧"混淆）

1. **单一 harness**：`pinn_harness.py`，组件菜单：网络宽深/激活、随机 Fourier 特征、周期嵌入、软/硬 IC·BC、损失权重（可线性 ramp）、均匀采样+重采样+RAR、课程式时间推进、Adam(+L-BFGS)、反问题 ν（log 参数化）、Euler 人工粘性。菜单范围须覆盖 26 份私有参考计划提及组件的并集；计划提出菜单外组件 → 就近映射并记录（`mapping_log.csv`）。
2. **确定性转写**：按 `plan_to_config_checklist_v0.4.md` 把计划文本映射为 YAML；转写者对模型身份与 plan_score **双盲**（臂文件用随机码命名）；未指定旋钮一律取 `configs/defaults_v0.4.yaml`。
3. **默认值冻结**：defaults 由作者批准后 commit，之后不得改动；若必须改（如发现 bug），重跑全部臂并在论文注明。
4. **审计**：第二人独立重转写 ≥20% 随机臂；不一致处仲裁并全量复查该旋钮。
5. **随机性**：自然臂/G/T 每臂 2 种子，消融臂与其 parent 3 种子（配对检验）；Adam 步数封顶（defaults 中冻结）。

## 6. 结果指标与统计分析（预注册）

指标：相对 L2（对参考解，held-out 网格；Euler 取 ρ,u,p 平均、跳过 t=0）；010 另报 |ν̂−ν|/ν；发散/NaN 记 diverged=1 且 **rel_l2 := 10**（log10=1，比任何收敛结果差）。

- **主分析 1（H4b）**：D 臂 vs parent 同种子配对，Δlog10 relL2 的 Wilcoxon 符号秩（单侧 greater），按算子分列 + 合并；报中位 Δ 与 n。
- **主分析 2（H4a）**：臂级（种子中位数）任务内 Spearman ρ(plan_score, log10 relL2)；跨任务平均 ρ + 任务内 bootstrap（B=10⁴）95% CI。**不做跨任务混合相关**（Simpson 悖论）。
- **辅助 1（H4c）**：capped vs uncapped 臂的 log10 relL2，Mann-Whitney U（单侧）。
- **辅助 2**：facet 级相关（预期 Physics Constraints、Training Strategy 最强——独立的可写发现）。
- 全部由 `analyze_validity.py` 产出（`validity_summary.md` + `validity_scatter.png` + `per_task_spearman.csv`）。

## 7. 预算（封顶）

5 题 × ~11 臂 × 2–3 种子 ≈ **130–160 次小训练**；1D 数分钟/次（CPU 可跑）、2D 单卡 ≤10 分钟；合计 ≈ 1–2 GPU·天，一次性。最小可发表版本：3 题（003/005/016）≈ 60 次。

## 8. 论文呈现

- 一节（约 1 页）+ 主图（PlanScore vs log10 relL2 散点，按题着色、按臂型标记、消融配对箭头）+ 一表（各题 ρ、配对 Δ 与 p、capped vs uncapped）。
- 与效度框架合并叙述：区分度（去饱和+CI）→ 抗套模板(T)→ 收敛效度（盲评 IAA）→ **预测效度（本实验）**。
- Limitations 如实写：仅覆盖 5/26 可执行子集；harness 菜单有界（不测计划之外的创造性实现）；不涉及代码生成能力；样本小、以配对设计承担统计重量。

## 9. 操作步骤

```bash
cd update_v04/execution_validation
python3 references.py --self-test          # 构建并校验参考解（已通过）
# 1) 撰写 T 臂与 D1–D3 臂文本（外部 docs 流程），全部臂过自动评分器 -> arms_v0.4.csv
# 2) 按 checklist 盲转写全部臂 -> configs/arms/*.yaml（随机码命名）
# 3) 冻结 defaults_v0.4.yaml + configs/arms + 本协议 -> git commit（预注册）
# 4) 可行性门：python3 run_validation.py --configs configs/arms/gate_023_gold.yaml --seeds 0 1 2 --out gate.csv
python3 run_validation.py --configs configs/arms --seeds 0 1 2 --out results_v0.4.csv
python3 analyze_validity.py --results results_v0.4.csv --arms arms_v0.4.csv --outdir analysis_v0.4
```

## 10. 已验证状态（2026-07-09）

- 参考解自检通过：Sod 星区 p*=0.30313/u*=0.92745 命中理论值；Burgers 奇对称 2.6e-9；AC 值域正常。
- 5 题 harness 300 步冒烟全部收敛路径正常（diverged=0；Poisson relL2 0.13、Burgers ν̂ 已到正确量级）。
- 分析管线合成数据自检：ρ=−0.906、CI 正常、图表产出正常。
