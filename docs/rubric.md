# PlanScore Rubric v0.3

Each task is scored on five facets. Use a 0-5 scale for each facet.

Total score: 25 points.

Rubric v0.3 keeps the v0.2 five-facet structure but adds explicit ceiling rules for generic answers, hallucinated specifications, and the v0.3 hard-trap tasks. These caps should be applied after reading the answer for the relevant facet. When multiple caps apply, use the strictest cap.

## General Scoring Principles

- Score only what is justified by the public task statement and the model answer.
- Reward explicit missing-information handling. A response that says a boundary condition, initial condition, coefficient, geometry, observation layout, or parameter value must be specified before execution should receive more credit than a response that silently invents it.
- Do not require the model to guess private-only reference values. Exact private IC/BC/source/parameter values are not required unless they are in the public prompt.
- Penalize unsupported assumptions. A response may make conditional assumptions if it labels them as assumptions and explains how the workflow changes under them.
- Distinguish breadth from task awareness. A long answer that lists many AI4Sci buzzwords should not receive full credit unless it makes the task-specific decisions required by the problem.
- A score of 4 means the answer is mostly correct and operational, but still misses one important subtlety or execution detail. A score of 5 requires task-specific correctness plus an executable plan for the main failure mode of the task.

## General Ceiling Rules

- Generic PINN template: If the answer gives only a generic PINN workflow without task-specific residuals, constraints, model rationale, training details, or risks, all affected facets are capped at 3.
- Hallucinated specifications: If the answer invents a concrete IC, BC, parameter value, geometry, coefficient field, observation layout, or source term not given in the public prompt and does not label it as an assumption, affected facets are capped at 2.
- Problem formalization over-credit cap: A Problem Formalization answer that correctly names the PDE or target field but does not explicitly separate known inputs, unknowns, inferred parameters if any, data/observation role, and missing execution specifications is capped at 4. If it omits the forward/inverse/data-assimilation/surrogate distinction when that distinction affects the workflow, it is capped at 3.
- Unsupported assumption handling in Problem Formalization: If the answer introduces concrete domain bounds, IC/BC values, source functions, coefficient fields, sensor layouts, or parameter values that are not in the public prompt but labels them only as defaults without explaining that alternatives must be supplied, Problem Formalization is capped at 3. If those assumptions are presented as facts, use the hallucinated-specification cap.
- Method name without execution detail: If the answer only names a method such as PINN, FNO, DeepONet, SIREN, weak form, vector potential, or domain decomposition without explaining inputs/outputs, losses, sampling, training, and validation, Model Choice and Training Strategy are capped at 2.
- Wrong task type: If the answer treats a forward problem as inverse, or an inverse/data-assimilation problem as a pure forward solve, Problem Formalization and Model Choice are capped at 2.
- Wrong PDE type or physics: If the answer changes the governing equation class, such as treating Helmholtz as a time-domain wave equation or Cahn-Hilliard as Allen-Cahn, Problem Formalization and Physics Constraints are capped at 2.
- Missing required data term: If the public prompt includes observations or sparse measurements and the answer omits a data-misfit term, Physics Constraints and Training Strategy are capped at 2.
- Missing IC/BC/constraint term: If the public prompt explicitly provides IC, BC, boundary topology, divergence, conservation, or other constraints and the answer omits them, affected Physics Constraints and Training Strategy facets are capped at 3, or 2 if the omitted constraint is central to the task.
- Validation uses only MSE: If validation reports only field MSE or generic held-out error without PDE residual, IC/BC error, data consistency, conservation, divergence, phase, flux, shock, or other task-specific physical checks, Validation & Failure Risks is capped at 3.
- Schema violation: If an answer cannot be mapped to the required five facets, score missing or unmappable facets as 0 unless a faithful manual mapping is documented.

## v0.3 Hard-Trap Ceiling Rules

These task-specific caps are intended for the rewritten v0.3 public tasks and matching private references.

