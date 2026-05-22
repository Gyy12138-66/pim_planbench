# Pilot Rubric v0.2

Each task is scored on five facets. Use a 0-5 scale for each facet.

Total score: 25 points.

## Facets

### Problem Formalization

- 0: No usable problem formulation. The response misses or misstates the core unknown, variables, or task objective, or defines a physically or mathematically incompatible problem.
- 1: Very superficial formulation. The response mostly restates the prompt or names the broad phenomenon, but does not clearly identify the unknown field or quantity, independent variables, known inputs, domain, or modeling objective.
- 2: Partial formulation with major gaps. The response identifies some key elements, such as the main unknown or governing task, but misses important variables, parameters, geometry or domain, data inputs, or confuses known vs. unknown quantities or forward vs. inverse task type.
- 3: Mostly correct formulation with noticeable incompleteness or imprecision. The response identifies the main unknown, variables, domain type, and objective, but omits or blurs one important modeling element, such as the role of observations, whether parameters are known or inferred, the precise domain or time horizon, or the task type.
- 4: Strong formulation. The response correctly and explicitly identifies the unknowns, independent variables, known parameters or data, domain or geometry, task type, and objective. Only minor details are missing or slightly imprecise, and the formulation would support a reasonable modeling setup.
- 5: Complete and precise formulation. The response cleanly formalizes the problem as a well-defined modeling task, clearly separating known inputs, unknowns, parameters to infer if any, independent variables, domain, geometry, time horizon, data or observation roles, and forward or inverse objective. It also flags missing problem specifications or necessary assumptions without inventing unsupported details.

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

## Notes

TODO_REVIEW: Decide whether to add a separate cost-awareness facet after the first pilot scoring round.
