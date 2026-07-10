# hard_plus_helmholtz_staircase_021 重写规格（草案）

## 诊断（v0.3）
spread 1 / MC 满分率 1.00——**全基准最失败的题之一**:hard_plus 难度、
六模型 21–22 分挤在一起。题面问"why a standard PINN may or may not be
sufficient"是开放论述题,论述题喂给语言模型 = 人人满分。无任务特异 cap。

## 决策支点（P1）
两支点叠加,并用预算逼出取舍(P3):
1. **凹角奇异性**(staircase 的每个内角都是 r^{2/3} 型奇异——与 007r
   同机制但叠加高频):全局光滑表示在角点集体失效;需要角点局部处理
   (分域/富集/加密)。
2. **高频 × 几何的预算分配**:域跨多个波长 + 多个角点,固定预算下
   "全局特征带宽"与"角点局部加密"竞争采样点——必须给出分配论证。
   (与 020 的 PPW 算术、007r 的角奇异形成支点家族,但组合难度独立。)

## 新公开题面（英文草案）
> A researcher must solve a frequency-domain Helmholtz problem in a
> two-dimensional staircase-shaped domain: the boundary consists of many
> axis-aligned steps, so the domain has multiple re-entrant corners, and the
> domain spans roughly ten wavelengths. Source and boundary data are known.
> The compute budget is fixed: at most 40,000 collocation points and one
> network (or an explicitly justified decomposition). Design a
> physics-informed modeling workflow. Required content: (i) how the solution
> behaves at re-entrant corners and what your representation does about it,
> (ii) the points-per-wavelength arithmetic for the oscillatory bulk, (iii)
> how the fixed point budget is split between corner refinement and bulk
> coverage, with numbers, and (iv) a validation plan that reports corner
> neighborhoods separately from the bulk.

## 可核验断言（P2）
- 角奇异指数:凹角 3π/2 → 指数 2/3;说错 → 数值断言矛盾(与 007r 共用
  核验代码)。
- 预算算术:角点数 × 每角加密点数 + PPW×波长数² ≤ 40,000——全部数字由
  计划给出,内部一致性可查(020 机制的推广)。

## 任务特异 cap 规则（英文草案）
- If the plan applies a single smooth network with uniform collocation and
  no corner-specific mechanism, Model Choice and Training Strategy are
  capped at 2.
- If the plan discusses spectral bias or Fourier features for the
  oscillatory bulk but never addresses the corner singularities (or vice
  versa), affected facets are capped at 3 (one-sided difficulty handling).
- If the stated budget split is absent or arithmetically inconsistent with
  the stated budget, Training Strategy is capped at 3.
- If validation reports only a global metric, Validation & Failure Risks is
  capped at 3.

## 私有参考 delta（P4）
- `domain_spec`:阶梯几何参数化(阶数、波长比)公开量级/私有精确值分离
- `failure_traps` += 四条 cap 的触发行为;`critical_points` 全 facet 重写
  (角奇异 + PPW + 预算分配三线并列)
- 参考解:分域谱/边界积分法离线算一次(私有);执行效度轮次可选缩小版
  (两阶阶梯)

## 验收判据
spread 1 → ≥4(本题是重写成效的最强指示器);双侧困难 cap 至少触发 1 次;
MC 满分率 1.00 → <0.2。
