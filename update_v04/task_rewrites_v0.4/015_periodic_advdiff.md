# medium_periodic_advdiff_015 重写规格（草案，评分器侧为主）

## 诊断（v0.3）
spread 2 / ρ 0.66。特殊案例：**题面已经很锋利**（明确要求"state exactly
which endpoint constraints are needed for a diffusive transport equation"），
rubric 的 trap 也已存在（值周期 vs 值+导数双周期,cap 至 3/2）,且是全基准
仅有的两处 hard-trap 触发之一（2 次）。但仍饱和——因为 cue 检测认"提到
derivative periodicity"这个词组,模型集体学会了提词。

## 决议：题面轻改 + trap 从 cue 检测升级为断言核验

支点不变（扩散项要求解与通量在端点同时同一：u(0)=u(L) 且 u_x(0)=u_x(L)）。
修复在检测机制:计划必须**枚举**它施加的端点约束集合,scorer v0.4 对枚举
做完备性核验（两条都在 → 通过;只有值周期 → cap;声称"周期嵌入自动满足
全部" → 需说明嵌入对导数的作用,否则 cap 3）。

## 题面增量（英文草案,末句替换）
> ...Design a physics-informed modeling workflow. Enumerate, as an explicit
> list, every endpoint constraint your workflow enforces, and for each one
> state whether it is enforced softly (as a penalty), by construction (via
> the representation), or not at all — and why the diffusive term makes the
> list you chose sufficient.

## 可核验断言（P2）
- 枚举完备性:约束列表 ⊇ {值同一, 一阶导/通量同一}——列表式输出是为
  机器核验设计的题面结构（本重写的方法论创新点,可推广到其他题的
  "显式承诺"设计）。
- 周期嵌入声明:若用 sin/cos 特征嵌入并声称由构造满足,该声明对 C¹ 同一
  成立（可判真）;若用截断傅里叶+输出层非线性,声明"自动满足所有导数
  周期"为真;若声称硬编码但网络结构描述与之矛盾 → 断言矛盾。

## cap 规则（继承 v0.3 两条,判定方式升级）
- 文字不变（value-only → PC/TS cap 2;忽略导数/通量周期 → 3）;
  触发条件从"未提到词组"改为"枚举列表缺失该约束且无构造性论证"。

## 私有参考 delta（P4）
- `critical_points.physics_constraints` 改为枚举式(两条约束分列)
- `expected_loss_terms` 标注"或由周期嵌入构造性满足（此时无此损失项,
  需在 Model Choice 声明）"——消除"用嵌入反被扣损失项"的误伤路径

## 验收判据
spread ≥4;trap 触发次数上升且触发理由从词组缺席变为枚举不完备
（评分理由字段可查——这是 trap 机制升级的可展示证据）。
