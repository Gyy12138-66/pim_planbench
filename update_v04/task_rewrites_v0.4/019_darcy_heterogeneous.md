# hard_darcy_heterogeneous_019 重写规格（草案）

## 诊断（v0.3）
spread 3 / ρ 0.12（全基准倒数第二）。"correctly accounting for heterogeneous
coefficients"在题面里没有牙齿:κ 的光滑性未说明,模型可以安全地写
∇·(κ∇h) 也可以写 κΔh + ∇κ·∇h,评分器都放行。

## 决策支点（P1）
**保守形式 vs 非法展开**:当 κ 分片常数/含尖锐通道(题面将明说)时,
∇κ 在界面上不存在,展开式 κΔh + ∇κ·∇h 在数学上非法且执行时在界面附近
系统性出错;h 本身 C⁰ 但法向导数跳跃(κ∂h/∂n 连续才是物理约束)。合法
路线:保守形式的弱式/积分残差、界面通量连续显式约束、或声明 κ 光滑化
假设并量化其偏差。这是"文本正确性可判、执行后果严重"的支点。

## 新公开题面（英文草案）
> A geoscience team models steady Darcy flow through a porous medium whose
> permeability field is known but piecewise-heterogeneous: it contains
> sharp, channel-like contrasts across internal interfaces where the
> permeability jumps by orders of magnitude. Boundary conditions are
> available. Design a physics-informed modeling workflow for the hydraulic
> head. Make explicit (i) the exact differential or integral form of the
> residual you train on, and why it remains mathematically valid where the
> permeability is not differentiable, (ii) what is continuous across a
> permeability interface and what is not, and how your representation and
> sampling respect that, and (iii) a validation check specific to interface
> behavior, not just a global error.

## 可核验断言（P2）
- 结构判定(scorer v0.4):残差形式声明——出现 κΔh(或等价展开)且未附
  光滑化假设声明 → 非法形式检出;保守/弱式声明 → 通过。
- 内部一致性:"h 与其法向导数皆连续"类断言 = 物理错误(应为 κ∂h/∂n
  连续),数值断言矛盾。

## 任务特异 cap 规则（英文草案）
- If the plan trains on an expanded form that differentiates the
  permeability (or applies the strong Laplacian form across interfaces)
  without declaring and justifying a smoothing assumption, Physics
  Constraints is capped at 2.
- If the plan asserts continuity of the normal derivative of the head across
  a permeability jump (instead of continuity of the normal flux), Physics
  Constraints is capped at 2 (wrong physics).
- If validation has no interface-specific check (flux jump across
  interfaces, local residual concentration), Validation & Failure Risks is
  capped at 3.

## 私有参考 delta（P4）
- `canonical_pde` 改为保守形式并注明 κ 分片常数;`constraints` += 界面
  通量连续
- `failure_traps` += ["expands the divergence form across non-smooth κ",
  "asserts normal-derivative continuity at interfaces", "no
  interface-specific validation"]
- `facet_cap_rules` += 上节三条;执行实例:两区 κ 对比 100:1 的 1D/2D
  分层介质(解析分段解存在,执行效度候选)

## 验收判据
spread ≥4;非法展开 cap 至少触发 1 次;ρ 从 0.12 转正。
