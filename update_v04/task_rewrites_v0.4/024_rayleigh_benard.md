# hard_plus_rayleigh_benard_024 重写规格（草案）

## 诊断（v0.3）
spread 2 / ρ 0.31;MC 满分率 0.83。题面已列出全部要素(耦合、不可压、
边界层传热)但以清单形式给出——模型照单复述即高分。多物理耦合的
**方向性**(谁驱动谁)从未被考。

## 决策支点（P1）
1. **Boussinesq 双向耦合的完整性**:浮力项 α·g·T 进动量方程(T 驱动流)
   且 温度被速度平流 u·∇T(流驱动 T)——只写单向(常见错:动量里没有
   浮力项,或 T 方程退化为纯扩散)即物理断裂,可从残差列表机器判定。
2. **传热收支验证**:上下板 Nusselt 数(或热通量)必须一致(定常统计意义
   下),这是比 field error 更根本的物理一致性——两板 Nu 不等 = 能量
   不守恒的直接证据。计划必须承诺这个可算的双边检验。
3. 压力规范(与 018 同,次要支点)。

## 新公开题面（英文草案）
> A fluid dynamics group models steady (or statistically steady)
> Rayleigh-Benard convection in a two-dimensional cell heated from below and
> cooled from above, under the Boussinesq approximation. Design a
> physics-informed modeling workflow coupling velocity, pressure, and
> temperature. Required content: (i) the full residual system you train on,
> written term by term, making explicit where the temperature acts on the
> momentum balance and where the velocity acts on the heat balance, (ii)
> boundary conditions for each field on each wall, (iii) how the pressure is
> made unique, and (iv) a validation plan that includes a heat-transport
> consistency check between the two plates, with the quantity you will
> compute and the tolerance you will accept.

## 可核验断言（P2）
- 残差完备性(scorer v0.4 结构判定):动量残差含浮力项 且 温度残差含
  平流项——逐项列写是题面要求,缺项可机器判定。
- Nu 双边一致:声称的验证量(上下板 Nu/通量)与阈值形式存在性。
- 内部一致性:声称"steady"却写时间推进课程 → 需自洽说明(伪时间可,
  但要声明)。

## 任务特异 cap 规则（英文草案）
- If the momentum residual omits the buoyancy coupling term, or the
  temperature residual omits advection by the velocity field, Physics
  Constraints is capped at 2 (one-way coupling).
- If no heat-transport consistency check between the plates (Nusselt or
  flux balance) appears in validation, Validation & Failure Risks is capped
  at 3.
- If pressure uniqueness is not addressed (as in task 018), Physics
  Constraints and Training Strategy are capped at 3.
- 保留通用 cap(不可压缺失等)。

## 私有参考 delta（P4）
- `canonical_pde` 逐项列写(浮力项、平流项显式)
- `failure_traps` += ["one-way coupling (missing buoyancy or advection
  term)", "no two-plate heat-flux consistency check", "pressure gauge
  unaddressed"]
- `facet_cap_rules` += 上节;执行实例:低 Ra(如 5×10³,层流定常滚动)
  谱参考——执行效度第二轮候选(2D 但小规模可控)
- P3 预算:2D 三场耦合昂贵,建议加配点/步数预算逼分配论证(与 021 一致)

## 验收判据
spread ≥4;单向耦合 cap 至少触发 1 次;MC 满分率 0.83 → <0.3。
