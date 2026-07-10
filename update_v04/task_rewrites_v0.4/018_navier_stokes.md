# hard_navier_stokes_2d_018 重写规格（草案）

## 诊断（v0.3）
spread 2 / ρ 0.31。题面把"pressure is not directly observed"当背景信息给出,
但没有任何机制要求模型面对它的后果——**压力规范自由度**。模型集体输出
"网络输出 (u,v,p),损失加动量残差+连续性残差+数据项"的标准配方拿 20+。

## 决策支点（P1）
两个耦合支点:
1. **压力可辨识性/规范固定**:不可压 NS 中压力只由速度场确定到相差一个
   常数(且仅当边界给定合适条件);压力无观测时,不固定规范(参考点钉零/
   零均值约束/出口压力条件)的优化问题是退化的——训练慢、压力漂移。
   计划必须显式钉规范,或选择消压表述(流函数-涡度)并说明代价。
2. **散度控制方式**:软惩罚 vs 构造性无散(流函数求导得速度)是二元结构
   决策,与 025 的散度支点同族但物理不同——软惩罚需监控散度漂移。

## 新公开题面（英文草案）
> A fluid dynamics group wants to reconstruct a two-dimensional
> incompressible flow from partial velocity observations. Pressure is not
> observed anywhere. The model must respect momentum balance and
> incompressibility; boundary and initial conditions are available only
> partially. Design a physics-informed modeling workflow for velocity and
> pressure. Address explicitly: (i) to what extent the pressure field is
> determined by the available information, and what your workflow adds to
> make it unique; (ii) whether incompressibility is enforced by penalty or
> by construction, and — if by penalty — how divergence drift is monitored
> and bounded; (iii) which parts of your validation would detect a spurious
> pressure mode that leaves the velocity fit unchanged.

## 可核验断言（P2）
- 规格对账:规范固定声明的存在性与形式(钉点/零均值/出口条件)——
  scorer v0.4 检测"pressure"上下文中规范机制表述的缺席与"recover the
  absolute pressure from velocity data"类过度声明(后者为矛盾断言)。
- 内部一致性:选构造性无散(流函数)却仍列连续性残差损失 → 冗余矛盾;
  软惩罚却无散度监控 → 承诺缺口。

## 任务特异 cap 规则（英文草案）
- If the plan outputs pressure but neither fixes a gauge (reference point,
  zero-mean constraint, or boundary pressure condition) nor adopts a
  pressure-free formulation, Physics Constraints and Training Strategy are
  capped at 3.
- If the plan claims to recover absolute pressure values from velocity
  observations alone, Problem Formalization is capped at 2 (identifiability
  error).
- If incompressibility is enforced only as a soft penalty and validation
  includes no divergence monitoring, Validation & Failure Risks is capped
  at 3.

## 私有参考 delta（P4）
- `critical_points.problem_formalization` += 压力规范;`unknowns` 标注
  "p 至相差常数"
- `failure_traps` += ["no pressure gauge fixing", "claims absolute pressure
  from velocity data", "soft divergence penalty without monitoring"]
- `facet_cap_rules` += 上节三条;执行实例建议:Taylor-Green 涡(解析参考,
  2D 可执行,未来效度轮次候选)

## 验收判据
spread ≥4;规范 cap 至少触发 1 次;与 024/025 的排名相关下降(三道耦合
流动题解耦为不同支点的证据)。
