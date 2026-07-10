# hard_helmholtz_high_frequency_020 重写规格（草案，轻改）

## 诊断（v0.3）
spread 4 / ρ 0.26;VR 满分率 1.00。rubric 已有 trap(架构名词无 PPW/复数/
相位细节 → cap 3)但零触发——"points per wavelength"作为词组出现即放行,
没人被要求给出**数**并保证数与频率、域尺寸自洽。

## 决策支点（P1，保持,判定升级）
高频可解性的定量论证:域跨约 N 个波长(题面公开给出量级,如"roughly
twenty wavelengths across the domain"——量级公开不泄私有实例),则表示
容量与采样密度都必须按波长计:每波长采样点数 × 波长数 = 总点数,
Fourier 特征带宽 σ 与 k 匹配。支点从"提到 PPW"升级为"给出的数自洽"。

## 题面增量（英文草案,插入两句）
> ...The wavelength is short relative to the domain size — the domain spans
> roughly twenty wavelengths in each direction — and both phase and
> amplitude accuracy matter. ... Quantify your sampling in points per
> wavelength and show the resulting total budget is consistent with the
> stated domain-to-wavelength ratio; a named architecture without this
> arithmetic is not sufficient.

## 可核验断言（P2，scorer v0.4 内部一致性检查的旗舰案例）
- 声称 PPW = p、域跨 N≈20 波长、总配点 M → 校验 M ≳ (p·N)^d(2D 下
  d=2)。三个数全由计划给出,算术矛盾即检出——不依赖私有值。
- 复数表述:声称"real-valued network"同时要求相位精度 → 结构矛盾
  (v0.3 trap 文字已有,升级为共现判定)。

## cap 规则（v0.3 三条保留,判定升级 + 新增一条）
- 新增:If the plan states a points-per-wavelength figure, a
  domain-to-wavelength ratio, and a total collocation budget that are
  mutually inconsistent by more than an order of magnitude, Training
  Strategy is capped at 3 (unverified quantitative claim)。
- 既有三条(架构名词无细节/时域化/实值无相位处理)触发方式改为断言核验。

## 私有参考 delta（P4）
- `parameter_values` 公开量级(≈20 波长)与私有精确 k 分离记录
- `critical_points.training_strategy` 改为算术三元组(PPW/波长数/总点数)
- `failure_traps` += ["PPW arithmetic inconsistent", "real-only network with
  phase accuracy claim"]

## 验收判据
spread 维持 ≥4 且 ρ 从 0.26 上升;PPW-算术 cap 至少触发 1 次;VR 满分率
1.00 → <0.3。
