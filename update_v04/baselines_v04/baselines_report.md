# 基线与消融报告（修订项 #2，v0.4）

生成：`update_v04/run/08_baselines_v04.sh`（确定性，可复现）；日期 2026-07-13。

回应评审：PdEo（"rubric-matching text" 可套分、"Eq. 5's constants are unexplained
with no ablation"）、d2gd（缺 expert-written / template baseline）。

## 臂定义与威胁模型

| 臂 | 威胁模型 | 可见信息 |
|---|---|---|
| T | 表述胜任但零任务特异的通用模板计划 | 无（一份文本全题复用） |
| S1 | 黑盒关键词堆砌：读过公开 rubric 来套分的对手 | 公开题面 + `docs/rubric_v0.3.md` |
| S2 | 白盒关键词堆砌（最坏情形）：读过评分器源码的对手 | 评分器内部线索词表与门控词 |
| GOLD | oracle 天花板：私有参考字段的确定性渲染 | 私有参考全部字段（**不冒充专家手写计划**） |

S1/S2 均为无结构关键词罗列（非连贯计划）；GOLD 渲染复用评分器
`reference_items()` 的字段→facet 映射，参考项逐条拼接，无人工润色。
所有重打分基于冻结评分器 `scripts/score_3modeloutput_v03.py`（只调用，未改动）；
cap 消融与 Eq.5 敏感性使用参数化镜像，默认参数下与冻结评分器逐行等值
（守卫断言，见 `scorer_mirror.py`）。


## 基线臂全题投放（T / S1 / S2 / GOLD × 26 题）

| 臂 | 定义 | 均分/25 | 最低 | 最高 |
|---|---|---|---|---|
| GOLD | 私有参考确定性渲染（oracle 天花板，见过私有参考） | 22.9 | 18 | 24 |
| S2 | 关键词堆砌·白盒（评分器内部词表，最坏情形） | 21.7 | 16 | 25 |
| S1 | 关键词堆砌·黑盒（公开题面 + 公开 rubric 词汇） | 24.1 | 16 | 25 |
| T | 通用模板计划（一份文本全题复用） | 15.9 | 10 | 20 |
| （6 模型最佳） | 每题取面板最高分模型 | 22.9 | 20 | 25 |
| （6 模型中位） | 每题面板中位数 | 21.3 | 19 | 24 |

- GOLD ≥ 当题最佳模型：18/26 题；GOLD 被 cap 击中的题数：3/26（trap 描述文本触发负向规则的行数见任务级 CSV，属 oracle 渲染的已知伪影，如实报告）
- S2（白盒堆砌）≥ 当题最佳模型：12/26；≥ 当题中位模型：20/26；被 cap 击中：2/26
- S1（黑盒堆砌）≥ 当题中位模型：24/26；被 cap 击中：2/26
- T（模板）≥ 当题中位模型：0/26；被 cap 击中：4/26

### 解读（如实报告，不回避）

- **模板防线有效**：连贯但零任务特异的 T 臂被稳定压制（0/26 达中位），generic cap 与 pf_strict 按设计工作。
- **关键词堆砌防线失守**：S1 只用公开信息即在多数题上超过中位模型，甚至超过 oracle 渲染（题面词 + rubric 词的堆砌同时喂饱了 core cue 覆盖率、参考项 token 匹配率与全部长度/missing 加分，而作为无结构词表又几乎不踩任何负向规则）。这实证确认了 PdEo 的 rubric-matching text 质疑在 v0.3 覆盖层上成立——人类或 LLM 评审对这类无结构词表会给 0 分，纯覆盖匹配层无法分辨。
- **对应的既定修订动作**：修订项 #1 的可核验断言重写（欠定规格逼真实建模决策，词表堆砌无法给出定量断言）与修订项 #2 的 scorer v0.4 断言核验层；v0.4 重打分时此表即论文的 before/after 对比列。建议（待作者确认）：S1/S2 两臂并入评分器发布门的对抗回归套件。
- GOLD 被 cap 击中的 3 题源于 failure_trap 描述文本里含触发词（oracle 逐条渲染的已知伪影）；GOLD 定位是自动评分口径下的天花板锚点，非人工润色的专家计划。

