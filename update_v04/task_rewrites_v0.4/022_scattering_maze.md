# hard_plus_acoustic_scattering_maze_022 重写规格（草案）

## 诊断（v0.3）
spread 1 / ρ 0.21;TS 满分率 1.00——与 021 并列全基准最失败。"maze-like
geometry"给了模型讲域分解故事的舞台,但散射问题真正的物理关口一个都
没被考。

## 决策支点（P1）
散射问题的三个可判定关口,其中第一个是二元且致命的:
1. **辐射条件/域截断**:开放散射域数值截断时,外边界必须是吸收型
   (Sommerfeld 辐射条件的近似、PML、一阶 ABC)——把外边界当 Dirichlet/
   Neumann 反射墙是物理错误,伪反射污染全域。这在 v0.3 的 tags 里
   (radiation_boundary)但题面与 rubric 均未强制。
2. **入射/散射场分解**:total field vs scattered field 表述的选择决定
   源如何进入方程与边界条件(障碍物上 u_total 满足硬/软条件,截断边界上
   只有 u_scattered 满足辐射条件)——混用即错。
3. **墙面 BC 族**(P3 干扰项天然存在):内部障碍(声硬 → Neumann /
   声软 → Dirichlet)与外截断边界(吸收)是不同 BC 族,计划必须分开
   指定,混淆即 cap。

## 新公开题面（英文草案）
> An acoustics group models time-harmonic wave scattering off a maze-like
> arrangement of internal obstacles in an unbounded two-dimensional medium.
> The incident wave and the obstacle surface properties (sound-hard) are
> known. Since the physical domain is unbounded, any computational domain
> must be truncated. Design a physics-informed modeling workflow. Required
> content: (i) whether you solve for the total field or the scattered field,
> and how the incident wave enters the formulation in your choice, (ii) the
> boundary treatment on the obstacle surfaces and — separately — on the
> artificial truncation boundary, including how outgoing waves are prevented
> from re-entering, and (iii) a validation check that would expose spurious
> reflections from the truncation boundary.

## 可核验断言（P2）
- 结构判定(scorer v0.4):截断边界处理声明 ∈ {PML, ABC, Sommerfeld
  近似, 边界积分} 的存在性;外边界声明为 Dirichlet/Neumann 反射条件
  → 物理矛盾检出。
- 一致性:声明 scattered-field 表述则障碍面条件应为 u_s = −u_inc(声软)
  或 ∂u_s/∂n = −∂u_inc/∂n(声硬)——表述选择与边界代入的配对可判。

## 任务特异 cap 规则（英文草案）
- If the truncation boundary is treated as a reflecting (Dirichlet or
  Neumann) wall, or no absorbing/radiation treatment is specified at all,
  Physics Constraints and Model Choice are capped at 2.
- If the plan never distinguishes total-field from scattered-field
  formulation, or injects the incident wave inconsistently with its stated
  choice, Problem Formalization and Physics Constraints are capped at 3.
- If obstacle boundary conditions and truncation boundary conditions are
  conflated into one treatment, Physics Constraints is capped at 2.
- If validation cannot detect spurious reflections (no energy-flux check,
  no comparison of near-field pattern against a reference/analytic case),
  Validation & Failure Risks is capped at 3.

## 私有参考 delta（P4）
- `constraints` 重写:障碍面(声硬 Neumann)与截断边界(吸收)分列;
  `canonical_pde` 注明 scattered-field 参考表述
- `failure_traps` += 四条 cap 触发行为
- 参考解:单圆柱散射的 Mie 级数解析解作为 maze 的退化校验实例(私有),
  maze 全构型用边界积分离线参考
- 几何复杂度(maze 阶数)公开量级/私有精确布局分离——防题面泄漏

## 验收判据
spread 1 → ≥4;反射墙 cap 至少触发 1 次;TS 满分率 1.00 → <0.2。
