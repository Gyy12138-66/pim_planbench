# medium_wave_sparse_sensors_012 重写规格（草案）

## 诊断（v0.3）
spread 3 / ρ 0.17（全基准倒数第三）。讽刺点：v0.3 题面**已经**要求"state
what additional information, assumptions, or identifiability checks are
required"，但评分器从未强制——泛泛一句"need more sensors"即过关。是
"题面意图正确、执行机制缺失"的典型。

## 决策支点（P1）
**波场数据同化的可观测性判断**：二阶波动方程需要两族初始数据；稀疏传感器
能否补足取决于传感器时空布局与波速锥的关系（信息沿特征传播——传感器的
影响域并集必须覆盖重建域）。支点 = 计划是否给出可判定的观测充分性论证
（覆盖锥/Nyquist 型条件），并对不可恢复的分量给出明确处理（正则化先验、
缩小重建目标、或声明不可行）。

## 新公开题面（英文草案）
> A team has sparse sensor measurements of a one-dimensional wave field over
> a time window. The wave speed is known, but neither initial conditions nor
> boundary conditions are provided. Whether the field is recoverable at all
> depends on how the sensor locations and the recording window relate to the
> domain of dependence of the wave equation. Design a physics-informed
> modeling workflow that (i) states a concrete sufficiency argument — in
> terms of wave speed, sensor positions, and window length — for which part
> of the space-time domain is recoverable, (ii) declares every assumption
> made about the unprovided initial and boundary information, and (iii)
> specifies what the workflow reports for regions it cannot constrain. Plans
> that silently assume full initial or boundary data are not acceptable.

## 可核验断言（P2）
- 内部一致性：声称的可恢复区域必须与声称的传感器数/位置/窗口通过 c·t 锥
  几何自洽（scorer v0.4 可做量纲级的锥覆盖对账）。
- 规格对账：执行实例的传感器布局（如 4 个等距点、T=2/c）与可恢复区域的
  参考计算写入私有参考。

## 任务特异 cap 规则（英文草案）
- If the plan assumes complete initial or boundary conditions that the prompt
  does not provide, without labeling them as assumptions and without stating
  how the workflow changes if they are unavailable, Problem Formalization is
  capped at 2 (hallucinated specification).
- If no sufficiency/observability argument connects sensors, wave speed, and
  window to the claimed reconstruction, Problem Formalization and Validation
  & Failure Risks are capped at 3.
- If the workflow claims to reconstruct the entire space-time field from
  sensors whose domains of influence provably do not cover it, affected
  facets are capped at 2.

## 私有参考 delta（P4）
- `failure_traps` += ["silently assumes full IC/BC", "no observability
  argument", "claims full-field recovery beyond sensor influence cones"]
- `critical_points.problem_formalization` += 影响域/依赖域论证
- `facet_cap_rules` += 上节三条；执行实例：4 传感器 + 已知解析波场

## 验收判据
spread ≥4；hallucinated-IC cap 至少触发 1 次（v0.3 全局零触发的 cap 在
本题复活是机制修复的直接证据）；ρ 转正。
