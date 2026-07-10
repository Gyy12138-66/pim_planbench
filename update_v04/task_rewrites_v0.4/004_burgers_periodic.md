# easy_burgers_1d_periodic_004 重写规格（草案）

## 诊断（v0.3）
spread 2 / ρ 0.68；Training Strategy 满分率 1.00——六个模型全员在"可能出现
陡梯度"的提示下背诵 RAR/权重平衡拿满分。没有任何定量责任：黏性层宽度
O(ν) 与配点密度、网络容量之间的换算从未被要求。

## 决策支点（P1）
黏性激波层的**分辨经济学**：层宽 δ ~ O(ν)，层内至少需要若干配点与足够的
表示带宽；在给定算力预算下，均匀采样 vs 自适应采样的配点分配是一个可算的
取舍。支点 = 计划是否给出"ν → 层宽 → 采样/容量需求"的定量论证，而不是
名词堆砌（"use RAR"）。

## 新公开题面（英文草案）
> A team wants to model a one-dimensional viscous Burgers system on a periodic
> spatial domain. The initial velocity profile and the viscosity coefficient
> are known, and the viscosity is small enough that a steep internal layer of
> width comparable to the viscosity scale will form. The compute budget is
> fixed in advance: at most 20,000 residual collocation points in memory at
> any time and at most 30,000 optimizer steps in total. Design a
> physics-informed modeling workflow for the velocity field. Justify
> quantitatively — in terms of the viscosity scale — how your sampling
> strategy and network capacity resolve the internal layer within the stated
> budget, and what you would monitor to detect an under-resolved layer.

## 可核验断言（P2）
- 内部一致性（公开可查）：声称的层内配点数 = 预算 × 层宽占比 ×（自适应
  富集倍数）——三个数计划自己给出，乘出来矛盾即断言失效；声称步数/配点
  超出题面预算 → 直接矛盾。
- 规格对账：执行效度轮次中 ν 的实例值与层宽断言的量级一致性。

## 任务特异 cap 规则（英文草案）
- If the plan invokes adaptive sampling, refinement, or loss weighting by
  name without any quantitative link between the viscosity scale, the layer
  width, and the collocation allocation, Training Strategy is capped at 3.
- If the proposed sampling or optimization plan exceeds the stated compute
  budget, or ignores it, Training Strategy and Model Choice are capped at 3.
- If validation includes no indicator specific to an under-resolved layer
  (residual concentration near the front, layer-width estimate vs theory,
  oscillation detection), Validation & Failure Risks is capped at 3.

## 私有参考 delta（P4）
- `failure_traps` += ["names RAR/weighting without quantitative layer-budget
  argument", "sampling plan exceeds stated budget", "no under-resolution
  indicator in validation"]
- `critical_points.training_strategy` += 层宽-预算换算；预算合规
- `parameter_values` 执行实例建议 ν=0.01/π（与 010 参考解基建复用）
- `facet_cap_rules` += 上节三条

## 验收判据
spread ≥4；TS 满分率 1.00 → <0.2；预算 cap 至少触发 1 次。