- `hard_plus_euler_shock_023`: If the answer uses a standard smooth strong-form pointwise PINN without weak, integral, conservative, or shock-aware treatment, Model Choice, Training Strategy, and Validation & Failure Risks are capped at 2. If it omits conservative variables or conservation form, Problem Formalization and Physics Constraints are capped at 2. If it omits entropy/admissibility or positivity considerations, Physics Constraints and Validation & Failure Risks are capped at 3.
- `medium_periodic_advdiff_015`: If the answer uses fixed Dirichlet endpoint values instead of identified-endpoint periodic compatibility, Physics Constraints and Training Strategy are capped at 2. If it mentions only value periodicity and ignores derivative or diffusive-flux periodicity, affected Physics Constraints, Training Strategy, and Validation & Failure Risks are capped at 3.
- `hard_plus_multiscale_darcy_026`: If the answer does not distinguish a single high-contrast solve from reusable surrogate/operator learning over many coefficient fields, Problem Formalization, Model Choice, and Training Strategy are capped at 3. If it chooses a neural operator without specifying many permeability-field samples or a generalization protocol, Model Choice and Training Strategy are capped at 3. If it ignores high-contrast coefficient effects, flux continuity, or mass balance, affected facets are capped at 2.
- `hard_helmholtz_high_frequency_020`: If the answer only names Fourier features, SIREN, or another high-frequency architecture but omits complex-valued representation, points-per-wavelength sampling, or phase-aware validation, Model Choice, Training Strategy, and Validation & Failure Risks are capped at 3. If it treats Helmholtz as time-dependent wave propagation, Problem Formalization and Physics Constraints are capped at 2. If it uses a real-only scalar formulation without addressing complex phase, affected facets are capped at 3.
- `hard_plus_mhd_divergence_025`: If the answer omits magnetic divergence control, Physics Constraints, Model Choice, and Validation & Failure Risks are capped at 2. If it relies only on a soft divergence penalty without constrained parameterization, projection, or divergence-drift validation, Model Choice, Training Strategy, and Validation & Failure Risks are capped at 3. If it models only fluid velocity or ignores magnetic induction coupling, Problem Formalization, Physics Constraints, and Model Choice are capped at 2.
- `hard_cahn_hilliard_017`: If the answer treats Cahn-Hilliard as Allen-Cahn, Problem Formalization, Physics Constraints, and Model Choice are capped at 2. If it does not introduce chemical potential or otherwise address fourth-order derivative burden, Model Choice and Training Strategy are capped at 3. A direct fourth-order PINN can receive at most 4 on Model Choice and Training Strategy even if it discusses derivative burden and conservation correctly. If it omits mass conservation, Physics Constraints and Validation & Failure Risks are capped at 2. If it omits free-energy or long-time drift validation, Validation & Failure Risks is capped at 4.

## Facets

### Problem Formalization

- 0: No usable problem formulation. The response misses or misstates the core unknown, variables, or task objective, or defines a physically or mathematically incompatible problem.
- 1: Very superficial formulation. The response mostly restates the prompt or names the broad phenomenon, but does not clearly identify the unknown field or quantity, independent variables, known inputs, domain, or modeling objective.
- 2: Partial formulation with major gaps. The response identifies some key elements, such as the main unknown or governing task, but misses important variables, parameters, geometry or domain, data inputs, or confuses known vs. unknown quantities or forward vs. inverse task type. A response at this level may be directionally correct but would not tell a reader what information must be supplied before the workflow can be executed.
- 3: Mostly correct formulation with noticeable incompleteness or imprecision. The response identifies the main unknown, variables, broad domain type, and objective, but omits or blurs one important modeling element, such as the role of observations, whether parameters are known or inferred, the precise domain or time horizon, boundary/initial/source specification status, coefficient-field status, or the forward/inverse/surrogate task type. This is the default score for a mathematically plausible but template-like problem setup.
- 4: Strong formulation. The response correctly and explicitly identifies the unknowns, independent variables, known parameters or data, domain or geometry type, task type, and objective, and avoids unsupported factual assumptions. It may receive 4 if it flags some missing information but does not state how that missing information changes the executable workflow, or if it misses one task-specific modeling decision such as complex-valued representation, conservative variables, coupled fields, sparse-observation role, or single-instance versus reusable-surrogate status.
- 5: Complete and precise formulation. Award 5 only when the response cleanly formalizes the problem as a well-defined modeling task and makes the central task-specific decision explicit. It must separate known inputs, unknown fields, inferred parameters if any, independent variables, domain/geometry/time horizon, data or observation roles, and forward/inverse/data-assimilation/surrogate objective. It must also handle missing public specifications operationally, by stating what must be supplied before execution or giving clearly labeled conditional branches, without inventing unsupported details. A polished restatement of the PDE, even with correct variables, is not enough for 5.

