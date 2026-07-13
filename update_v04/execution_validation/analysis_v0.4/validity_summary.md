# 执行效度分析（v0.4）

输入：150 条 run，臂级聚合后 50 臂 / 5 题；发散 run 比例 0.000。

## H4a 主检验（仅 N1–N6 + G + T；预注册判定：CI 上界 < 0）

| task                                 |   n_arms |       rho |        p | note   |
|:-------------------------------------|---------:|----------:|---------:|:-------|
| easy_advection_1d_periodic_005       |        8 |  0.527282 | 0.179309 |        |
| easy_poisson_2d_source_003           |        8 | -0.228932 | 0.585514 |        |
| hard_allen_cahn_016                  |        8 | -0.610853 | 0.107674 |        |
| hard_plus_euler_shock_023            |        8 | -0.370035 | 0.366917 |        |
| medium_burgers_inverse_viscosity_010 |        8 | -0.204834 | 0.626544 |        |

跨任务平均 ρ = -0.177，bootstrap 95% CI [-0.480, 0.200]；方向一致（ρ<0）任务 4/5。

预注册判定：**未证实 H4a**（CI 上界 ≥ 0，如实报告，不做事后子集挑选）

### 次要报告：全臂版本（含 D 臂，循环论证风险，仅作参考）

| task                                 |   n_arms |       rho |        p | note   |
|:-------------------------------------|---------:|----------:|---------:|:-------|
| easy_advection_1d_periodic_005       |       10 |  0.445874 | 0.196519 |        |
| easy_poisson_2d_source_003           |       10 |  0.116564 | 0.748452 |        |
| hard_allen_cahn_016                  |       10 | -0.539751 | 0.107315 |        |
| hard_plus_euler_shock_023            |       10 | -0.415025 | 0.233011 |        |
| medium_burgers_inverse_viscosity_010 |       10 | -0.536595 | 0.10979  |        |

全臂跨任务平均 ρ = -0.186，CI [-0.451, 0.128]

## H4b 消融配对检验（ablation − parent，预期 Δ>0）

| task                                 | ablation   |   n_seeds |   median_delta_log10 |   wilcoxon_p |
|:-------------------------------------|:-----------|----------:|---------------------:|-------------:|
| easy_advection_1d_periodic_005       | D1         |         3 |          2.09488     |          nan |
| easy_advection_1d_periodic_005       | D3         |         3 |          2.15251     |          nan |
| easy_poisson_2d_source_003           | D1         |         3 |          5.71479     |          nan |
| easy_poisson_2d_source_003           | D3         |         3 |          5.55949     |          nan |
| hard_allen_cahn_016                  | D1         |         3 |         -0.0118128   |          nan |
| hard_allen_cahn_016                  | D3         |         3 |         -5.85394e-05 |          nan |
| hard_plus_euler_shock_023            | D1         |         3 |          0.437267    |          nan |
| hard_plus_euler_shock_023            | D3         |         3 |          0.121506    |          nan |
| medium_burgers_inverse_viscosity_010 | D1         |         3 |          0.629403    |          nan |
| medium_burgers_inverse_viscosity_010 | D2         |         3 |          0.721729    |          nan |

合并配对 n=30，Wilcoxon 单侧 p = 2.3562461137771606e-07

## H4c capped vs uncapped（臂级）

{'n_capped': 4, 'n_uncapped': 46, 'median_capped': -0.7419336418564779, 'median_uncapped': -1.0285587651099792, 'mannwhitney_p': 0.32738359108355636}

## 010 反问题 ν 恢复（|ν̂−ν|/ν，种子中位数）

| arm   | kind     |   plan_score |   nu_rel_err_median |   log_rel_l2 |
|:------|:---------|-------------:|--------------------:|-------------:|
| N2    | natural  |           22 |            0.555609 |    -1.6112   |
| N5    | natural  |           22 |            0.555705 |    -1.61111  |
| N4    | natural  |           19 |            0.561553 |    -1.60526  |
| N3    | natural  |           23 |            2.22565  |    -1.12024  |
| N6    | natural  |           24 |            2.24339  |    -1.11685  |
| G     | gold     |           23 |            2.32271  |    -1.10481  |
| N1    | natural  |           21 |            2.61578  |    -1.07228  |
| D1    | ablation |           20 |           20.597    |    -0.475129 |
| D2    | ablation |           17 |           30.4159   |    -0.383187 |
| T     | template |           15 |           51.7782   |    -0.268268 |

## 辅助：facet 级任务内相关（仅 N+G+T；预期 Physics Constraints / Training Strategy 最强）

| facet                    |   n_tasks |   mean_rho |
|:-------------------------|----------:|-----------:|
| Validation Failure Risks |         5 |  -0.222704 |
| Problem Formalization    |         5 |  -0.186688 |
| Model Choice             |         5 |  -0.148663 |
| Physics Constraints      |         5 |  -0.085022 |
| Training Strategy        |         5 |  -0.08396  |
