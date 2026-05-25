# Task Revision Notes v0.3

This revision follows the benchmark readiness audit and targets the first batch of saturated or low-discrimination tasks. The goal is to reduce method leakage in public prompts while tightening private scoring references.

## Public Task Changes

| Task | Change |
| --- | --- |
| `hard_plus_euler_shock_023` | Removed explicit instruction to avoid pointwise smooth residual fitting. The public prompt now asks for a workflow for nonsmooth Euler-type fields from piecewise states. |
| `medium_periodic_advdiff_015` | Rephrased periodicity as physically identified endpoints and asks which endpoint constraints are needed for diffusive transport. |
| `hard_plus_multiscale_darcy_026` | Removed explicit candidate methods from the prompt. The task now asks the model to decide between single-instance solving and reusable surrogate modeling based on available information. |
| `hard_helmholtz_high_frequency_020` | Made the field explicitly complex-valued and phase-sensitive, with short wavelength relative to domain size. |
| `hard_plus_mhd_divergence_025` | Removed explicit divergence-free wording from the public prompt while keeping nonphysical field configurations as the planning challenge. |
| `hard_cahn_hilliard_017` | Removed explicit fourth-order derivative difficulty from the public prompt and emphasized chemical-potential-driven conserved phase-field dynamics. |

## Private Reference Changes

The matching entries in `dataset/references_private_v0.3.jsonl` now use `scoring_version = pim_planscore_private_v0.3` and add stricter traps/cap rules:

- Generic PINN answers remain capped at 3.
- Euler shock answers must infer weak/conservative treatment, entropy/admissibility, positivity, and shock-aware validation.
- Periodic advection-diffusion answers that mention only value periodicity are capped at 3 for affected facets.
- Multiscale Darcy answers must distinguish single-instance solvers from learned surrogates across coefficient-field families.
- Helmholtz answers must handle complex-valued fields, wavelength-scaled sampling, and phase-aware validation.
- MHD answers cannot rely on an unexamined soft divergence penalty for full credit.
- Cahn-Hilliard answers need chemical-potential/mixed-form reasoning, mass conservation, and energy or long-time drift validation.

## Result Status

Existing `runs/pilot_v0.1/` and `scores/pilot_v0.1/` artifacts were generated from public v0.1 prompts. They should be treated as pilot evidence only. New model runs are required before scoring v0.3.
