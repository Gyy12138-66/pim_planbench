# easy_laplace_2d_boundary_007 → 重定位为 L 形域凹角问题（草案）

## 诊断（v0.3）
spread 4 / ρ 0.35；TS 满分率 1.00、MC 0.83。与 003 同为"2D 椭圆 + 矩形 +
Dirichlet"槽位，功能重复；矩形上的 Laplace 无任何任务特异决策可考。

## 重定位决策
不砍。改为 **L 形域（凹角）Laplace/Poisson**——科学计算最经典的奇异性
基准：凹角处解 u ~ r^{2/3}sin(2θ/3)，导数在角点无界。有精确解析参考
（分数幂调和函数），执行也便宜（2D、小域），未来可进执行效度轮次。
难度标签建议从 easy 调整为 medium（凹角奇异不是 easy 内容——这同时
服务难度轴的重建）。

## 决策支点（P1）
凹角奇异性的处理是二元决策：光滑 MLP + 均匀采样在 r^{2/3} 奇异附近既逼近
不好也采样不足；计划必须选择一种机制（角点局部加密/奇异富集基底/分域/
梯度加权）并说明为什么普通谱偏置网络在角点失效。

## 新公开题面（英文草案）
> An engineer needs the steady-state potential field in a two-dimensional
> L-shaped region (a square with one quadrant removed). There are no internal
> sources, and Dirichlet values are prescribed on the whole boundary. Note
> that the re-entrant corner makes the exact solution non-smooth: its
> gradient is unbounded at that corner. Design a physics-informed modeling
> workflow for this boundary value problem. Explain how your representation
> and sampling treat the corner singularity, why a standard smooth network
> trained on uniform collocation may fail there, and how you will measure
> solution quality near the corner separately from the rest of the domain.

## 可核验断言（P2）
- 内部一致性：声称的角点邻域加密倍数/富集函数形式 r^{α} 的 α 与凹角开角
  2π·(3/4)→ α=2/3 的匹配（说错指数即数值断言矛盾，scorer v0.4 可对账）。
- 规格对账：私有参考含精确解 u = r^{2/3}sin(2θ/3)（或其边界数据），角点
  邻域误差单独报告。

## 任务特异 cap 规则（英文草案）
- If the plan treats the domain as smooth and applies uniform collocation
  with a plain MLP without any corner-specific mechanism, Model Choice and
  Training Strategy are capped at 2.
- If the plan states a corner-singularity exponent inconsistent with the
  re-entrant angle, affected facets are capped at 2 (hallucinated
  specification).
- If validation reports only a global error metric with no corner-local
  assessment, Validation & Failure Risks is capped at 3.

## 私有参考 delta（P4）
- 全字段重建：canonical_pde（Laplace）、domain_spec（L 形）、
  analytic_solution（r^{2/3}sin(2θ/3)）、reference_conditions（相应边界值）
- `failure_traps` = 上面三条 cap 的触发行为
- `public_metadata.difficulty`: easy → medium；id 建议保留 007 编号加后缀
  （`medium_laplace_L_corner_007r`），旧题面归档

## 验收判据
spread ≥4；角点 cap 至少触发 1 次；与 003 的模型排名相关度下降（解耦证据）。