### Physics Constraints

- 0: No valid physical constraint formulation. The response omits the governing equation or gives a physically or mathematically wrong equation, initial condition, boundary condition, or constraint.
- 1: Very weak constraint statement. The response only mentions generic ideas such as "satisfy the PDE" or "obey physics," but does not correctly specify the residual form, where it applies, or the relevant IC, BC, or observation constraints.
- 2: Partial constraints with major omissions or errors. The response identifies some core constraints, such as the PDE residual or one condition type, but misses important IC, BC, or observation constraints, applies them on the wrong domain, uses the wrong boundary type, or incorrectly changes the problem assumptions.
- 3: Basic correct constraints. The response correctly states the main governing residual and the required IC, BC, or observation constraints in the appropriate parts of the domain, but remains generic or misses important qualifiers, such as source terms, variable coefficients, compatibility conditions, conservation laws, or other task-specific physical constraints.
- 4: Strong constraint formulation. The response correctly and explicitly specifies the PDE residual, interior or domain applicability, IC, BC, or observation constraints, and relevant physical assumptions such as constant coefficients, no source terms, incompressibility, periodicity, conservation, or material assumptions when applicable. Minor imprecision is acceptable.
- 5: Complete and physically insightful constraint formulation. The response gives the correct constraints and also identifies subtle but important physical or mathematical requirements, such as compatibility at boundaries or corners, conservation or maximum principles, energy behavior, regularity issues, source or forcing assumptions, variable-coefficient cases, or constraints that affect learnability and validation, without inventing unsupported conditions.

### Model Choice

- 0: No suitable model choice. The response either gives no model, chooses a model incompatible with the problem, or proposes an approach that cannot represent the required solution or constraints.
- 1: Very generic model choice. The response names a broad model class, such as "neural network" or "PINN," but does not specify inputs, outputs, architecture type, or why the model fits the PDE or task.
- 2: Partially suitable model choice with weak justification. The response chooses a plausible model and may identify inputs or outputs, but gives little task-specific rationale, ignores the PDE type or data setting, or misses important implications for representing derivatives, constraints, or unknown parameters.
- 3: Basic correct model choice. The response selects an appropriate model class, such as a coordinate-based PINN for a forward PDE problem, specifies the main inputs and outputs, and gives a reasonable but limited rationale based on smoothness, PDE type, available data, or task type.
- 4: Strong model choice. The response gives a suitable architecture and explains why it fits the governing equation, solution regularity, derivative requirements, data availability, and forward or inverse nature of the task. It may also discuss activation functions, capacity, hard vs. soft constraint handling, or parameterization choices.
- 5: Excellent, task-aware model choice. The response not only selects a suitable physics-informed model and architecture, but also adapts the choice to the problem's mathematical structure, such as smoothness, boundary enforcement, variable coefficients, high-frequency modes, stiffness, conservation structure, or identifiability. It justifies design tradeoffs without making unsupported claims or adding unnecessary complexity.

### Training Strategy

