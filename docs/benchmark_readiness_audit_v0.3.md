# PIM-PlanBench Benchmark Readiness Audit v0.3

Generated: 2026-05-26 03:19:42 UTC

## Inputs

| Input | Path |
| --- | --- |
| Public tasks | dataset/tasks_public_v0.3.jsonl |
| Private references | dataset/references_private_v0.3.jsonl |
| Score CSV | scores/pilot_v0.3/ModelOutput_all_existing_scored_v0.3.csv |

## Executive Summary

| Metric | Value |
| --- | --- |
| Public tasks | 26 |
| Private references | 26 |
| Scored tasks | 26 |
| Scored models | 6 |
| Score rows | 780 |
| Expected score rows for scored tasks | 780 |
| Missing score rows | 0 |
| Facet ceiling rows >= 4.5 | 297 (38.1%) |
| Exact 5.0 rows | 297 (38.1%) |
| Ceiling task totals >= 22.5 | 3 |
| Low-discrimination tasks, range <= 3.0 | 14 |
| Low-discrimination task-facets, range <= 0.5 | 28 |

## Recommendations

- High ceiling rate: add or rewrite hard-trap variants where generic PINN workflows are capped below full credit.
- Inspect saturated tasks first; require more explicit decisions about missing information, failure traps, or unsuitable baseline PINNs.
- Review low-discrimination tasks; either tighten the private reference/cap rules or replace with variants that force model-specific choices.
- Broaden failure-trap coverage for weak categories: shock_or_discontinuity.

## Dataset Taxonomy

### By Difficulty

| Difficulty | Tasks |
| --- | --- |
| medium | 8 |
| easy | 7 |
| hard_plus | 6 |
| hard | 5 |

### By Task Type

| Task type | Tasks |
| --- | --- |
| forward_pde_solving | 7 |
| inverse_parameter_estimation | 2 |
| boundary_condition_handling | 1 |
| boundary_value_problem | 1 |
| complex_geometry_high_frequency_modeling | 1 |
| complex_geometry_scattering | 1 |
| coupled_divergence_free_field_modeling | 1 |
| coupled_multiphysics_modeling | 1 |
| discontinuous_solution_modeling | 1 |
| forward_or_data_assimilation | 1 |
| heterogeneous_coefficient_field | 1 |
| high_frequency_frequency_domain_modeling | 1 |
| high_order_pde_modeling | 1 |
| multiscale_operator_or_solver_design | 1 |
| noisy_data_fitting | 1 |
| periodic_constraint_handling | 1 |
| sparse_observation_modeling | 1 |
| stiff_phase_field_modeling | 1 |
| unknown_source_recovery | 1 |

### By Domain

| Domain | Tasks |
| --- | --- |
| fluid_dynamics | 3 |
| heat_transfer | 3 |
| potential_fields | 3 |
| transport | 3 |
| chemical_biology | 2 |
| phase_field | 2 |
| porous_media | 2 |
| wave_physics | 2 |
| wave_propagation | 2 |
| acoustics | 1 |
| compressible_flow | 1 |
| magnetohydrodynamics | 1 |
| thermal_fluid_dynamics | 1 |

## Score Coverage Checks

| Check | Count | Examples |
| --- | --- | --- |
| Unscored public tasks | 0 |  |
| Scored task IDs not in public tasks | 0 |  |
| Public tasks missing private references | 0 |  |
| Missing task/model/facet score rows | 0 |  |

## Overall Model Scores

| Model | Rows | Avg facet score | Total facet points | Std | Ceiling rate | 5.0 rate |
| --- | --- | --- | --- | --- | --- | --- |
| Pro/moonshotai/Kimi-K2.6 | 130 | 4.43 | 576.0 | 0.55 | 46.2% | 46.2% |
| Pro/zai-org/GLM-4.7 | 130 | 3.98 | 518.0 | 0.72 | 23.8% | 23.8% |
| Pro/zai-org/GLM-5.1 | 130 | 4.36 | 567.0 | 0.67 | 46.9% | 46.9% |
| deepseek-ai/DeepSeek-V4-Flash | 130 | 4.22 | 549.0 | 0.69 | 37.7% | 37.7% |
| deepseek/deepseek-v4-pro | 130 | 4.22 | 549.0 | 0.72 | 36.9% | 36.9% |
| qwen/qwen3.7-max | 130 | 4.24 | 551.0 | 0.69 | 36.9% | 36.9% |

## Average Score By Difficulty

