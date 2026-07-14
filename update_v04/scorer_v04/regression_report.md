# 评分器 v0.4 回归套件报告

**结论：全部通过**

## 55 臂明细（v0.3 总分 vs v0.4 cap 后总分）

| task                                 | arm                           | kinds                 |   n_findings |   v03 |   v04 | capped_facets                      |
|:-------------------------------------|:------------------------------|:----------------------|-------------:|------:|------:|:-----------------------------------|
| easy_advection_1d_periodic_005       | D1                            | -                     |            0 |    19 |    19 | -                                  |
| easy_advection_1d_periodic_005       | D2                            | wrong_task_type       |            1 |    24 |    19 | Model Choice|Problem Formalization |
| easy_advection_1d_periodic_005       | D3                            | numeric_contradiction |            1 |    25 |    22 | Problem Formalization              |
| easy_advection_1d_periodic_005       | G                             | -                     |            0 |    25 |    25 | -                                  |
| easy_advection_1d_periodic_005       | Pro/moonshotai/Kimi-K2.6      | -                     |            0 |    24 |    24 | -                                  |
| easy_advection_1d_periodic_005       | Pro/zai-org/GLM-4.7           | -                     |            0 |    19 |    19 | -                                  |
| easy_advection_1d_periodic_005       | Pro/zai-org/GLM-5.1           | -                     |            0 |    19 |    19 | -                                  |
| easy_advection_1d_periodic_005       | T                             | -                     |            0 |    17 |    17 | -                                  |
| easy_advection_1d_periodic_005       | deepseek-ai/DeepSeek-V4-Flash | -                     |            0 |    20 |    20 | -                                  |
| easy_advection_1d_periodic_005       | deepseek/deepseek-v4-pro      | -                     |            0 |    22 |    22 | -                                  |
| easy_advection_1d_periodic_005       | qwen/qwen3.7-max              | -                     |            0 |    20 |    20 | -                                  |
| easy_poisson_2d_source_003           | D1                            | -                     |            0 |    22 |    22 | -                                  |
| easy_poisson_2d_source_003           | D2                            | wrong_task_type       |            1 |    25 |    19 | Model Choice|Problem Formalization |
| easy_poisson_2d_source_003           | D3                            | numeric_contradiction |            1 |    25 |    22 | Problem Formalization              |
| easy_poisson_2d_source_003           | G                             | -                     |            0 |    25 |    25 | -                                  |
| easy_poisson_2d_source_003           | Pro/moonshotai/Kimi-K2.6      | -                     |            0 |    24 |    24 | -                                  |
| easy_poisson_2d_source_003           | Pro/zai-org/GLM-4.7           | -                     |            0 |    18 |    18 | -                                  |
| easy_poisson_2d_source_003           | Pro/zai-org/GLM-5.1           | -                     |            0 |    22 |    22 | -                                  |
| easy_poisson_2d_source_003           | T                             | -                     |            0 |    19 |    19 | -                                  |
| easy_poisson_2d_source_003           | deepseek-ai/DeepSeek-V4-Flash | -                     |            0 |    21 |    21 | -                                  |
| easy_poisson_2d_source_003           | deepseek/deepseek-v4-pro      | -                     |            0 |    20 |    20 | -                                  |
| easy_poisson_2d_source_003           | qwen/qwen3.7-max              | -                     |            0 |    23 |    23 | -                                  |
| hard_allen_cahn_016                  | D1                            | -                     |            0 |    24 |    24 | -                                  |
| hard_allen_cahn_016                  | D2                            | wrong_task_type       |            1 |    24 |    19 | Model Choice|Problem Formalization |
| hard_allen_cahn_016                  | D3                            | numeric_contradiction |            1 |    25 |    22 | Problem Formalization              |
| hard_allen_cahn_016                  | G                             | -                     |            0 |    25 |    25 | -                                  |
| hard_allen_cahn_016                  | Pro/moonshotai/Kimi-K2.6      | -                     |            0 |    22 |    22 | -                                  |
| hard_allen_cahn_016                  | Pro/zai-org/GLM-4.7           | -                     |            0 |    19 |    19 | -                                  |
| hard_allen_cahn_016                  | Pro/zai-org/GLM-5.1           | -                     |            0 |    22 |    22 | -                                  |
| hard_allen_cahn_016                  | T                             | -                     |            0 |    17 |    17 | -                                  |
| hard_allen_cahn_016                  | deepseek-ai/DeepSeek-V4-Flash | -                     |            0 |    23 |    23 | -                                  |
| hard_allen_cahn_016                  | deepseek/deepseek-v4-pro      | -                     |            0 |    22 |    22 | -                                  |
| hard_allen_cahn_016                  | qwen/qwen3.7-max              | -                     |            0 |    18 |    18 | -                                  |
| hard_plus_euler_shock_023            | D1                            | -                     |            0 |    20 |    20 | -                                  |
| hard_plus_euler_shock_023            | D2                            | wrong_task_type       |            1 |    23 |    18 | Model Choice|Problem Formalization |
| hard_plus_euler_shock_023            | D3                            | numeric_contradiction |            1 |    23 |    21 | Problem Formalization              |
| hard_plus_euler_shock_023            | G                             | -                     |            0 |    23 |    23 | -                                  |
| hard_plus_euler_shock_023            | Pro/moonshotai/Kimi-K2.6      | -                     |            0 |    23 |    23 | -                                  |
| hard_plus_euler_shock_023            | Pro/zai-org/GLM-4.7           | -                     |            0 |    15 |    15 | -                                  |
| hard_plus_euler_shock_023            | Pro/zai-org/GLM-5.1           | -                     |            0 |    23 |    23 | -                                  |
| hard_plus_euler_shock_023            | T                             | -                     |            0 |    10 |    10 | -                                  |
| hard_plus_euler_shock_023            | deepseek-ai/DeepSeek-V4-Flash | -                     |            0 |    22 |    22 | -                                  |
| hard_plus_euler_shock_023            | deepseek/deepseek-v4-pro      | -                     |            0 |    19 |    19 | -                                  |
| hard_plus_euler_shock_023            | qwen/qwen3.7-max              | -                     |            0 |    23 |    23 | -                                  |
| medium_burgers_inverse_viscosity_010 | D1                            | -                     |            0 |    20 |    20 | -                                  |
| medium_burgers_inverse_viscosity_010 | D2                            | wrong_task_type       |            3 |    17 |    15 | Model Choice|Problem Formalization |
| medium_burgers_inverse_viscosity_010 | D3                            | fabricated_component  |            1 |    23 |    20 | Physics Constraints                |
| medium_burgers_inverse_viscosity_010 | G                             | -                     |            0 |    23 |    23 | -                                  |
| medium_burgers_inverse_viscosity_010 | Pro/moonshotai/Kimi-K2.6      | -                     |            0 |    21 |    21 | -                                  |
| medium_burgers_inverse_viscosity_010 | Pro/zai-org/GLM-4.7           | -                     |            0 |    22 |    22 | -                                  |
| medium_burgers_inverse_viscosity_010 | Pro/zai-org/GLM-5.1           | -                     |            0 |    23 |    23 | -                                  |
| medium_burgers_inverse_viscosity_010 | T                             | -                     |            0 |    15 |    15 | -                                  |
| medium_burgers_inverse_viscosity_010 | deepseek-ai/DeepSeek-V4-Flash | -                     |            0 |    19 |    19 | -                                  |
| medium_burgers_inverse_viscosity_010 | deepseek/deepseek-v4-pro      | -                     |            0 |    22 |    22 | -                                  |
| medium_burgers_inverse_viscosity_010 | qwen/qwen3.7-max              | -                     |            0 |    24 |    24 | -                                  |

## R6 堆砌臂（S1/S2 × 25 题 × claim_verifier_v04）

矛盾类检出 0/50（门）；有检出的臂如下（support 类 = claim_without_support，属正当遏制记录）：

| task                   | arm   |   contradiction |   support | kinds             |
|:-----------------------|:------|----------------:|----------:|:------------------|
| hard_cahn_hilliard_017 | S2    |               0 |         1 | unsupported_claim |

## 判据

R1 D3 数值篡改检出（003/005/016/023）；R2 D3 幻觉组件检出（010）；
R3 D2 任务类型检出（5 题）；R4 G/T/N/D1 零误伤；R5 cap 后 D2/D3 < G；
R6 S1/S2 堆砌臂矛盾类零检出（support 类计数入报告）。