任务级明细：`generated/baseline_task_totals_v0.4.csv`；facet 级评分：`generated/baseline_arms_scored_v0.4.csv`。

## cap 规则开/关重打分（cap 消融）

| 变体 | Kimi-K2.6 | GLM-4.7 | GLM-5.1 | DeepSeek-V4-Flash | deepseek-v4-pro | qwen3.7-max | 排名 τ vs 默认 | 变动行数/780 |
|---|---|---|---|---|---|---|---|---|
| full | 22.15 | 19.92 | 21.81 | 21.12 | 21.12 | 21.19 | 1.000 | 0 |
| no_ext | 22.15 | 20.19 | 21.81 | 21.12 | 21.38 | 21.42 | 0.966 | 10 |
| no_pf | 22.62 | 20.65 | 22.58 | 21.88 | 21.69 | 21.81 | 0.828 | 86 |
| no_caps | 22.62 | 20.92 | 22.58 | 21.88 | 21.96 | 22.04 | 0.966 | 96 |

基线臂在各变体下的均分/25（cap 对反模板防线的贡献）：

| 变体 | GOLD | S1 | S2 | T |
|---|---|---|---|---|
| full | 22.92 | 24.12 | 21.69 | 15.92 |
| no_ext | 23.35 | 24.77 | 22.27 | 16.50 |
| no_pf | 23.35 | 24.12 | 21.81 | 16.35 |
| no_caps | 23.77 | 24.77 | 22.38 | 17.08 |

pf_strict 内部 cap 生效行数（面板 780 行）：86

外部 cap（generic/hard-trap）触发原因 Top 10（面板行）：

- 3 次：smooth strong-form PINN without weak/integral/conservative shock-aware treatment
- 2 次：mentions value periodicity but not derivative or diffusive-flux periodicity
- 2 次：neural operator suggested without many coefficient fields or generalization protocol
- 2 次：does not model coupled velocity and magnetic induction fields
- 1 次：missing magnetic divergence control

全量数据：`generated/cap_onoff_v0.4.csv`。

## Eq.5 常数敏感性

默认排名（26 题均分/25）：Kimi-K2.6 22.15 > GLM-5.1 21.81 > qwen3.7-max 21.19 > DeepSeek-V4-Flash 21.12 > deepseek-v4-pro 21.12 > GLM-4.7 19.92

### OAT：每常数单独 ×{0.8, 0.9, 1.1, 1.2}

| 常数 | 默认值 | 最差排名 τ | 无严格逆序的扰动数/4 |
|---|---|---|---|
| BASE | 1.0 | 0.929 | 4/4 |
| W_SPEC | 2.2 | 0.926 | 4/4 |
| W_CORE | 1.25 | 0.929 | 4/4 |
| CORE_NORM | 0.45 | 0.966 | 4/4 |
| LEN_B1 | 0.35 | 0.786 | 2/4 |
| LEN_B2 | 0.25 | 0.786 | 2/4 |
| MISS_B | 0.2 | 0.966 | 4/4 |
| DET_B1 | 0.25 | 0.929 | 4/4 |
| DET_B2 | 0.35 | 1.000 | 4/4 |

### 联合扰动：9 常数同时均匀 ±25% × 200 次（种子 20260713）

- 排名 τ（tau-b，并列校正）：min 0.690 / median 0.966 / mean 0.944
- 无严格逆序比例（默认严格序对零反转；默认排名中恰有一对并列，脱离并列不计）：86.5%；Top-1 不变比例：100.0%
- 模型均分最大偏移（全部扰动中）：2.65 / 25

范围说明：仅扰动 Eq.5 的 9 个数值常数；长度/比例门槛与 facet 规则逻辑属规则结构，保持固定（cap 的消融见上一节）。全量数据：`generated/eq5_sensitivity_v0.4.csv`。
