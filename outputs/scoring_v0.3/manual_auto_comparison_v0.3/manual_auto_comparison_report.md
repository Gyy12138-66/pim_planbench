# Manual vs Auto Score Comparison v0.3

Positive `diff_mean_human_minus_auto` means the manual score is higher than the automatic score.
Variance columns use sample variance; singleton groups use 0.000.

## Inputs

- `/Users/0x47/Desktop/pim_planbench/outputs/scoring_v0.3/manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx`
- `/Users/0x47/Desktop/pim_planbench/outputs/scoring_v0.3/manual_scoring_selected_02_03_15_22_23_24_v0.3_compare.xlsx`
- auto score CSV: `scores/pilot_v0.3/3ModelOutput_scored.csv`

## Overall

| n_rows | n_compared | missing_manual | missing_auto | human_mean | auto_mean | diff_mean_human_minus_auto | abs_diff_mean | exact_match_rate | within_0_5_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 180 | 180 | 0 | 0 | 4.381 | 4.456 | -0.075 | 0.386 | 0.406 | 0.828 |

## By Manual Workbook

| manual_file | n_rows | n_compared | missing_manual | missing_auto | human_mean | human_variance | auto_mean | auto_variance | diff_mean_human_minus_auto | diff_variance | abs_diff_mean | abs_diff_max | exact_match_rate | within_0_5_rate | within_1_0_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | 90 | 90 | 0 | 0 | 4.228 | 0.271 | 4.511 | 0.455 | -0.283 | 0.242 | 0.406 | 1.500 | 0.411 | 0.789 | 0.989 |
| manual_scoring_selected_02_03_15_22_23_24_v0.3_compare.xlsx | 90 | 90 | 0 | 0 | 4.533 | 0.269 | 4.400 | 0.467 | 0.133 | 0.235 | 0.367 | 1.000 | 0.400 | 0.867 | 1.000 |

## By Facet

| facet | n_rows | n_compared | missing_manual | missing_auto | human_mean | human_variance | auto_mean | auto_variance | diff_mean_human_minus_auto | diff_variance | abs_diff_mean | abs_diff_max | exact_match_rate | within_0_5_rate | within_1_0_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model Choice | 36 | 36 | 0 | 0 | 4.347 | 0.312 | 4.472 | 0.542 | -0.125 | 0.248 | 0.375 | 1.000 | 0.389 | 0.861 | 1.000 |
| Physics Constraints | 36 | 36 | 0 | 0 | 4.278 | 0.435 | 4.222 | 0.463 | 0.056 | 0.311 | 0.389 | 1.000 | 0.444 | 0.778 | 1.000 |
| Problem Formalization | 36 | 36 | 0 | 0 | 4.569 | 0.145 | 4.889 | 0.102 | -0.319 | 0.174 | 0.375 | 1.000 | 0.417 | 0.833 | 1.000 |
| Training Strategy | 36 | 36 | 0 | 0 | 4.375 | 0.263 | 4.444 | 0.483 | -0.069 | 0.288 | 0.375 | 1.000 | 0.444 | 0.806 | 1.000 |
| Validation Failure Risks | 36 | 36 | 0 | 0 | 4.333 | 0.286 | 4.250 | 0.479 | 0.083 | 0.307 | 0.417 | 1.500 | 0.333 | 0.861 | 0.972 |

## By Model

| model | n_rows | n_compared | missing_manual | missing_auto | human_mean | human_variance | auto_mean | auto_variance | diff_mean_human_minus_auto | diff_variance | abs_diff_mean | abs_diff_max | exact_match_rate | within_0_5_rate | within_1_0_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pro/moonshotai/Kimi-K2.6 | 60 | 60 | 0 | 0 | 4.525 | 0.173 | 4.650 | 0.231 | -0.125 | 0.200 | 0.325 | 1.000 | 0.450 | 0.900 | 1.000 |
| Pro/zai-org/GLM-4.7 | 60 | 60 | 0 | 0 | 4.167 | 0.412 | 4.217 | 0.613 | -0.050 | 0.404 | 0.483 | 1.000 | 0.350 | 0.683 | 1.000 |
| deepseek-ai/DeepSeek-V4-Flash | 60 | 60 | 0 | 0 | 4.450 | 0.226 | 4.500 | 0.458 | -0.050 | 0.243 | 0.350 | 1.500 | 0.417 | 0.900 | 0.983 |

## By Facet And Model

