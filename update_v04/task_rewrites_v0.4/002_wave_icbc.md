# easy_wave_1d_icbc_002 重写规格（草案）

## 诊断（v0.3）
spread 3 / ρ 0.34；Physics Constraints 满分率 0.83。二阶时间方程给了两个 IC，
但所有模型都"提到"两个 IC 就拿满分——没人被要求说明**速度 IC 是导数级约束**
（u_t(x,0) 需对网络输出求时间导后惩罚，或用时间因子硬编码），也没人处理
IC/BC 角点相容性。

## 决策支点（P1）
初速度条件的施加方式是导数级的：软施加需要 autograd 的 ∂u_θ/∂t 在 t=0 上的
残差项；硬施加需要 ansatz u_θ = f(x) + t·g(x) + t²·N(x,t) 类构造。二元且后果
严重：把 u_t(x,0) 当作普通值约束（或干脆只钉 u(x,0)）训练出的解在短时间内
就偏离特征线传播。角点相容性（f(0)=f(1)=0 与 BC 一致、g 同理）是第二支点。

## 新公开题面（英文草案）
> A scientist needs to approximate the displacement of a one-dimensional
> vibrating string over a fixed time window. The wave speed is known. Both the
> initial displacement profile and the initial velocity profile are provided
> as measured data, and the endpoints are held fixed. Because the initial data
> come from measurements, they may fail to satisfy the endpoint conditions
> exactly at the corners of the space-time domain. Design a physics-informed
> modeling workflow for the displacement field. State explicitly (i) how each
> of the two initial conditions is enforced, including any derivative-level
> treatment the second one requires, (ii) how compatibility between initial
> and boundary data is checked and what the workflow does if it fails, and
> (iii) which physical invariants of the ideal system you will monitor during
> validation and with what tolerance.

## 可核验断言（P2）
- 内部一致性：验证节声称监控能量 E(t)=½∫(u_t²+c²u_x²)dx → 若计划同时声称
  "无阻尼理想弦"，能量应守恒；声称监控却无阈值/漂移判据 → VR 不得 5。
- 规格对账（评分时）：速度 IC 残差项 ∂u_θ/∂t(x,0)−g(x) 是否作为独立损失/
  硬约束出现（scorer v0.4：Training Strategy 文本中检测导数级 IC 表述）。

## 任务特异 cap 规则（英文草案，入 rubric v0.4）
- If the plan enforces only the displacement initial condition, or treats the
  initial velocity as a value constraint on u rather than a constraint on the
  time derivative of the network output (or an equivalent hard-encoding),
  Physics Constraints and Training Strategy are capped at 2.
- If the prompt states the initial data may be incompatible with the boundary
  conditions and the plan neither checks compatibility nor states a remedy,
  Problem Formalization and Validation & Failure Risks are capped at 3.
- If validation omits every wave-specific check (energy drift, d'Alembert /
  characteristic consistency, reflection behavior), Validation & Failure
  Risks is capped at 3.

## 私有参考 delta（P4）
- `failure_traps` += ["treats initial velocity as a value constraint (misses
  derivative-level enforcement)", "no corner compatibility check between
  IC and BC", "claims energy conservation monitoring without a drift
  tolerance"]
- `critical_points.physics_constraints` += 导数级速度 IC；角点相容性
- `facet_cap_rules` += 上节三条
- `reference_conditions` 增补一组**故意不相容**的执行验证实例（如
  u(x,0)=sin(πx)+0.05、端点 0）用于未来执行效度轮次
- `expected_validation` += 能量漂移阈值、特征线一致性

## 验收判据
6 模型重跑后 spread ≥4；速度-IC cap 至少触发 1 次；PC 满分率从 0.83 降至 <0.3。
