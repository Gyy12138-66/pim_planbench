# easy_reaction_diffusion_1d_006 重写规格（草案，轻改）

## 诊断（v0.3）
spread 4 / ρ 0.31；Model Choice 满分率 0.83。区分度处于边缘，题面对"非线性
反应项"没有提出任何任务特异要求，MC/TS 靠通用表述拿分。

## 决策支点（P1）
行波前沿的分辨与反应-扩散尺度分离：双稳/Fisher 型反应项产生宽度
δ ~ √(d/r) 的前沿、速度 v ~ √(d·r)。支点 = 计划是否把反应强度与扩散系数
的比值转化为采样与验证的定量要求（同 004 的分辨经济学，但驱动尺度来自
反应项而非黏性）。

## 新公开题面（英文草案，改动加粗处）
> A scientist wants to model a one-dimensional scalar reaction-diffusion
> process where a concentration diffuses and reacts according to a known
> nonlinear reaction term. Initial and boundary conditions are available.
> **The reaction is strong relative to diffusion, so the solution develops a
> propagating front whose width and speed are set by the balance of the two
> mechanisms.** Design a physics-informed modeling workflow for the
> concentration field, **including how the front scale enters your sampling
> and validation choices, and how you would detect a front that moves at the
> wrong speed even when the total loss looks small.**

## 可核验断言（P2）
- 内部一致性：声称的前沿宽度/速度公式与声称的采样密度自洽。
- 规格对账：执行实例（建议 Fisher-KPP，d、r 给定）下前沿速度的理论值
  2√(dr) 可作为验证断言的对账目标。

## 任务特异 cap 规则（英文草案）
- If the plan does not connect the reaction-diffusion balance to any concrete
  sampling or validation decision, Training Strategy is capped at 3.
- If validation cannot detect a wrong front speed (no front-position tracking,
  no comparison against the theoretical or reference speed), Validation &
  Failure Risks is capped at 3.

## 私有参考 delta（P4）
- 实例化建议：Fisher-KPP u_t = d·u_xx + r·u(1−u)，前沿速度 2√(dr) 解析可查
- `failure_traps` += ["ignores front scale in sampling", "validation blind to
  wrong front speed"]；`facet_cap_rules` += 上节两条

## 备选（供决策）
若 #1b 扩题后本槽位与 013（双物种反应扩散）功能重叠，可将本题降为
执行效度轮次的候补执行题（1D、有解析对账、便宜），或并入 013。

## 验收判据
spread ≥4 稳定；MC 满分率 0.83 → <0.3。