- 0: No usable training strategy. The response omits the loss, sampling, or optimization plan, or proposes a training setup that is incompatible with the model or physics constraints.
- 1: Very incomplete strategy. The response only mentions generic training ideas, such as "train the neural network" or "minimize error," without specifying the required loss components, where samples come from, or how optimization is performed.
- 2: Partial strategy with major gaps. The response includes some relevant elements, such as a PDE residual loss or optimizer, but misses key loss terms, omits IC, BC, or data sampling, ignores constraint enforcement, or gives an underspecified optimization procedure.
- 3: Basic correct strategy. The response defines a reasonable composite loss with PDE residual and required IC, BC, or data terms, samples the appropriate interior and boundary, initial, or observation regions, and proposes a plausible optimizer. However, it remains fairly standard and lacks conditioning, weighting, refinement, or stability details.
- 4: Strong strategy. The response specifies appropriate residual, data, IC, or BC losses, or explains when some terms are removed by hard constraints; describes interior, boundary, initial, and observation sampling; includes normalization or nondimensionalization; uses a credible optimization schedule such as Adam followed by L-BFGS; and mentions loss balancing, monitoring, or stability measures.
- 5: Excellent, problem-aware training strategy. The response gives a complete training plan and adapts it to likely difficulty modes of the PDE or task, such as sharp initial transients, small diffusivity, long time horizons, stiff dynamics, boundary layers, spectral bias, imbalance between residual and data terms, or localized high-error regions. It includes targeted methods such as adaptive loss weighting, residual-based adaptive refinement, causal or time-marching training, hard-constraint-aware loss design, normalization, and concrete monitoring criteria without adding irrelevant complexity.

### Validation & Failure Risks

- 0: No meaningful validation or risk analysis. The response omits validation entirely, gives irrelevant metrics, or identifies failure modes unrelated to the task.
- 1: Very generic validation or risks. The response mentions broad ideas such as "check accuracy," "avoid overfitting," or "training may fail," but does not specify suitable metrics, reference comparisons, physics checks, or task-specific risks.
- 2: Partial validation with major gaps. The response gives some plausible validation method or risk, such as comparing predictions to data or monitoring loss, but misses important physics-specific checks, ignores the absence or role of reference data, or does not connect risks to the PDE or task structure.
- 3: Basic correct validation and risk analysis. The response proposes reasonable validation using analytical, numerical, or reference data when available, held-out observations, residual checks, or visual and time-slice comparisons, and identifies common PINN risks such as loss imbalance, sparse collocation, spectral bias, or poor BC or IC satisfaction.
- 4: Strong validation and risk analysis. The response includes task-specific validation metrics and physical consistency checks, such as PDE residual maps, IC or BC error, comparison to analytical, numerical, or sensor data, maximum principle, conservation or energy behavior where appropriate, and identifies risks tied to the problem assumptions, data availability, boundary or initial conditions, parameter assumptions, or sampling strategy.
- 5: Excellent, problem-aware validation and risk analysis. The response gives a complete validation plan and deeply task-specific failure analysis, including subtle mathematical or physical risks such as IC or BC incompatibility, lack of identifiability, missing observations, wrong coefficient or source assumptions, stiffness or small-parameter regimes, long-horizon causality issues, boundary layers, high-frequency initial data, or residuals that look small while prediction error remains large. It also explains what can and cannot be verified without reference solutions.

## Scoring Examples

### Generic PINN Template

An answer says: "Use a PINN with inputs x,t and output u. Minimize PDE residual, boundary loss, and initial loss with Adam and L-BFGS. Validate with MSE."

This can be reasonable for easy tasks, but it is generic. If it does not specify the task residual, required conditions, data terms, and task-specific failure risks, affected facets should not exceed 3. Validation should not exceed 3 because it relies on generic MSE and omits physics-specific checks.

### Missing-Condition Hallucination

For a task where the public prompt says boundary or initial information may be missing, an answer asserts a concrete Dirichlet boundary condition or a specific initial profile without labeling it as an assumption.

Affected facets should be capped at 2 because the response invents information unavailable to the model. A better answer would say that the condition must be specified, acquired, or treated through conditional workflows before training.

### Hard-Trap Full-Credit Pattern

For `hard_plus_euler_shock_023`, a high-scoring answer identifies compressible Euler as a conservation-law problem with nonsmooth weak solutions, represents conservative variables, avoids using a smooth strong-form pointwise residual across shocks as the only physics loss, proposes weak/integral or control-volume residuals, includes positivity and entropy/admissibility checks, samples or decomposes near discontinuities, and validates shock speed/location, Rankine-Hugoniot consistency, and conservation errors.

This pattern can receive 5s because it makes the central task-specific decision rather than only naming a PINN or weak form.

## Notes

Rubric v0.3 supports the public v0.3 task wording and private `pim_planscore_private_v0.3` references. Do not mix v0.1 pilot outputs with v0.3 scoring claims without rerunning the model prompts.
