# medium_reaction_diffusion_noisy_013 重写规格（草案）

## 诊断（v0.3）
spread 2 / ρ 0.61；均分 19.0（全基准最低）但仍不区分——所有模型同样平庸。
"noisy data"在题面里只是形容词：没有噪声结构、没有物种间差异，模型答
"加数据损失+正则化"即达 v0.3 得分上限。

## 决策支点（P1）
两个耦合支点：
1. **噪声感知目标**：异方差噪声（两物种噪声水平不同/随浓度变化）下，
   等权 MSE 在统计上是错的——计划必须把声明的噪声模型映射到损失加权
   （高噪观测降权）或似然形式。
2. **物种可观测性不对称**（P3 干扰项）：物种 A 有观测、物种 B 完全无观测
   ——B 只能通过耦合动力学间接约束。计划必须论证 B 的可恢复性依赖于耦合
   项的结构，并说明若耦合弱则 B 不可辨识。

## 新公开题面（英文草案）
> A biophysics group studies a two-species reaction-diffusion process with a
> known coupled reaction form. Species A is observed at scattered space-time
> locations with noise whose magnitude is roughly proportional to the local
> concentration; species B is not observed at all. Design a physics-informed
> modeling workflow that fits both concentration fields. State explicitly
> (i) how the stated noise structure enters your objective — an unweighted
> mean-squared data loss is not a neutral default here, (ii) through which
> terms of the coupled dynamics the unobserved species is constrained, and
> under what conditions it would not be recoverable, and (iii) a validation
> design that does not reward overfitting the noisy observations of A.

## 可核验断言（P2）
- 内部一致性：声明"比例噪声"后仍使用未加权 MSE → 目标与噪声模型矛盾
  （scorer v0.4：噪声声明与损失形式的共现检查）。
- 规格对账：执行实例的噪声系数、B 物种耦合强度写入私有参考；ν 型可辨识性
  论证与实例参数对账。

## 任务特异 cap 规则（英文草案）
- If the plan uses an unweighted data loss while the prompt states
  concentration-proportional noise, and gives no likelihood-based or
  weighting-based justification, Training Strategy is capped at 3.
- If the plan treats species B as observed, or never addresses how B is
  constrained despite having no data, Problem Formalization and Physics
  Constraints are capped at 2.
- If validation reports only the fit to species A's noisy data (no held-out
  design, no physics-residual check for B), Validation & Failure Risks is
  capped at 3.

## 私有参考 delta（P4）
- `constraints.observations`：A 有噪观测（比例噪声）、B 无观测——明确写入
- `failure_traps` += ["unweighted MSE under stated heteroscedastic noise",
  "treats unobserved species as observed", "validates only on A's noisy fit"]
- `facet_cap_rules` += 上节三条
- 执行实例建议：Schnakenberg/λ-ω 型耦合（1D、谱参考便宜）

## 验收判据
spread ≥4；treats-B-as-observed cap 至少触发 1 次；均分从 19 降（难度轴
贡献为正）且 spread 扩大。
