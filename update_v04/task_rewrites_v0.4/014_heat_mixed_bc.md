# medium_heat_mixed_bc_014 重写规格（草案，兼并 001 槽位）

## 诊断（v0.3）
spread 2 / 均分 23.3（全基准最高）；MC/TS/PC 满分率 0.83/1.00/1.00——最
接近"送分题"的一道。ρ 0.94 说明它排序与总分高度一致但没有分辨力（人人
高分,差距靠 1 分噪声）。同时 001（纯 Dirichlet 热传导,spread 2）与本题
同物理槽位——决议（item_analysis §4-C）：001 并入本题,槽位只留一道
"1D 热传导 + 混合 BC"重写题,001 编号让给 #1b 新题。

## 决策支点（P1）
**Neumann 通量的符号/方向约定**：题面以物理语言给热流（"heated at a rate
…into the rod" / "insulated"），计划必须把物理方向翻译成带符号的法向导数
（−k·∂u/∂n = q, n 为外法向）。符号错误 = 物理上加热变冷却，执行必然偏离
参考——这是典型的"文本看似正确、执行灾难"支点，正是本基准该考的。
第二支点：**能量收支验证**——∫u dx 的变化率 = 边界净热流,离散可查,
是比 field MSE 更根本的物理一致性检验。

## 新公开题面（英文草案）
> A researcher models heat conduction in a one-dimensional rod. One end is
> held at a fixed temperature. At the other end, heat is injected into the
> rod at a prescribed constant rate through the boundary surface. The initial
> temperature profile is known, and the material properties are given. Design
> a physics-informed modeling workflow for the temperature field. Make the
> boundary treatment fully explicit: write the flux condition as a signed
> relation between the outward normal derivative and the stated injection
> rate, and explain how you verify the sign is physically correct. Include in
> your validation an energy-balance check relating the change of total
> thermal energy in the rod to the boundary fluxes, with a tolerance.

## 可核验断言（P2）
- 规格对账（scorer v0.4 数值核验的教科书案例）：计划写出的通量条件符号
  （±k·u_x(L,t) = q）与"注入"方向的规格对账——符号断言可机器判定。
- 内部一致性：能量收支声明的两侧（d/dt ∫u vs 边界通量差）形式自洽。

## 任务特异 cap 规则（英文草案）
- If the flux boundary condition is stated without an explicit sign
  convention tied to the outward normal (or with a sign inconsistent with
  the stated physical direction of heat flow), Physics Constraints and
  Training Strategy are capped at 2.
- If the flux condition is enforced as a value constraint on u rather than on
  its normal derivative, Physics Constraints is capped at 2.
- If validation contains no energy-balance or flux-consistency check,
  Validation & Failure Risks is capped at 3.

## 私有参考 delta（P4）
- `reference_conditions.boundary`：左端 Dirichlet `u(0,t)=0`、右端注入
  `k·u_x(L,t) = +q_in`（q_in > 0,数值入私有实例）。约定：外法向 n = +x̂,
  边界外流通量 = −k·∂u/∂n;"注入"⇔ 外流为负 ⇔ k·u_x(L,t) = +q_in。
  （注意:`−k·∂u/∂n = q_in` **不是**等价写法——那是抽热。）
- `failure_traps` += ["flux sign inconsistent with stated direction",
  "flux enforced as value constraint", "no energy balance validation"]
- `facet_cap_rules` += 上节三条；`analytic_solution`：常通量 + 定温端的
  经典级数解可作参考
- 001 的参考条目标记 superseded,归档不删除（治理节要求可追溯）

### 编写注记（符号事故,入设计决策表/治理节素材）

本节初稿曾写作 `−k·u_x(L,t)=+q（注入）`——按外法向约定这是**抽热**：
规格作者本人踩中了本题设计的陷阱,在落地格式转写核对时被检出
（`docs/dataset_schema_v0.4.md` §4）。此记录有意保留：它是"该支点考的
是真困难、人工审文本抓不住、必须机器核验"的一手证据；同时提示参考侧
自检（references.py --self-test 一类）应覆盖解析解与 BC 符号的一致性。

## 验收判据
spread ≥4；符号 cap 至少触发 1 次；均分从 23.3 显著下降（送分题修复的
直接证据,写进论文 item-analysis 叙事）。