| Difficulty | Pro/moonshotai/Kimi-K2.6 | Pro/zai-org/GLM-4.7 | Pro/zai-org/GLM-5.1 | deepseek-ai/DeepSeek-V4-Flash | deepseek/deepseek-v4-pro | qwen/qwen3.7-max |
| --- | --- | --- | --- | --- | --- | --- |
| medium | 4.38 | 3.98 | 4.20 | 3.95 | 4.12 | 4.25 |
| easy | 4.46 | 3.94 | 4.43 | 4.23 | 4.23 | 4.29 |
| hard_plus | 4.53 | 4.00 | 4.47 | 4.47 | 4.23 | 4.20 |
| hard | 4.36 | 4.04 | 4.40 | 4.36 | 4.36 | 4.20 |

## Facet Discrimination

| Facet | Avg score | Score std | Avg model range per task | Min range | Max range | Ceiling rate |
| --- | --- | --- | --- | --- | --- | --- |
| Problem Formalization | 4.15 | 0.60 | 0.81 | 0.00 | 2.00 | 26.9% |
| Physics Constraints | 4.09 | 0.69 | 0.96 | 0.00 | 3.00 | 28.2% |
| Model Choice | 4.44 | 0.76 | 1.42 | 0.00 | 3.00 | 57.7% |
| Training Strategy | 4.39 | 0.67 | 0.85 | 0.00 | 3.00 | 48.7% |
| Validation Failure Risks | 4.15 | 0.65 | 1.15 | 0.00 | 3.00 | 28.8% |

## Task Discrimination

### Highest Model Separation

| Task | Difficulty | Type | PDE/system | Mean total | Range | Std | Ceiling models |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hard_plus_euler_shock_023 | hard_plus | discontinuous_solution_modeling | Compressible Euler equations with shocks | 20.83 | 8.00 | 2.97 | 3 |
| hard_plus_mhd_divergence_025 | hard_plus | coupled_divergence_free_field_modeling | Resistive magnetohydrodynamics | 22.00 | 7.00 | 2.58 | 4 |
| easy_poisson_2d_source_003 | easy | forward_pde_solving | 2D Poisson equation | 21.33 | 6.00 | 1.97 | 2 |
| easy_advection_1d_periodic_005 | easy | forward_pde_solving | 1D linear advection equation | 20.67 | 5.00 | 1.80 | 1 |
| hard_allen_cahn_016 | hard | stiff_phase_field_modeling | Allen-Cahn equation | 21.00 | 5.00 | 1.83 | 1 |
| hard_plus_multiscale_darcy_026 | hard_plus | multiscale_operator_or_solver_design | Multiscale Darcy flow with high-contrast permeability | 21.83 | 5.00 | 1.67 | 3 |
| medium_advection_diffusion_008 | medium | forward_pde_solving | Advection-diffusion equation | 19.33 | 5.00 | 1.49 | 0 |
| medium_burgers_inverse_viscosity_010 | medium | inverse_parameter_estimation | 1D viscous Burgers equation | 21.83 | 5.00 | 1.57 | 2 |
| easy_laplace_2d_boundary_007 | easy | boundary_value_problem | 2D Laplace equation | 20.83 | 4.00 | 1.34 | 1 |
| easy_reaction_diffusion_1d_006 | easy | forward_pde_solving | 1D reaction-diffusion equation | 21.00 | 4.00 | 1.41 | 0 |

### Lowest Model Separation

| Task | Difficulty | Type | PDE/system | Mean total | Range | Std | Ceiling models |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hard_plus_helmholtz_staircase_021 | hard_plus | complex_geometry_high_frequency_modeling | High-frequency Helmholtz equation in staircase geometry | 21.83 | 1.00 | 0.37 | 0 |
| hard_plus_acoustic_scattering_maze_022 | hard_plus | complex_geometry_scattering | Acoustic scattering in maze-like geometry | 21.33 | 1.00 | 0.47 | 0 |
| medium_heat_mixed_bc_014 | medium | boundary_condition_handling | 1D heat equation | 23.33 | 2.00 | 0.75 | 5 |
| hard_cahn_hilliard_017 | hard | high_order_pde_modeling | Cahn-Hilliard equation | 23.17 | 2.00 | 0.69 | 5 |
| easy_heat_1d_dirichlet_001 | easy | forward_pde_solving | 1D heat equation | 21.67 | 2.00 | 0.75 | 1 |
| hard_plus_rayleigh_benard_024 | hard_plus | coupled_multiphysics_modeling | Rayleigh-Benard convection under Boussinesq approximation | 21.67 | 2.00 | 0.75 | 1 |
| easy_burgers_1d_periodic_004 | easy | forward_pde_solving | 1D viscous Burgers equation | 21.50 | 2.00 | 0.76 | 0 |
| hard_navier_stokes_2d_018 | hard | forward_or_data_assimilation | 2D incompressible Navier-Stokes equations | 20.83 | 2.00 | 0.90 | 0 |
| medium_periodic_advdiff_015 | medium | periodic_constraint_handling | Periodic advection-diffusion equation | 20.33 | 2.00 | 0.75 | 0 |
| medium_reaction_diffusion_noisy_013 | medium | noisy_data_fitting | Two-species reaction-diffusion system | 19.00 | 2.00 | 0.82 | 0 |

