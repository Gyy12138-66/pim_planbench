# hard_cahn_hilliard_017 重写规格（草案）

## 诊断（v0.3）
spread 2 / ρ 0.15;TS/PC 满分率双双 1.00,均分 23.2（全基准第二高）——
一道 hard 题成了送分题。rubric 的任务特异 trap（μ-分裂、质量守恒、直接
四阶封顶 4）写得很好但**零触发**:模型都会说"introduce chemical potential
μ"这个词,cue 检测就放行了;没人被检查是否真的把 μ 作为网络输出/独立
残差,还是嘴上提 μ、损失里仍然直接写四阶导数。

## 决策支点（P1）
**μ-分裂的结构性承诺**:把 C-H 写成耦合二阶系统 u_t = ∇·(M∇μ),
μ = f'(u) − ε²Δu,要求网络输出（或辅助网络）显式包含 μ,残差是两条
二阶方程——versus 单输出 u 的直接四阶残差（autograd 代价高、训练病态）。
这是从 Model Choice 文本可机器判定的结构决策:声明的网络输出集合与声明的
残差集合必须自洽（提了 μ 但输出只有 u 且残差只有一条四阶 → 口头 μ）。

## 新公开题面（英文草案）
> A researcher wants to model a conserved phase-field process governed by a
> Cahn-Hilliard-type equation. The order parameter evolves through a
> chemical-potential-driven mechanism, total phase mass must not drift, and
> sharp interfaces may form. Design a physics-informed modeling workflow.
> Specify precisely (i) the complete list of fields your network(s) output,
> (ii) the complete list of residual equations you train on, written so that
> the derivative order of each residual is unambiguous, and (iii) how mass
> conservation is monitored quantitatively over the simulated horizon. If
> you train directly on the fourth-order form, justify the differentiation
> cost and conditioning consequences explicitly.

## 可核验断言（P2）
- 结构自洽（scorer v0.4 核心检查）:输出字段集合 × 残差方程集合 → 若文本
  提及 μ 但输出集合不含 μ 且残差只有单条四阶 → "口头 μ"检出,trap 触发;
  若承诺分裂,两条残差的导数阶数声明应均 ≤2。
- 质量守恒:声称的守恒监控必须带漂移阈值(数值断言)。

## cap 规则（v0.3 三条保留,判定升级 + 一条新增）
- 既有:C-H 当 A-C → 2;无 μ/四阶负担处理 → 3;直接四阶最高 4;
  无质量守恒 → 2;无自由能/长时漂移验证 → 4。
- 新增:If the plan invokes the chemical potential verbally but the declared
  network outputs and residual list do not contain it (and the residual
  remains a single fourth-order equation), Model Choice and Training
  Strategy are capped at 3 (nominal-splitting trap)。
- P3（预算）:题面可选加步数/自动微分预算,使直接四阶的代价成为显式取舍
  ——建议加(与 004/021 的预算机制一致)。

## 私有参考 delta（P4）
- `critical_points.model_choice` 改为结构化:输出集合、残差集合、阶数
- `failure_traps` += ["nominal chemical potential (mentioned but not an
  output/residual)", "conservation claimed without drift tolerance"]
- `facet_cap_rules` += 新增条;执行实例:1D C-H,谱参考(016 基建复用)
  ——本题重写后是执行效度第二轮的优质候选(检验 μ-分裂 vs 直接四阶的
  真实执行差,支点的因果证据)

## 验收判据
spread ≥4;nominal-splitting cap 至少触发 1 次;TS/PC 满分率 1.00 → <0.2;
均分从 23.2 显著下降。
