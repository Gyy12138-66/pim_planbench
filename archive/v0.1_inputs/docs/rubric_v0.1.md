# Pilot Rubric

Each task is scored on five facets. Use a 0-2 scale for each facet.

## Facets

### Problem Formalization

- 0: Missing or physically wrong variables, unknowns, or task objective.
- 1: Partially identifies variables and objective but misses important parameters or inverse/forward distinction.
- 2: Correctly identifies variables, unknowns, known parameters, geometry or domain when available, and task objective.

### Physics Constraints

- 0: Missing or incorrect governing equation, IC, BC, or key physical constraint.
- 1: Partially correct but incomplete constraints.
- 2: Correctly captures governing equation, IC/BC/observations, and special constraints such as periodicity, incompressibility, or conservation.

### Model Choice

- 0: Chooses an unsuitable model or gives no model rationale.
- 1: Chooses a plausible model but gives weak or generic justification.
- 2: Chooses a suitable physics-informed model and explains why it fits the PDE, data, and task type.

### Training Strategy

- 0: Missing or incorrect loss design, sampling, or optimization plan.
- 1: Includes some reasonable training details but omits important loss terms or stability strategies.
- 2: Specifies appropriate residual/data/IC/BC losses, sampling, normalization, optimization, and relevant stability strategies.

### Validation & Failure Risks

- 0: Missing validation or gives irrelevant metrics.
- 1: Gives generic validation but misses physics-specific risks.
- 2: Provides task-specific validation metrics and identifies plausible failure risks such as missing conditions, stiffness, spectral bias, identifiability, or boundary violations.

## Notes

TODO_REVIEW: Decide whether to add a separate cost-awareness facet after the first pilot scoring round.