### Most Saturated Tasks

| Task | Difficulty | Type | PDE/system | Mean total | Range | Ceiling models |
| --- | --- | --- | --- | --- | --- | --- |
| medium_heat_mixed_bc_014 | medium | boundary_condition_handling | 1D heat equation | 23.33 | 2.00 | 5 |
| hard_cahn_hilliard_017 | hard | high_order_pde_modeling | Cahn-Hilliard equation | 23.17 | 2.00 | 5 |
| hard_helmholtz_high_frequency_020 | hard | high_frequency_frequency_domain_modeling | Helmholtz equation | 22.50 | 4.00 | 3 |

## Failure-Trap Coverage

| Category | Tasks hit | Task coverage |
| --- | --- | --- |
| missing_or_hallucinated_conditions | 26 | 100.0% |
| wrong_pde_or_wrong_physics | 12 | 46.2% |
| loss_or_constraint_omission | 26 | 100.0% |
| inverse_identifiability | 10 | 38.5% |
| high_frequency_or_spectral_bias | 9 | 34.6% |
| stiffness_or_multiscale | 9 | 34.6% |
| conservation_or_divergence | 6 | 23.1% |
| geometry_or_boundary_complexity | 26 | 100.0% |
| shock_or_discontinuity | 1 | 3.8% |
| operator_or_family_generalization | 7 | 26.9% |

### Task-Level Reference Coverage

| Task | Difficulty | Task type | Failure traps | Cap rules | Detected categories |
| --- | --- | --- | --- | --- | --- |
| easy_heat_1d_dirichlet_001 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, geometry_or_boundary_complexity |
| easy_wave_1d_icbc_002 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, high_frequency_or_spectral_bias, geometry_or_boundary_complexity |
| easy_poisson_2d_source_003 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, geometry_or_boundary_complexity |
| easy_burgers_1d_periodic_004 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, high_frequency_or_spectral_bias, geometry_or_boundary_complexity |
| easy_advection_1d_periodic_005 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, high_frequency_or_spectral_bias, geometry_or_boundary_complexity |
| easy_reaction_diffusion_1d_006 | easy | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, geometry_or_boundary_complexity |
| easy_laplace_2d_boundary_007 | easy | boundary_value_problem | 5 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, geometry_or_boundary_complexity |
| medium_advection_diffusion_008 | medium | forward_pde_solving | 5 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, geometry_or_boundary_complexity |
| medium_heat_inverse_alpha_009 | medium | inverse_parameter_estimation | 6 | 4 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, geometry_or_boundary_complexity |
| medium_burgers_inverse_viscosity_010 | medium | inverse_parameter_estimation | 6 | 4 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, inverse_identifiability, stiffness_or_multiscale, +1 more |
| medium_poisson_source_recovery_011 | medium | unknown_source_recovery | 6 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, inverse_identifiability, geometry_or_boundary_complexity |
| medium_wave_sparse_sensors_012 | medium | sparse_observation_modeling | 6 | 4 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, high_frequency_or_spectral_bias, geometry_or_boundary_complexity |
| medium_reaction_diffusion_noisy_013 | medium | noisy_data_fitting | 7 | 4 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, geometry_or_boundary_complexity |
| medium_heat_mixed_bc_014 | medium | boundary_condition_handling | 5 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, geometry_or_boundary_complexity |
| medium_periodic_advdiff_015 | medium | periodic_constraint_handling | 6 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, high_frequency_or_spectral_bias, geometry_or_boundary_complexity |
| hard_allen_cahn_016 | hard | stiff_phase_field_modeling | 7 | 4 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, high_frequency_or_spectral_bias, stiffness_or_multiscale, +2 more |
| hard_cahn_hilliard_017 | hard | high_order_pde_modeling | 7 | 6 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, stiffness_or_multiscale, conservation_or_divergence, +2 more |
| hard_navier_stokes_2d_018 | hard | forward_or_data_assimilation | 8 | 4 | missing_or_hallucinated_conditions, loss_or_constraint_omission, conservation_or_divergence, geometry_or_boundary_complexity |
| hard_darcy_heterogeneous_019 | hard | heterogeneous_coefficient_field | 5 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, geometry_or_boundary_complexity |
| hard_helmholtz_high_frequency_020 | hard | high_frequency_frequency_domain_modeling | 7 | 5 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, inverse_identifiability, high_frequency_or_spectral_bias, +3 more |
| hard_plus_helmholtz_staircase_021 | hard_plus | complex_geometry_high_frequency_modeling | 7 | 3 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, inverse_identifiability, high_frequency_or_spectral_bias, +3 more |
| hard_plus_acoustic_scattering_maze_022 | hard_plus | complex_geometry_scattering | 7 | 3 | missing_or_hallucinated_conditions, loss_or_constraint_omission, high_frequency_or_spectral_bias, stiffness_or_multiscale, geometry_or_boundary_complexity, +1 more |
| hard_plus_euler_shock_023 | hard_plus | discontinuous_solution_modeling | 7 | 5 | missing_or_hallucinated_conditions, loss_or_constraint_omission, stiffness_or_multiscale, conservation_or_divergence, geometry_or_boundary_complexity, +1 more |
| hard_plus_rayleigh_benard_024 | hard_plus | coupled_multiphysics_modeling | 7 | 4 | missing_or_hallucinated_conditions, loss_or_constraint_omission, stiffness_or_multiscale, conservation_or_divergence, geometry_or_boundary_complexity, +1 more |
| hard_plus_mhd_divergence_025 | hard_plus | coupled_divergence_free_field_modeling | 8 | 5 | missing_or_hallucinated_conditions, loss_or_constraint_omission, inverse_identifiability, conservation_or_divergence, geometry_or_boundary_complexity |
| hard_plus_multiscale_darcy_026 | hard_plus | multiscale_operator_or_solver_design | 7 | 5 | missing_or_hallucinated_conditions, wrong_pde_or_wrong_physics, loss_or_constraint_omission, stiffness_or_multiscale, conservation_or_divergence, +2 more |