| facet | model | n_rows | n_compared | missing_manual | missing_auto | human_mean | human_variance | auto_mean | auto_variance | diff_mean_human_minus_auto | diff_variance | abs_diff_mean | abs_diff_max | exact_match_rate | within_0_5_rate | within_1_0_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model Choice | Pro/moonshotai/Kimi-K2.6 | 12 | 12 | 0 | 0 | 4.542 | 0.157 | 4.583 | 0.265 | -0.042 | 0.203 | 0.292 | 1.000 | 0.500 | 0.917 | 1.000 |
| Model Choice | Pro/zai-org/GLM-4.7 | 12 | 12 | 0 | 0 | 3.875 | 0.369 | 4.000 | 0.909 | -0.125 | 0.460 | 0.542 | 1.000 | 0.250 | 0.667 | 1.000 |
| Model Choice | deepseek-ai/DeepSeek-V4-Flash | 12 | 12 | 0 | 0 | 4.625 | 0.097 | 4.833 | 0.152 | -0.208 | 0.112 | 0.292 | 0.500 | 0.417 | 1.000 | 1.000 |
| Physics Constraints | Pro/moonshotai/Kimi-K2.6 | 12 | 12 | 0 | 0 | 4.500 | 0.182 | 4.417 | 0.265 | 0.083 | 0.356 | 0.417 | 1.000 | 0.417 | 0.750 | 1.000 |
| Physics Constraints | Pro/zai-org/GLM-4.7 | 12 | 12 | 0 | 0 | 4.083 | 0.674 | 4.000 | 0.545 | 0.083 | 0.492 | 0.500 | 1.000 | 0.417 | 0.583 | 1.000 |
| Physics Constraints | deepseek-ai/DeepSeek-V4-Flash | 12 | 12 | 0 | 0 | 4.250 | 0.432 | 4.250 | 0.568 | 0.000 | 0.136 | 0.250 | 0.500 | 0.500 | 1.000 | 1.000 |
| Problem Formalization | Pro/moonshotai/Kimi-K2.6 | 12 | 12 | 0 | 0 | 4.667 | 0.106 | 5.000 | 0.000 | -0.333 | 0.106 | 0.333 | 1.000 | 0.417 | 0.917 | 1.000 |
| Problem Formalization | Pro/zai-org/GLM-4.7 | 12 | 12 | 0 | 0 | 4.417 | 0.174 | 4.750 | 0.205 | -0.333 | 0.333 | 0.500 | 1.000 | 0.333 | 0.667 | 1.000 |
| Problem Formalization | deepseek-ai/DeepSeek-V4-Flash | 12 | 12 | 0 | 0 | 4.625 | 0.142 | 4.917 | 0.083 | -0.292 | 0.112 | 0.292 | 1.000 | 0.500 | 0.917 | 1.000 |
| Training Strategy | Pro/moonshotai/Kimi-K2.6 | 12 | 12 | 0 | 0 | 4.542 | 0.157 | 4.750 | 0.205 | -0.208 | 0.157 | 0.292 | 1.000 | 0.500 | 0.917 | 1.000 |
| Training Strategy | Pro/zai-org/GLM-4.7 | 12 | 12 | 0 | 0 | 4.167 | 0.424 | 4.167 | 0.697 | 0.000 | 0.364 | 0.417 | 1.000 | 0.417 | 0.750 | 1.000 |
| Training Strategy | deepseek-ai/DeepSeek-V4-Flash | 12 | 12 | 0 | 0 | 4.417 | 0.174 | 4.417 | 0.447 | 0.000 | 0.364 | 0.417 | 1.000 | 0.417 | 0.750 | 1.000 |
| Validation Failure Risks | Pro/moonshotai/Kimi-K2.6 | 12 | 12 | 0 | 0 | 4.375 | 0.278 | 4.500 | 0.273 | -0.125 | 0.142 | 0.292 | 0.500 | 0.417 | 1.000 | 1.000 |
| Validation Failure Risks | Pro/zai-org/GLM-4.7 | 12 | 12 | 0 | 0 | 4.292 | 0.384 | 4.167 | 0.515 | 0.125 | 0.369 | 0.458 | 1.000 | 0.333 | 0.750 | 1.000 |
| Validation Failure Risks | deepseek-ai/DeepSeek-V4-Flash | 12 | 12 | 0 | 0 | 4.333 | 0.242 | 4.083 | 0.629 | 0.250 | 0.386 | 0.500 | 1.500 | 0.250 | 0.833 | 0.917 |

## Largest Absolute Differences

| manual_file | task_id | model_display | facet | human_score | auto_score | manual_minus_auto | abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | DeepSeek-V4-Flash | Validation Failure Risks | 4.5 | 3 | 1.5 | 1.5 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | Kimi-K2.6 | Physics Constraints | 5 | 4 | 1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | GLM-4.7 | Physics Constraints | 3 | 4 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | GLM-4.7 | Model Choice | 3 | 4 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | Kimi-K2.6 | Training Strategy | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | easy_heat_1d_dirichlet_001 | GLM-4.7 | Training Strategy | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_heat_inverse_alpha_009 | GLM-4.7 | Model Choice | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_heat_inverse_alpha_009 | DeepSeek-V4-Flash | Training Strategy | 4 | 3 | 1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | DeepSeek-V4-Flash | Problem Formalization | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | Kimi-K2.6 | Problem Formalization | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | GLM-4.7 | Problem Formalization | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | Kimi-K2.6 | Model Choice | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | GLM-4.7 | Model Choice | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | medium_wave_sparse_sensors_012 | DeepSeek-V4-Flash | Validation Failure Risks | 4 | 3 | 1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | hard_cahn_hilliard_017 | GLM-4.7 | Problem Formalization | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | hard_cahn_hilliard_017 | GLM-4.7 | Physics Constraints | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | hard_cahn_hilliard_017 | DeepSeek-V4-Flash | Training Strategy | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | hard_cahn_hilliard_017 | GLM-4.7 | Training Strategy | 4 | 5 | -1 | 1 |
| manual_scoring_selected_01_09_12_17_20_25_v0.3_compare.xlsx | hard_helmholtz_high_frequency_020 | GLM-4.7 | Problem Formalization | 4 | 5 | -1 | 1 |
| manual_scoring_selected_02_03_15_22_23_24_v0.3_compare.xlsx | easy_poisson_2d_source_003 | GLM-4.7 | Training Strategy | 5 | 4 | 1 | 1 |

