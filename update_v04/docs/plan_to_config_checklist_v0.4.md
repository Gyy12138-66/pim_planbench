# 计划 → 配置 转写清单 v0.4（盲转写操作手册）

目的：把一份计划文本**忠实转录**为 harness YAML 配置。转写者的唯一职责是"翻译"，
严禁补全、优化或纠错计划内容——计划的缺陷正是实验要测的对象。

## 0. 盲化准备（由非转写者执行）

1. 每个臂分配随机码（如 `arm_7f3a`），文件名与 YAML `arm` 字段只用随机码；
2. 剥离计划文本中的模型署名/来源线索；
3. 转写者不得接触 plan_score、capped 标志或模型身份；
4. 随机码 ↔ 真实臂 的映射表由非转写者保管，分析阶段才合并。

## 1. 逐旋钮转写规则

按顺序回答，每项在计划文本中找**明示依据**；找不到 → 该旋钮**不写**（自动落到
defaults_v0.4.yaml 的预注册默认值），并在 mapping_log 记 `unspecified`。

| # | 旋钮 | YAML 键 | 判定规则 |
|---|---|---|---|
| 1 | 网络宽/深/激活 | `net.width/depth/activation` | 计划给出数值才填；只说"MLP"不填。激活菜单 tanh/gelu/sin，其他→就近映射并记录 |
| 2 | Fourier 特征 | `features.fourier.num/sigma` | 计划明确提 Fourier/positional 特征才启用；未给参数→num=64, sigma=5.0 并记 `partial` |
| 3 | 周期嵌入 | `features.periodic_harmonics` | 计划提"周期性输入编码/嵌入"才启用（默认 4 谐波，给了数按数）；仅提"周期边界条件"**不算**（那是 BC 处理，走 #4） |
| 4 | 硬/软约束 | `constraints.hard_bc/hard_ic` | 计划明说"硬约束/ansatz/构造性满足"→ hard；说罚项/损失项→ soft（默认） |
| 5 | 配点与采样 | `sampling.n_pde/n_bc/n_ic/resample_every` | 给了数按数；"动态重采样"→ resample_every=1000 并记 `partial` |
| 6 | RAR/自适应加点 | `sampling.rar.*` | 计划提残差自适应采样才启用（默认 every=1000, pool=50000, add=500） |
| 7 | 损失权重 | `weights.*` | **损失项集合先于权重数值**：某约束项（bc/ic/data/periodic）在计划全文（含 Physics Constraints facet）**完全未被提及** → 该项权重置 0 并记 `omitted`（计划的缺失正是实验对象，defaults 不得替计划补全约束——否则 D1 类缺失永远落不到配置层）；提及但未给权重 → 1.0；给数按数；只说"加大 IC 权重"这类定性→ 该项 ×10 并记 `qualitative`；提"权重退火/warmup"→ {start,end,steps} ramp，端点未给→ start=0.1·end |
| 8 | 优化器 | `optimizer.adam.lr/steps`、`optimizer.lbfgs.steps` | 给数按数；提"Adam 后接 L-BFGS"未给步数→ lbfgs.steps=500 并记 `partial` |
| 9 | 课程/时间推进 | `curriculum` | 计划提 time-marching/课程训练才启用；未给分段→ [0.25,0.5,1.0] 三段均分总步数，记 `partial` |
| 10 | 反问题初值 | `inverse.init_nu` | 010 专用；计划给了先验/初值按其值，否则默认 |
| 11 | 人工粘性 | `euler.artificial_viscosity` | 023 专用；计划提人工粘性/扩散正则才启用，未给量→ 0.005 记 `partial` |
| 12 | PDE 系数 | `pde.*`（poisson_source_scale / advection_c / burgers_nu_fixed / ac_d / ac_reaction / euler_gamma） | 计划**明确断言了具体数值**且与实例化表冲突 → 按计划值填入对应键，记 `conflict`；符号表述（"对流速度 c"）、与实例化一致、或未提 → **不写**。转写者手头有实例化表（公开材料），无须知道臂身份即可判定冲突 |
| 13 | 数据损失开关 | `data.enabled` | 010 专用；计划明确表述"ν 已知 / 正问题 / 不使用观测数据" → enabled=false，且 ν 值按计划断言填 `pde.burgers_nu_fixed`（计划未给值 → 0.1，记 `partial`）；否则不写 |

**菜单外组件**（如自适应权重算法、注意力网络、域分解）：不实现；就近映射
（说明理由）或忽略，必须在 mapping_log 记 `out_of_menu`。此日志随论文附录发布。

### 1.1 仲裁澄清（v0.4 盲转写期间裁定，随协议一并冻结）

- **符号形式 ≠ 数值断言（#12）**：教科书式符号写法（如 `u−u³`、`(1/ε)(u³−u)`、
  "对流速度 c"）不构成与实例化表的系数冲突；仅当计划给出**具体数值**且与实例化表
  换算后矛盾时记 `conflict`（ε 表述按 d=ε² 换算后再判）。
- **区间值**：计划给区间（如 "4–8 层"、"50–100 神经元"、"lr 1e-3→1e-4"）：默认值
  落在区间内 → 不写该键，记 `partial` 并注明；默认值在区间外 → 取最近端点，记 `partial`。
- **对冲语气不启用**：consider / optionally / possibly / can help / if needed /
  仅在风险缓解清单中"或"式出现 → 不启用，记 `unspecified` 附原文；use / employ /
  implement / apply / is recommended / is preferred → 承诺，启用。条件句
  （"if the IC is known"）的条件由实例化表满足时视为承诺。
- **"Adam or L-BFGS" 非顺序句式**：不满足 #8 的"Adam 后接 L-BFGS"，不启用 lbfgs。
- **构造性周期（harmonics>0）时的 `weights.periodic`**：写 0.0 或不写均可
  （harness 在 harmonics>0 时不计算该损失项，行为等价）；审计不视为不一致。

## 2. mapping_log.csv 字段

`arm_code, knob, plan_quote(原文摘录), decision, tag(exact|partial|qualitative|unspecified|out_of_menu|conflict)`

## 3. 审计

- 第二人对 ≥20% 随机臂独立重转写；
- 逐键 diff：不一致 → 三方仲裁（转写者、审计者、规则文本），并全量复查该旋钮；
- 审计通过后，configs/arms 目录 commit 冻结。

## 4. 消融臂（D1–D3）撰写规则（非转写步骤，由作者执行、在盲化之前）

- 基底一律为该题金计划 G；只做**最小文本编辑**，其余逐字保留；
- D1：删去 rubric 判定为关键的物理约束/BC 描述段；
- D2：把任务类型表述改错。**仅 010 撰写可执行版**（"估计 ν 的反问题"改写为
  "ν = 0.1 已知的正问题"，随之删去 data loss 描述 → 转写落到 #13）；
  其余 4 题的 D2 只进评分器侧检验，不执行（见协议 §4 可执行性边界）；
- D3：植入幻觉规格。**优先用系数篡改**（改错方程系数并写明具体数值，
  如 ν=0.1、c=2、γ=2.0、d=10⁻²、源项翻倍 → 转写落到 #12，全部 5 题可执行）；
  "编造损失组件名"变体只进评分器侧检验，不进 H4b 配对；
- 每个消融的 diff 存 `ablation_diffs/`，随附录发布。