### Sparse Private References To Inspect

| Task | Difficulty | PDE/system | Failure traps | Cap rules |
| --- | --- | --- | --- | --- |

### Review Flags Present In Private References

| Task | Review flags |
| --- | --- |
| easy_reaction_diffusion_1d_006 | Public task says IC/BC are available but does not expose exact private IC/BC; score conditional handling rather than guessing exact values. |
| medium_heat_inverse_alpha_009 | Public task asks for additional physical conditions to be specified or obtained; do not require exact private IC/BC values. |
| medium_burgers_inverse_viscosity_010 | Public task does not specify boundary type; reward requesting BC information or explicitly stating assumptions. |
| medium_wave_sparse_sensors_012 | This is intentionally a missing-condition detection task; do not require exact private IC/BC values. |
| medium_reaction_diffusion_noisy_013 | Exact private Gray-Scott parameters are not in public; require coupled reaction-diffusion planning, not parameter guessing. |
| hard_allen_cahn_016 | Exact private IC is not public; score interface/stiffness planning rather than exact IC reproduction. |
| hard_navier_stokes_2d_018 | Public task does not give exact BC/IC; reward conditional incorporation or requesting details. |
| hard_helmholtz_high_frequency_020 | Exact private k/source are not public; require high-frequency strategy, not exact parameter reproduction. |
| hard_plus_helmholtz_staircase_021 | Hard-plus stress task; exact geometry discretization is not public, so evaluate geometry-aware planning rather than exact implementation details. |
| hard_plus_acoustic_scattering_maze_022 | Boundary descriptions are public only at a high level; evaluate whether the plan asks for/uses them rather than guessing exact wall conditions. |
| hard_plus_euler_shock_023 | Exact piecewise states are not public; require shock-aware conservation planning, not exact Riemann data. |

## Score Distribution

| Score | Rows |
| --- | --- |
| 2.0 | 7 |
| 3.0 | 93 |
| 4.0 | 383 |
| 5.0 | 297 |

## Interpretation Notes

- This audit detects saturation and coverage patterns; it does not replace human scoring.
- A high score ceiling is not automatically bad, but it weakens model ranking claims if many tasks have low model separation.
- Failure-trap categories are keyword-based diagnostics over private references and task text.
- Before paper release, add inter-annotator agreement and an execution-validation subset.
