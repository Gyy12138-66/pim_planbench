# score_v04 迁移核验报告

**结论：PASS**
## 55 臂不变量

- I1 D2/D3 < G：PASS
- I2 非消融臂零 claim cap：PASS

### 55 臂：v0.3 管线 vs score_v04

- cue-dropped（v0.3 硬编码外部 cap 挂起为 cue 规则）：9 行
- claim-added（新断言层压分）：14 行
- 其他差异：0 行

  - [cue-dropped] hard_plus_euler_shock_023 / Pro/zai-org/GLM-4.7 / Model Choice: 2 -> 4
  - [cue-dropped] hard_plus_euler_shock_023 / Pro/zai-org/GLM-4.7 / Training Strategy: 2 -> 4
  - [cue-dropped] hard_plus_euler_shock_023 / deepseek/deepseek-v4-pro / Model Choice: 2 -> 5
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/T / Problem Formalization: 2 -> 3
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/T / Physics Constraints: 2 -> 3
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/T / Model Choice: 2 -> 3
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/T / Training Strategy: 2 -> 3
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/T / Validation Failure Risks: 2 -> 3
  - [cue-dropped] hard_plus_euler_shock_023 / ARM/D1 / Training Strategy: 2 -> 4
  - [claim-added] easy_poisson_2d_source_003 / ARM/D2 / Problem Formalization: 5 -> 2
  - [claim-added] easy_poisson_2d_source_003 / ARM/D2 / Model Choice: 5 -> 2
  - [claim-added] easy_poisson_2d_source_003 / ARM/D3 / Problem Formalization: 5 -> 2
  - [claim-added] easy_advection_1d_periodic_005 / ARM/D2 / Problem Formalization: 4 -> 2
  - [claim-added] easy_advection_1d_periodic_005 / ARM/D2 / Model Choice: 5 -> 2
  - [claim-added] easy_advection_1d_periodic_005 / ARM/D3 / Problem Formalization: 5 -> 2
  - [claim-added] medium_burgers_inverse_viscosity_010 / ARM/D2 / Problem Formalization: 4 -> 2
  - [claim-added] medium_burgers_inverse_viscosity_010 / ARM/D3 / Physics Constraints: 5 -> 2
  - [claim-added] hard_allen_cahn_016 / ARM/D2 / Problem Formalization: 4 -> 2
  - [claim-added] hard_allen_cahn_016 / ARM/D2 / Model Choice: 5 -> 2
  - [claim-added] hard_allen_cahn_016 / ARM/D3 / Problem Formalization: 5 -> 2
  - [claim-added] hard_plus_euler_shock_023 / ARM/D2 / Problem Formalization: 4 -> 2
  - [claim-added] hard_plus_euler_shock_023 / ARM/D2 / Model Choice: 5 -> 2
  - [claim-added] hard_plus_euler_shock_023 / ARM/D3 / Problem Formalization: 4 -> 2

## 面板 unchanged 题子集（9 题 × 6 模型 = 270 行）

### 面板 unchanged：v0.3 管线 vs score_v04

- cue-dropped（v0.3 硬编码外部 cap 挂起为 cue 规则）：8 行
- claim-added（新断言层压分）：0 行
- 其他差异：0 行

  - [cue-dropped] hard_plus_euler_shock_023 / Pro/zai-org/GLM-4.7 / Model Choice: 2 -> 4
  - [cue-dropped] hard_plus_euler_shock_023 / Pro/zai-org/GLM-4.7 / Training Strategy: 2 -> 4
  - [cue-dropped] hard_plus_multiscale_darcy_026 / Pro/zai-org/GLM-4.7 / Model Choice: 3 -> 5
  - [cue-dropped] hard_plus_euler_shock_023 / deepseek/deepseek-v4-pro / Model Choice: 2 -> 5
  - [cue-dropped] hard_plus_mhd_divergence_025 / deepseek/deepseek-v4-pro / Model Choice: 2 -> 5
  - [cue-dropped] hard_plus_mhd_divergence_025 / qwen/qwen3.7-max / Model Choice: 2 -> 5
  - [cue-dropped] hard_plus_mhd_divergence_025 / qwen/qwen3.7-max / Validation Failure Risks: 2 -> 4
  - [cue-dropped] hard_plus_multiscale_darcy_026 / qwen/qwen3.7-max / Model Choice: 3 -> 4
