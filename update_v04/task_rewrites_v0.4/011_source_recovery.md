# medium_poisson_source_recovery_011 重写规格（草案）

## 诊断（v0.3）
spread 3 / ρ 0.39；MC 满分率 0.83、PF 0.83。反问题里最病态的一类（源项
反演）却没人被要求面对病态性：v0.3 题面说"源必须从数据与物理中恢复"，
模型泛泛提"用网络参数化源+数据损失"即可高分。

## 决策支点（P1）
**源项不可辨识性**：部分内部观测 + 边界数据不能唯一确定分布源（多个源
配置可产生同样的可观测场）；任何合法计划必须（i）声明病态性，（ii）承诺
一种正则化/参数化（Tikhonov、稀疏性、低维基底、物理先验），（iii）说明该
选择引入的偏差以及观测布局如何影响可辨识性。三者缺一即支点失守。

## 新公开题面（英文草案）
> A scientist has interior observations of a two-dimensional potential field
> at a limited set of locations and wants to infer an unknown source term in
> a Poisson equation. Boundary information is available. Be aware that with
> finitely many observations the source is in general not uniquely
> determined: different source configurations can reproduce the same
> observations. Design a physics-informed modeling workflow for joint field
> reconstruction and source recovery. State explicitly (i) how the source is
> represented and why that representation restores well-posedness, (ii) what
> regularization you add and what bias it introduces, and (iii) how the
> observation layout limits which source features are recoverable, including
> a validation design that honestly reflects those limits.

## 可核验断言（P2）
- 内部一致性：声称"唯一恢复/exact recovery"同时又未给正则化 → 矛盾断言
  （scorer v0.4 检测"unique/exactly recover"与正则化承诺缺席的共现）。
- 规格对账：执行实例中源的自由度数 vs 观测数的比值（欠定倍数）写入私有
  参考，验证声称与之对账。

## 任务特异 cap 规则（英文草案）
- If the plan claims unique or exact source recovery from the stated partial
  observations without any regularization or restrictive parameterization,
  Problem Formalization and Physics Constraints are capped at 2.
- If the source representation (network, basis, grid) is chosen without any
  identifiability rationale, Model Choice is capped at 3.
- If validation evaluates only the reconstructed field and never the
  recovered source against held-out information (or does not acknowledge
  that source error cannot be fully validated without ground truth),
  Validation & Failure Risks is capped at 3.

## 私有参考 delta（P4）
- `failure_traps` += ["claims unique recovery without regularization",
  "no identifiability rationale for source representation", "validates field
  only, never the source"]
- `critical_points.problem_formalization` += 病态性声明；`facet_cap_rules`
  += 上节三条
- 执行实例建议：高斯源两叶配置 + 16–32 个观测点（欠定倍数明确可算）

## 验收判据
spread ≥4；"唯一恢复"cap 至少触发 1 次；PF/MC 满分率 <0.3。
