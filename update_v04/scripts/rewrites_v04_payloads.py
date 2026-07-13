#!/usr/bin/env python3
"""v0.4 逐题转写 payload（修订项 #1/#3 落地，格式见 docs/dataset_schema_v0.4.md）。

来源：update_v04/task_rewrites_v0.4/*.md 的 16 份重写规格（作者已放行转写）。
每题 payload：
  public:  problem（终稿题面）、tags_add/tags、difficulty/id 覆盖（仅 007r）
  private: set（顶层字段替换）、failure_traps_add、critical_points_{set,add}、
           verifiable_claims（含 selftest gold/tamper）、cap_rules（v0.4 结构）、
           cap_rules_mode（replace=全量替换任务特异规则 / add=在 v0.3 之上追加）、
           task_type_decl、human_review
机器化政策（schema §3.2）：写不出高精确率 patterns 的支点退 trigger:"cue"，
不硬塞 claim——002/006/012 三题为全 cue 题，记入 CHANGELOG。
"""

NUM = r"([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)"
BIGNUM = r"([0-9][0-9,]{2,})"   # ≥3 位（含千分逗号），避免误捕 "10 points per wavelength"
DRAFT_HR = "DRAFT v0.4: instance values pending author finalization"
ALL_FACETS = ["problem_formalization", "physics_constraints", "model_choice",
              "training_strategy", "validation_failure_risks"]


def _corner_exponent_claim(cap_id):
    """凹角奇异指数 2/3 的规格对账（007r 与 021 共用，item_analysis §4-B）。"""
    return {
        "claim_id": "corner_exponent",
        "type": "param_value",
        "basis": "spec",
        "facets": ALL_FACETS,
        "description": "声称的凹角奇异指数须与 3π/2 开角的理论值 2/3 一致",
        "param": "singularity_exponent",
        "true_value": 0.6667,
        "rtol": 0.03,
        "patterns": [
            r"r\^\{?\(?([0-9]+\s*/\s*[0-9]+)\)?\}?",
            r"(?:singular\w*|corner)[^.]{0,80}r\^\{?\(?([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+)?)\)?\}?",
            r"(?:singularity\s+)?exponent\s*(?:of|is|=|:)\s*(?:about\s+|approximately\s+)?([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+)?)",
        ],
        "on_contradiction": cap_id,
        "selftest": {
            "gold": "Near the re-entrant corner the solution behaves like r^(2/3)*sin(2*theta/3), so the gradient is unbounded there.",
            "tamper": "The corner singularity has exponent 1/2, matching the u ~ r^(1/2) behaviour we expect at the re-entrant corner.",
        },
    }


def _budget_claim(claim_id, quantity_patterns, limit, cap_id, what, gold, tamper):
    """公开算力预算合规断言（004/021；schema §3.2 单量 arithmetic_consistency 惯用法）。"""
    return {
        "claim_id": claim_id,
        "type": "arithmetic_consistency",
        "basis": "plan_internal",
        "facets": ["training_strategy", "model_choice"],
        "description": f"计划声称的{what}不得超出题面公开预算 {limit}",
        "quantities": {"n": quantity_patterns},
        "expression": f"n <= {limit}",
        "on_contradiction": cap_id,
        "selftest": {"gold": gold, "tamper": tamper},
    }


POINTS_PATTERNS = [
    BIGNUM + r"\s+(?:total\s+|residual\s+|collocation\s+|interior\s+|corner\s+|bulk\s+)*points",
    r"points?\s*(?:budget|count|total)?\s*(?:of|=|:)\s*" + BIGNUM,
]
STEPS_PATTERNS = [
    BIGNUM + r"\s+(?:optimizer|training|adam|l-bfgs|total|gradient)?\s*steps",
    r"steps?\s*(?:budget)?\s*(?:of|=|:)\s*" + BIGNUM,
]

REWRITES = {

# ─────────────────────────────────────────────────────── 002 wave IC/BC
"easy_wave_1d_icbc_002": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A scientist needs to approximate the displacement of a one-dimensional "
            "vibrating string over a fixed time window. The wave speed is known. Both the "
            "initial displacement profile and the initial velocity profile are provided "
            "as measured data, and the endpoints are held fixed. Because the initial data "
            "come from measurements, they may fail to satisfy the endpoint conditions "
            "exactly at the corners of the space-time domain. Design a physics-informed "
            "modeling workflow for the displacement field. State explicitly (i) how each "
            "of the two initial conditions is enforced, including any derivative-level "
            "treatment the second one requires, (ii) how compatibility between initial "
            "and boundary data is checked and what the workflow does if it fails, and "
            "(iii) which physical invariants of the ideal system you will monitor during "
            "validation and with what tolerance."
        ),
        "tags_add": ["derivative_ic", "corner_compatibility", "energy_conservation"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [],   # 全 cue 题：能量阈值/导数级 IC 的高精确率 patterns 写不出（§3.2 政策）
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_velocity_ic_value", "trigger": "cue",
             "condition": "enforces only the displacement initial condition, or treats the initial velocity as a value constraint on u rather than a constraint on the time derivative of the network output (or an equivalent hard-encoding)",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 2,
             "rationale": "The second IC of a second-order-in-time equation is derivative-level; a value treatment breaks characteristic propagation."},
            {"rule_id": "cap_no_compatibility_handling", "trigger": "cue",
             "condition": "the prompt states the initial data may be incompatible with the boundary conditions and the plan neither checks compatibility nor states a remedy",
             "affected_facets": ["problem_formalization", "validation_failure_risks"], "max_score": 3,
             "rationale": "Corner compatibility is an announced part of the task specification."},
            {"rule_id": "cap_no_wave_specific_validation", "trigger": "cue",
             "condition": "validation omits every wave-specific check (energy drift with tolerance, d'Alembert/characteristic consistency, reflection behavior)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Field MSE alone cannot expose wave-specific failure modes."},
        ],
        "failure_traps_add": [
            "treats initial velocity as a value constraint (misses derivative-level enforcement)",
            "no corner compatibility check between IC and BC",
            "claims energy conservation monitoring without a drift tolerance",
        ],
        "critical_points_add": {
            "physics_constraints": [
                "enforces the initial velocity as a constraint on the time derivative of the network output (or hard-encodes it via a time-factor ansatz)",
                "addresses corner compatibility between initial data and endpoint conditions",
            ],
            "validation_failure_risks": [
                "monitors energy drift with an explicit tolerance",
                "includes a characteristic/d'Alembert consistency or reflection-behavior check",
            ],
        },
        "set": {
            "reference_conditions_extra": {
                "incompatible_validation_instance":
                    "u(x,0)=sin(pi*x)+0.05 with zero endpoint values (deliberately corner-incompatible; reserved for a future execution-validity round)"
            },
        },
    },
},

# ─────────────────────────────────────────────────────── 004 Burgers 预算
"easy_burgers_1d_periodic_004": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A team wants to model a one-dimensional viscous Burgers system on a periodic "
            "spatial domain. The initial velocity profile and the viscosity coefficient "
            "are known, and the viscosity is small enough that a steep internal layer of "
            "width comparable to the viscosity scale will form. The compute budget is "
            "fixed in advance: at most 20,000 residual collocation points in memory at "
            "any time and at most 30,000 optimizer steps in total. Design a "
            "physics-informed modeling workflow for the velocity field. Justify "
            "quantitatively — in terms of the viscosity scale — how your sampling "
            "strategy and network capacity resolve the internal layer within the stated "
            "budget, and what you would monitor to detect an under-resolved layer."
        ),
        "tags_add": ["viscous_layer", "compute_budget", "resolution_economics"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            _budget_claim(
                "budget_points", POINTS_PATTERNS, 20000, "cap_budget_violation",
                "配点数",
                gold="We allocate 18,000 collocation points, concentrating 6,000 of them inside the viscous layer via residual-based resampling.",
                tamper="We sample 50,000 collocation points uniformly across the space-time domain each iteration.",
            ),
            _budget_claim(
                "budget_steps", STEPS_PATTERNS, 30000, "cap_budget_violation",
                "优化步数",
                gold="Training uses 25,000 optimizer steps in total: 20,000 Adam steps followed by 5,000 L-BFGS steps.",
                tamper="We train for 100,000 optimizer steps to ensure convergence of the layer region.",
            ),
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_no_quantitative_layer_link", "trigger": "cue",
             "condition": "invokes adaptive sampling, refinement, or loss weighting by name without any quantitative link between the viscosity scale, the layer width, and the collocation allocation",
             "affected_facets": ["training_strategy"], "max_score": 3,
             "rationale": "Named techniques without layer-budget arithmetic are template text."},
            {"rule_id": "cap_budget_violation", "trigger": "claim",
             "condition": "the proposed sampling or optimization plan exceeds the stated compute budget, or ignores it",
             "affected_facets": ["training_strategy", "model_choice"], "max_score": 3,
             "rationale": "The budget is part of the public specification; exceeding it is a specification violation."},
            {"rule_id": "cap_no_underresolution_indicator", "trigger": "cue",
             "condition": "validation includes no indicator specific to an under-resolved layer (residual concentration near the front, layer-width estimate vs theory, oscillation detection)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "A small total loss can coexist with an under-resolved internal layer."},
        ],
        "failure_traps_add": [
            "names RAR/weighting without quantitative layer-budget argument",
            "sampling plan exceeds stated budget",
            "no under-resolution indicator in validation",
        ],
        "critical_points_add": {
            "training_strategy": [
                "converts the viscosity scale into a layer width and a collocation allocation (numbers, not names)",
                "stays within the stated 20,000-point / 30,000-step budget",
            ],
        },
        "set": {
            "parameter_values": {"nu": "0.01/pi (reference instance; reuses task-010 reference infrastructure)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 006 反应扩散（轻改）
"easy_reaction_diffusion_1d_006": {
    "revision": "light_edit",
    "public": {
        "problem": (
            "A scientist wants to model a one-dimensional scalar reaction-diffusion "
            "process where a concentration diffuses and reacts according to a known "
            "nonlinear reaction term. Initial and boundary conditions are available. "
            "The reaction is strong relative to diffusion, so the solution develops a "
            "propagating front whose width and speed are set by the balance of the two "
            "mechanisms. Design a physics-informed modeling workflow for the "
            "concentration field, including how the front scale enters your sampling "
            "and validation choices, and how you would detect a front that moves at the "
            "wrong speed even when the total loss looks small."
        ),
        "tags_add": ["traveling_front", "scale_separation"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [],   # 前沿尺度公式的自洽核验留 v0.5（高精确率 patterns 难写）
        "cap_rules_mode": "add",
        "cap_rules": [
            {"rule_id": "cap_no_front_scale_link", "trigger": "cue",
             "condition": "does not connect the reaction-diffusion balance to any concrete sampling or validation decision",
             "affected_facets": ["training_strategy"], "max_score": 3,
             "rationale": "The front scale is the task-specific content; ignoring it is generic text."},
            {"rule_id": "cap_validation_blind_to_front_speed", "trigger": "cue",
             "condition": "validation cannot detect a wrong front speed (no front-position tracking, no comparison against the theoretical or reference speed)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Front speed error is the canonical silent failure for this problem class."},
        ],
        "failure_traps_add": [
            "ignores front scale in sampling",
            "validation blind to wrong front speed",
        ],
        "critical_points_add": {
            "training_strategy": ["links front width sqrt(d/r) to sampling density"],
            "validation_failure_risks": ["tracks front position/speed against the theoretical value 2*sqrt(d*r)"],
        },
        "set": {
            "canonical_pde": "u_t = d*u_xx + r*u*(1-u) (Fisher-KPP reference instance)",
            "parameter_values": {"d": "0.01", "r": "1.0",
                                 "front_speed_theory": "2*sqrt(d*r) = 0.2",
                                 "front_width_scale": "sqrt(d/r) = 0.1"},
        },
    },
},

# ─────────────────────────────────────────────────────── 007 → L 形域重定位
"easy_laplace_2d_boundary_007": {
    "revision": "relocated",
    "public": {
        "id": "medium_laplace_L_corner_007r",
        "difficulty": "medium",
        "pde_system": "2D Laplace equation on an L-shaped domain",
        "tags": ["2d", "elliptic_pde", "corner_singularity", "l_shaped_domain",
                 "boundary_value_problem", "pinn"],
        "source_provenance_note": "Classic L-shaped-domain corner-singularity benchmark, adapted as a natural-language planning task; no numerical data copied.",
        "problem": (
            "An engineer needs the steady-state potential field in a two-dimensional "
            "L-shaped region (a square with one quadrant removed). There are no internal "
            "sources, and Dirichlet values are prescribed on the whole boundary. Note "
            "that the re-entrant corner makes the exact solution non-smooth: its "
            "gradient is unbounded at that corner. Design a physics-informed modeling "
            "workflow for this boundary value problem. Explain how your representation "
            "and sampling treat the corner singularity, why a standard smooth network "
            "trained on uniform collocation may fail there, and how you will measure "
            "solution quality near the corner separately from the rest of the domain."
        ),
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "supersedes": ["easy_laplace_2d_boundary_007"],
        "verifiable_claims": [_corner_exponent_claim("cap_wrong_exponent")],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_no_corner_mechanism", "trigger": "cue",
             "condition": "treats the domain as smooth and applies uniform collocation with a plain MLP without any corner-specific mechanism",
             "affected_facets": ["model_choice", "training_strategy"], "max_score": 2,
             "rationale": "The corner singularity is the decision pivot of this task."},
            {"rule_id": "cap_wrong_exponent", "trigger": "claim",
             "condition": "states a corner-singularity exponent inconsistent with the re-entrant angle (theory: 2/3 for the 3*pi/2 corner)",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "Hallucinated specification: the exponent is determined by the public geometry."},
            {"rule_id": "cap_global_metric_only", "trigger": "cue",
             "condition": "validation reports only a global error metric with no corner-local assessment",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Global metrics hide the corner failure this task is about."},
        ],
        "failure_traps_replace": [
            "uniform collocation with plain smooth MLP and no corner mechanism",
            "states a corner-singularity exponent inconsistent with the re-entrant angle",
            "only global error metric, no corner-local assessment",
        ],
        "critical_points_set": {
            "problem_formalization": [
                "identifies the Laplace boundary value problem on an L-shaped (re-entrant corner) domain",
                "states that the exact solution has an r^(2/3)-type singularity with unbounded gradient at the corner",
            ],
            "physics_constraints": [
                "Laplace residual plus Dirichlet boundary enforcement on all boundary segments",
                "does not assume global smoothness of the solution",
            ],
            "model_choice": [
                "chooses a corner-aware mechanism (local refinement, singular enrichment r^(2/3)-type basis, domain decomposition, or gradient-weighted sampling)",
                "explains why a plain spectrally-biased smooth network fails near the corner",
            ],
            "training_strategy": [
                "collocation plan concentrates points near the re-entrant corner",
                "handles the unbounded gradient (loss weighting or enrichment) explicitly",
            ],
            "validation_failure_risks": [
                "reports corner-neighborhood error separately from the bulk",
                "checks against the analytic singular solution or a refined reference near the corner",
            ],
        },
        "set": {
            "canonical_pde": "Laplace equation: u_xx + u_yy = 0 on the L-shaped domain",
            "variables": ["x", "y", "u(x,y)"],
            "known_parameters": ["domain geometry (L-shape)", "Dirichlet boundary data"],
            "unknowns": ["u(x,y)"],
            "domain_spec": {"space": "L-shape: [-1,1]^2 minus the closed quadrant [0,1]x[-1,0]"},
            "parameter_values": {"corner_angle": "3*pi/2", "singularity_exponent": "2/3"},
            "reference_conditions": {
                "boundary": "trace of u = r^(2/3)*sin(2*theta/3) on the L-shaped boundary (private instance)"},
            "analytic_solution": "u = r^(2/3)*sin(2*theta/3) in polar coordinates centered at the re-entrant corner",
            "constraints": {"boundary_conditions": ["Dirichlet data on the whole L-shaped boundary (trace of the singular analytic solution)"]},
        },
    },
},

# ─────────────────────────────────────────────────────── 011 源项反演
"medium_poisson_source_recovery_011": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A scientist has interior observations of a two-dimensional potential field "
            "at a limited set of locations and wants to infer an unknown source term in "
            "a Poisson equation. Boundary information is available. Be aware that with "
            "finitely many observations the source is in general not uniquely "
            "determined: different source configurations can reproduce the same "
            "observations. Design a physics-informed modeling workflow for joint field "
            "reconstruction and source recovery. State explicitly (i) how the source is "
            "represented and why that representation restores well-posedness, (ii) what "
            "regularization you add and what bias it introduces, and (iii) how the "
            "observation layout limits which source features are recoverable, including "
            "a validation design that honestly reflects those limits."
        ),
        "tags_add": ["identifiability", "regularization", "ill_posedness"],
    },
    "private": {
        "task_type_decl": "inverse",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "unique_recovery_without_regularization",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["problem_formalization", "physics_constraints"],
                "scope": "plan",
                "description": "声称唯一/精确恢复源项但全篇无正则化或限制性参数化承诺",
                "pattern": r"\b(?:unique(?:ly)?|exact(?:ly)?)\s+(?:recover|reconstruct|determin|identif)\w*",
                "support_patterns": [
                    r"regulariz", r"tikhonov", r"sparsit|sparse", r"\bprior\b",
                    r"penalt", r"\bbasis\b", r"low[- ]dimensional|low[- ]rank",
                    r"parameteriz\w*[^.]{0,50}(?:restrict|constrain|coarse|limit)",
                ],
                "on_contradiction": "cap_unique_recovery",
                "selftest": {
                    "gold": "With Tikhonov regularization and a coarse radial-basis parameterization, the source is uniquely determined within that restricted class.",
                    "tamper": "Our method exactly recovers the true source from the interior observations, so no further assumptions are needed.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_unique_recovery", "trigger": "claim",
             "condition": "claims unique or exact source recovery from the stated partial observations without any regularization or restrictive parameterization",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "The prompt states non-uniqueness; the claim contradicts the specification."},
            {"rule_id": "cap_no_identifiability_rationale", "trigger": "cue",
             "condition": "the source representation (network, basis, grid) is chosen without any identifiability rationale",
             "affected_facets": ["model_choice"], "max_score": 3,
             "rationale": "Representation choice is exactly where well-posedness is restored or lost."},
            {"rule_id": "cap_source_never_validated", "trigger": "cue",
             "condition": "validation evaluates only the reconstructed field and never the recovered source against held-out information (or does not acknowledge that source error cannot be fully validated without ground truth)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Field fit does not certify source recovery under non-uniqueness."},
        ],
        "failure_traps_add": [
            "claims unique recovery without regularization",
            "no identifiability rationale for source representation",
            "validates field only, never the source",
        ],
        "critical_points_add": {
            "problem_formalization": [
                "states the ill-posedness/non-uniqueness of source recovery from partial observations",
            ],
        },
        "set": {
            "parameter_values": {
                "source_instance": "two-lobe Gaussian mixture (private)",
                "n_observations": "24 interior points",
                "underdetermination_note": "source dof >> observation count in the unrestricted class",
            },
        },
    },
},

# ─────────────────────────────────────────────────────── 012 稀疏传感器波场
"medium_wave_sparse_sensors_012": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A team has sparse sensor measurements of a one-dimensional wave field over "
            "a time window. The wave speed is known, but neither initial conditions nor "
            "boundary conditions are provided. Whether the field is recoverable at all "
            "depends on how the sensor locations and the recording window relate to the "
            "domain of dependence of the wave equation. Design a physics-informed "
            "modeling workflow that (i) states a concrete sufficiency argument — in "
            "terms of wave speed, sensor positions, and window length — for which part "
            "of the space-time domain is recoverable, (ii) declares every assumption "
            "made about the unprovided initial and boundary information, and (iii) "
            "specifies what the workflow reports for regions it cannot constrain. Plans "
            "that silently assume full initial or boundary data are not acceptable."
        ),
        "tags_add": ["observability", "data_assimilation", "underdetermined"],
    },
    "private": {
        "task_type_decl": "inverse",
        "human_review": DRAFT_HR,
        "verifiable_claims": [],   # 全 cue 题：锥覆盖对账需要几何推理，v0.4 正则做不到高精确率
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_hallucinated_icbc", "trigger": "cue",
             "condition": "assumes complete initial or boundary conditions that the prompt does not provide, without labeling them as assumptions and without stating how the workflow changes if they are unavailable",
             "affected_facets": ["problem_formalization"], "max_score": 2,
             "rationale": "Hallucinated specification — the prompt explicitly withholds IC/BC."},
            {"rule_id": "cap_no_observability_argument", "trigger": "cue",
             "condition": "no sufficiency/observability argument connects sensors, wave speed, and window to the claimed reconstruction",
             "affected_facets": ["problem_formalization", "validation_failure_risks"], "max_score": 3,
             "rationale": "The observability argument is the explicit deliverable of the task."},
            {"rule_id": "cap_recovery_beyond_cones", "trigger": "cue",
             "condition": "claims to reconstruct the entire space-time field from sensors whose domains of influence provably do not cover it",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "Contradicts finite-speed propagation."},
        ],
        "failure_traps_add": [
            "silently assumes full IC/BC",
            "no observability argument",
            "claims full-field recovery beyond sensor influence cones",
        ],
        "critical_points_add": {
            "problem_formalization": [
                "argues recoverability via domains of dependence/influence (c·t cones) of the sensor set and window",
                "labels every assumption about the missing IC/BC as an assumption",
            ],
        },
        "set": {
            "parameter_values": {"c": "1.0", "sensors": "4 equally spaced interior sensors (private layout)",
                                 "window": "T = 2.0"},
            "reference_conditions": {
                "recoverable_region": "computed union of sensor influence cones for the private layout (reference computation, private)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 013 噪声双物种
"medium_reaction_diffusion_noisy_013": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A biophysics group studies a two-species reaction-diffusion process with a "
            "known coupled reaction form. Species A is observed at scattered space-time "
            "locations with noise whose magnitude is roughly proportional to the local "
            "concentration; species B is not observed at all. Design a physics-informed "
            "modeling workflow that fits both concentration fields. State explicitly "
            "(i) how the stated noise structure enters your objective — an unweighted "
            "mean-squared data loss is not a neutral default here, (ii) through which "
            "terms of the coupled dynamics the unobserved species is constrained, and "
            "under what conditions it would not be recoverable, and (iii) a validation "
            "design that does not reward overfitting the noisy observations of A."
        ),
        "tags_add": ["heteroscedastic_noise", "unobserved_species", "coupled_system"],
    },
    "private": {
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "unweighted_mse_under_stated_noise",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["training_strategy"],
                "scope": "plan",
                "description": "在题面声明比例噪声的前提下使用未加权 MSE 数据损失且无加权/似然论证",
                "pattern": r"(?:standard|plain|unweighted|simple|ordinary)\s+(?:mse|mean[- ]squared[- ]error)|(?:mse|mean[- ]squared[- ]error)\s+(?:data|observation)\s+loss",
                "support_patterns": [
                    r"heteroscedast", r"weight", r"likelihood", r"inverse[- ]variance",
                    r"proportional[- ]noise", r"noise[- ]aware", r"variance[- ]scaled",
                ],
                "on_contradiction": "cap_unweighted_loss",
                "selftest": {
                    "gold": "The data loss is inverse-variance weighted, consistent with the stated concentration-proportional noise.",
                    "tamper": "We fit species A with a standard MSE data loss on all observations plus the PDE residual.",
                },
            },
            {
                "claim_id": "treats_b_as_observed",
                "type": "forbidden_assertion",
                "basis": "spec",
                "facets": ["problem_formalization", "physics_constraints"],
                "scope": "plan",
                "description": "把无观测的物种 B 当作有观测数据使用（规格：B 完全无观测）",
                "patterns": [
                    r"observations?\s+(?:of|for)\s+(?:species\s+)?b\b",
                    r"\bspecies\s+b\b[^.]{0,40}\b(?:is|are)\s+observed",
                    r"data\s+(?:for|on)\s+(?:species\s+)?b\b",
                    r"measurements?\s+of\s+(?:species\s+)?b\b",
                ],
                "on_contradiction": "cap_b_observed",
                "selftest": {
                    "gold": "Species B has no observations at all; it is constrained only through the coupling terms of the reaction dynamics.",
                    "tamper": "We additionally use the scattered observations of species B to anchor the joint fit.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_unweighted_loss", "trigger": "claim",
             "condition": "uses an unweighted data loss while the prompt states concentration-proportional noise, and gives no likelihood-based or weighting-based justification",
             "affected_facets": ["training_strategy"], "max_score": 3,
             "rationale": "Statistically wrong objective under stated heteroscedastic noise."},
            {"rule_id": "cap_b_observed", "trigger": "claim",
             "condition": "treats species B as observed, or never addresses how B is constrained despite having no data",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "Contradicts the stated observation asymmetry (hallucinated data)."},
            {"rule_id": "cap_validates_only_A_fit", "trigger": "cue",
             "condition": "validation reports only the fit to species A's noisy data (no held-out design, no physics-residual check for B)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Rewards overfitting the noise; B remains unvalidated."},
        ],
        "failure_traps_add": [
            "unweighted MSE under stated heteroscedastic noise",
            "treats unobserved species as observed",
            "validates only on A's noisy fit",
        ],
        "critical_points_add": {
            "training_strategy": [
                "maps the stated proportional-noise model to a weighted or likelihood-based data objective",
            ],
            "problem_formalization": [
                "states through which coupling terms species B is constrained and when it is not recoverable",
            ],
        },
        "set": {
            "constraints": {
                "observations": "species A: scattered space-time observations, noise magnitude proportional to local concentration (coefficient private); species B: completely unobserved",
            },
            "parameter_values": {"noise_coefficient": "0.1 (proportional, private instance)",
                                 "coupling": "Schnakenberg-type, moderate strength (private instance)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 014 混合 BC（兼并 001）
"medium_heat_mixed_bc_014": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A researcher models heat conduction in a one-dimensional rod. One end is "
            "held at a fixed temperature. At the other end, heat is injected into the "
            "rod at a prescribed constant rate through the boundary surface. The initial "
            "temperature profile is known, and the material properties are given. Design "
            "a physics-informed modeling workflow for the temperature field. Make the "
            "boundary treatment fully explicit: write the flux condition as a signed "
            "relation between the outward normal derivative and the stated injection "
            "rate, and explain how you verify the sign is physically correct. Include in "
            "your validation an energy-balance check relating the change of total "
            "thermal energy in the rod to the boundary fluxes, with a tolerance."
        ),
        "tags_add": ["neumann_flux_injection", "energy_balance"],
    },
    "private": {
        "task_type_decl": "forward",
        "supersedes": ["easy_heat_1d_dirichlet_001"],
        "human_review": "RESOLVED v0.4: sign convention k*u_x(1,t)=+q_in confirmed (outward normal, injection positive); instance values q_in/alpha/IC pending author finalization",
        "verifiable_claims": [
            {
                "claim_id": "flux_sign",
                "type": "sign_relation",
                "basis": "spec",
                "facets": ["physics_constraints"],
                "scope": "plan",
                "description": "计划写出的右端通量条件符号必须与'注入'方向一致（外法向约定）",
                "quantity": "k*u_x(1,t) vs q_in",
                "canonical": "+",
                "sign_patterns": [
                    r"([+-]?)\s*k\s*\*?\s*(?:u_x|du/dx|du/dn|u_n)\s*\(?\s*(?:1|l)?\s*,?\s*t?\s*\)?\s*=\s*([+-]?)\s*q",
                ],
                "on_contradiction": "cap_flux_sign",
                "selftest": {
                    "gold": "At the heated end we impose k*u_x(1,t) = +q_in, consistent with injection under the outward normal n = +x.",
                    "tamper": "At the heated end we impose -k*u_x(1,t) = q_in for the prescribed injection rate.",
                },
            },
            {
                "claim_id": "flux_as_value_constraint",
                "type": "co_occurrence",
                "basis": "plan_internal",
                "facets": ["physics_constraints", "training_strategy"],
                "scope": "facet",
                "description": "通量条件被当作 u 的值约束施加（而非法向导数约束）",
                "pattern_a": r"u\s*\(\s*(?:1|l)\s*,\s*t\s*\)\s*=\s*q",
                "pattern_b": r"\b(?:flux|neumann|injection)\b",
                "on_contradiction": "cap_flux_as_value",
                "selftest": {
                    "gold": "The flux condition k*u_x(1,t) = q_in is enforced through automatic differentiation of the network output.",
                    "tamper": "We enforce the flux by setting u(1,t) = q_in as a boundary value constraint.",
                },
            },
            {
                "claim_id": "alpha_value",
                "type": "param_value",
                "basis": "spec",
                "facets": ALL_FACETS,
                "description": "计划若断言具体 alpha 数值，须与私有实例一致（公开题面无数值）",
                "param": "alpha",
                "true_value": 1.0,
                "rtol": 0.01,
                "patterns": [
                    r"(?:thermal\s+)?diffusivity\s+(?:alpha\s+)?(?:=|of|:)\s*" + NUM,
                    r"\balpha\s*(?:=|:)\s*" + NUM,
                ],
                "on_contradiction": "cap_hallucinated_value",
                "selftest": {
                    "gold": "Writing the heat equation u_t = alpha*u_xx with the given material diffusivity (alpha = 1.0 in the reference instance).",
                    "tamper": "We take the thermal diffusivity alpha = 0.01, typical for such materials.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_flux_sign", "trigger": "claim",
             "condition": "flux boundary condition stated without an explicit sign convention tied to the outward normal, or with a sign inconsistent with the stated physical direction of heat flow",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 2,
             "rationale": "Sign error turns heating into cooling; execution necessarily diverges from the reference."},
            {"rule_id": "cap_flux_as_value", "trigger": "claim",
             "condition": "flux condition enforced as a value constraint on u rather than on its normal derivative",
             "affected_facets": ["physics_constraints"], "max_score": 2,
             "rationale": "Mistakes the mathematical type of the boundary condition."},
            {"rule_id": "cap_no_energy_balance", "trigger": "cue",
             "condition": "validation contains no energy-balance or flux-consistency check",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "The energy budget d/dt integral(u) = net boundary flux is the fundamental consistency check for this task."},
            {"rule_id": "cap_hallucinated_value", "trigger": "claim",
             "condition": "plan asserts a specific numeric value contradicting the private instance (the public statement contains no numbers)",
             "affected_facets": [], "max_score": 2,
             "rationale": "Hallucinated specification values."},
            {"rule_id": "cap_same_bc_type", "trigger": "cue",
             "condition": "treats both boundaries as the same type",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 2,
             "rationale": "The stress test is mixed BC handling."},
        ],
        "failure_traps_replace": [
            "treats both boundaries as Dirichlet",
            "omits derivative boundary loss",
            "omits initial condition",
            "flux sign inconsistent with stated direction",
            "flux enforced as value constraint",
            "no energy balance validation",
        ],
        "critical_points_set": {
            "problem_formalization": [
                "identifies 1D heat equation with mixed Dirichlet/flux boundary conditions",
                "translates 'heat injected' into a signed normal-derivative condition",
                "states the outward-normal sign convention explicitly",
            ],
            "physics_constraints": [
                "includes heat residual and initial-condition loss",
                "includes Dirichlet value loss at x=0",
                "includes signed flux (Neumann derivative) loss at x=1 with correct sign",
                "does not enforce the flux as a value constraint on u",
            ],
            "model_choice": [
                "chooses PINN with autodiff for the boundary derivative",
                "justifies how the derivative constraint is represented",
            ],
            "training_strategy": [
                "samples interior, initial, Dirichlet-boundary, and flux-boundary points",
                "balances derivative and value boundary losses",
                "verifies the flux sign against the physical direction before training",
            ],
            "validation_failure_risks": [
                "energy-balance check: rate of change of total thermal energy vs net boundary flux, with tolerance",
                "field error against the series/steady reference",
                "separate Dirichlet and flux boundary errors",
                "names flux sign error as an explicit failure risk",
            ],
        },
        "set": {
            "known_parameters": ["alpha = 1.0", "k = 1.0", "q_in = 0.5"],
            "constraints": {
                "initial_condition": "u(x,0) is given; reference instance: u(x,0)=0",
                "boundary_conditions": [
                    "Dirichlet u(0,t)=0 at the left end",
                    "flux injection at the right end: k*u_x(1,t) = q_in, i.e. outward flux -k*u_x(1,t) = -q_in with outward normal n = +x",
                ],
            },
            "parameter_values": {"alpha": "1.0", "k": "1.0", "q_in": "0.5"},
            "reference_conditions": {
                "initial": "u(x,0)=0",
                "boundary": ["u(0,t)=0", "k*u_x(1,t) = +0.5 (injection)"],
            },
            "analytic_solution": "steady state u_s(x) = q_in*x/k plus classical eigenfunction transient series for the reference instance",
        },
        "expected_validation_add": [
            "energy-balance check: d/dt of total thermal energy vs net boundary flux, with tolerance",
        ],
    },
},

# ─────────────────────────────────────────────────────── 015 双周期（枚举升级）
"medium_periodic_advdiff_015": {
    "revision": "light_edit",
    "public": {
        "problem": (
            "A scientist wants to model a scalar field governed by advection and "
            "diffusion on a one-dimensional domain whose endpoints are physically "
            "identified. The initial profile is compatible with this topology, and the "
            "solution should remain compatible with it over time. Design a "
            "physics-informed modeling workflow. Enumerate, as an explicit list, every "
            "endpoint constraint your workflow enforces, and for each one state whether "
            "it is enforced softly (as a penalty), by construction (via the "
            "representation), or not at all — and why the diffusive term makes the list "
            "you chose sufficient."
        ),
        "tags_add": ["constraint_enumeration"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "value_only_periodicity",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["physics_constraints", "training_strategy"],
                "scope": "plan",
                "description": "只枚举值周期约束，无导数/通量周期且无构造性（周期嵌入）论证",
                "pattern": r"u\s*\(\s*0\s*(?:,\s*t)?\s*\)\s*=\s*u\s*\(\s*(?:1|l)\s*(?:,\s*t)?\s*\)|value\s+periodic|periodic\s+(?:value|boundary)\s+(?:constraint|condition)",
                "support_patterns": [
                    r"(?:derivative|flux|u_x|gradient|first[- ]order)[^.]{0,80}period",
                    r"period\w*[^.]{0,80}(?:derivative|flux|u_x|gradient)",
                    r"u_x\s*\(\s*0[^)]*\)\s*=\s*u_x\s*\(\s*(?:1|l)",
                    r"(?:sin|cos|fourier|trigonometric|periodic)[^.]{0,60}(?:embedding|feature|input|encoding)",
                    r"by\s+construction",
                ],
                "on_contradiction": "cap_value_only_periodicity",
                "selftest": {
                    "gold": "Constraints enforced: (1) u(0,t) = u(1,t), softly as a penalty; (2) u_x(0,t) = u_x(1,t), softly — the diffusive term requires flux continuity across the identified endpoints.",
                    "tamper": "Constraints enforced: u(0,t) = u(1,t) as a soft penalty; endpoint values remain identified throughout training.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_fixed_boundary_values", "trigger": "cue",
             "condition": "uses fixed boundary values instead of identified-endpoint periodic constraints",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 2,
             "rationale": "Wrong topology (carried over from v0.3)."},
            {"rule_id": "cap_value_only_periodicity", "trigger": "claim",
             "condition": "mentions only value periodicity and ignores derivative or diffusive-flux periodicity (and gives no constructive-embedding argument)",
             "affected_facets": ["physics_constraints", "training_strategy", "validation_failure_risks"], "max_score": 3,
             "rationale": "The diffusive term makes C^1 endpoint identification necessary (v0.3 rule, detection upgraded from cue to claim)."},
        ],
        "critical_points_set": {
            "physics_constraints": [
                "enumerates endpoint value identification u(0,t) = u(1,t)",
                "enumerates first-derivative/diffusive-flux identification u_x(0,t) = u_x(1,t), or satisfies both by a periodic construction and says so",
            ],
        },
        "expected_loss_terms_note": "constraints may instead be satisfied by construction via a periodic embedding — the plan must then declare this under Model Choice (no loss term expected in that case)",
    },
},

# ─────────────────────────────────────────────────────── 017 Cahn-Hilliard
"hard_cahn_hilliard_017": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A researcher wants to model a conserved phase-field process governed by a "
            "Cahn-Hilliard-type equation. The order parameter evolves through a "
            "chemical-potential-driven mechanism, total phase mass must not drift, and "
            "sharp interfaces may form. Design a physics-informed modeling workflow. "
            "Specify precisely (i) the complete list of fields your network(s) output, "
            "(ii) the complete list of residual equations you train on, written so that "
            "the derivative order of each residual is unambiguous, and (iii) how mass "
            "conservation is monitored quantitatively over the simulated horizon. If "
            "you train directly on the fourth-order form, justify the differentiation "
            "cost and conditioning consequences explicitly."
        ),
        "tags_add": ["mixed_formulation", "structural_commitment"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "nominal_chemical_potential",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["model_choice", "training_strategy"],
                "scope": "plan",
                "description": "口头提及化学势 μ 但输出/残差结构中不含它（口头分裂陷阱）",
                "pattern": r"chemical\s+potential|\bmu\b",
                "support_patterns": [
                    r"(?:output|predict)s?[^.]{0,80}(?:mu\b|chemical\s+potential)",
                    r"(?:mu\b|chemical\s+potential)[^.]{0,60}(?:as|is)[^.]{0,40}(?:an?\s+)?(?:output|field|network|variable)",
                    r"auxiliary\s+(?:network|field|variable|output)",
                    r"(?:two|second)[- ]?(?:equation|order)\s+(?:coupled\s+)?system",
                    r"coupled[^.]{0,40}(?:second[- ]order|two)[^.]{0,40}(?:residual|equation)",
                    r"split(?:ting)?\s+(?:form|scheme|formulation)",
                    r"mixed\s+formulation",
                ],
                "on_contradiction": "cap_nominal_splitting",
                "selftest": {
                    "gold": "We adopt a mixed formulation: the network outputs (u, mu) and we train on two coupled second-order residuals, u_t = div(M*grad(mu)) and mu = f'(u) - eps^2*lap(u).",
                    "tamper": "The dynamics are driven by the chemical potential; we train a single network for u on the fourth-order residual directly.",
                },
            },
            {
                "claim_id": "conservation_without_tolerance",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["validation_failure_risks"],
                "scope": "plan",
                "description": "声称监控质量守恒但无漂移阈值/容差（守恒承诺不可证伪）",
                "pattern": r"mass\s+(?:conservation|is\s+conserved)|conserv\w*[^.]{0,40}\bmass\b|total\s+(?:phase\s+)?mass",
                "support_patterns": [
                    r"toleran", r"threshold", r"drift[^.]{0,60}(?:below|under|<|bound)",
                    r"[0-9]+(?:\.[0-9]+)?\s*%", r"1e-[0-9]", r"10\^\{?-",
                ],
                "on_contradiction": "cap_conservation_no_tolerance",
                "selftest": {
                    "gold": "We monitor total phase mass over the horizon and require the drift to stay below a tolerance of 1e-3 relative to the initial mass.",
                    "tamper": "Total phase mass is monitored during training to confirm the conserved dynamics are respected.",
                },
            },
        ],
        "cap_rules_mode": "add",
        "cap_rules": [
            {"rule_id": "cap_nominal_splitting", "trigger": "claim",
             "condition": "invokes the chemical potential verbally but the declared network outputs and residual list do not contain it (and the residual remains a single fourth-order equation)",
             "affected_facets": ["model_choice", "training_strategy"], "max_score": 3,
             "rationale": "Nominal-splitting trap: mentioning mu is not a structural commitment."},
            {"rule_id": "cap_conservation_no_tolerance", "trigger": "claim",
             "condition": "claims mass-conservation monitoring without any drift tolerance or threshold",
             "affected_facets": ["validation_failure_risks"], "max_score": 4,
             "rationale": "A conservation promise without a falsifiable threshold is template text."},
        ],
        "failure_traps_add": [
            "nominal chemical potential (mentioned but not an output/residual)",
            "conservation claimed without drift tolerance",
        ],
        "critical_points_set": {
            "model_choice": [
                "declares the complete set of network output fields (u alone, or (u, mu))",
                "declares the complete residual list with the derivative order of each residual unambiguous",
                "if direct fourth-order: justifies autograd cost and conditioning; if split: two residuals of order <= 2 with mu as an explicit output",
            ],
        },
        "set": {
            "parameter_values": {"epsilon": "0.02", "M": "1.0",
                                 "instance": "1D Cahn-Hilliard, spectral reference (reuses task-016 infrastructure)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 018 NS 压力规范
"hard_navier_stokes_2d_018": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A fluid dynamics group wants to reconstruct a two-dimensional "
            "incompressible flow from partial velocity observations. Pressure is not "
            "observed anywhere. The model must respect momentum balance and "
            "incompressibility; boundary and initial conditions are available only "
            "partially. Design a physics-informed modeling workflow for velocity and "
            "pressure. Address explicitly: (i) to what extent the pressure field is "
            "determined by the available information, and what your workflow adds to "
            "make it unique; (ii) whether incompressibility is enforced by penalty or "
            "by construction, and — if by penalty — how divergence drift is monitored "
            "and bounded; (iii) which parts of your validation would detect a spurious "
            "pressure mode that leaves the velocity fit unchanged."
        ),
        "tags_add": ["pressure_gauge", "identifiability", "divergence_control"],
    },
    "private": {
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "absolute_pressure_from_velocity",
                "type": "forbidden_assertion",
                "basis": "spec",
                "facets": ["problem_formalization"],
                "scope": "plan",
                "description": "声称仅凭速度观测恢复绝对压力（压力仅确定到相差常数）",
                "patterns": [
                    r"recover(?:ing|s)?\s+(?:the\s+)?absolute\s+pressure",
                    r"absolute\s+pressure[^.]{0,50}from\s+(?:the\s+)?velocity",
                    r"uniquely\s+(?:recover|determine)s?\s+(?:the\s+)?pressure\b(?![^.]{0,40}(?:up\s+to|gauge|constant))",
                ],
                "on_contradiction": "cap_absolute_pressure",
                "selftest": {
                    "gold": "Pressure is determined only up to an additive constant; we pin p at a reference point to fix the gauge.",
                    "tamper": "The workflow recovers the absolute pressure field from the velocity observations alone.",
                },
            },
            {
                "claim_id": "soft_divergence_without_monitoring",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["validation_failure_risks"],
                "scope": "plan",
                "description": "软惩罚施加不可压但全篇无散度监控/漂移界（承诺缺口）",
                "pattern": r"(?:incompressib|diverg|continuity)\w*[^.]{0,60}(?:soft\s+)?penalt|soft(?:ly)?\s+enforc\w*[^.]{0,50}(?:incompressib|diverg|continuity)|continuity\s+(?:residual\s+)?loss",
                "support_patterns": [
                    r"diverg\w*[^.]{0,60}(?:monitor|check|report|drift|bound)",
                    r"monitor\w*[^.]{0,60}diverg",
                    r"stream\s*function", r"by\s+construction", r"divergence[- ]free\s+(?:by|via)",
                ],
                "on_contradiction": "cap_soft_div_no_monitoring",
                "selftest": {
                    "gold": "Incompressibility enters as a penalty; we monitor the divergence residual on a held-out grid and bound its drift during training.",
                    "tamper": "Incompressibility is enforced with a soft continuity penalty alongside the momentum residuals and the data loss.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_no_gauge", "trigger": "cue",
             "condition": "outputs pressure but neither fixes a gauge (reference point, zero-mean constraint, or boundary pressure condition) nor adopts a pressure-free formulation",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 3,
             "rationale": "Un-gauged pressure makes the optimization problem degenerate."},
            {"rule_id": "cap_absolute_pressure", "trigger": "claim",
             "condition": "claims to recover absolute pressure values from velocity observations alone",
             "affected_facets": ["problem_formalization"], "max_score": 2,
             "rationale": "Identifiability error: pressure is determined only up to a constant."},
            {"rule_id": "cap_soft_div_no_monitoring", "trigger": "claim",
             "condition": "incompressibility is enforced only as a soft penalty and validation includes no divergence monitoring",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Soft constraints require monitoring; otherwise divergence drift is invisible."},
        ],
        "failure_traps_add": [
            "no pressure gauge fixing",
            "claims absolute pressure from velocity data",
            "soft divergence penalty without monitoring",
        ],
        "critical_points_add": {
            "problem_formalization": [
                "states that pressure is determined only up to an additive constant and fixes a gauge (or adopts a pressure-free formulation)",
            ],
        },
        "set": {
            "unknowns": ["u(x,y,t)", "v(x,y,t)", "p(x,y,t) up to an additive constant"],
            "parameter_values": {"instance": "Taylor-Green vortex, nu = 0.01 (private reference; execution-validity candidate)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 019 Darcy 保守形式
"hard_darcy_heterogeneous_019": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A geoscience team models steady Darcy flow through a porous medium whose "
            "permeability field is known but piecewise-heterogeneous: it contains "
            "sharp, channel-like contrasts across internal interfaces where the "
            "permeability jumps by orders of magnitude. Boundary conditions are "
            "available. Design a physics-informed modeling workflow for the hydraulic "
            "head. Make explicit (i) the exact differential or integral form of the "
            "residual you train on, and why it remains mathematically valid where the "
            "permeability is not differentiable, (ii) what is continuous across a "
            "permeability interface and what is not, and how your representation and "
            "sampling respect that, and (iii) a validation check specific to interface "
            "behavior, not just a global error."
        ),
        "tags_add": ["conservative_form", "interface_flux", "piecewise_coefficients"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "expanded_form_without_smoothing",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["physics_constraints"],
                "scope": "plan",
                "description": "对非光滑 κ 使用展开式 κΔh+∇κ·∇h（或对 κ 求导）且无光滑化假设声明",
                "pattern": r"kappa\s*\*?\s*(?:delta|lap(?:lacian)?|nabla\^?2)\s*\(?h|nabla\s*kappa|grad(?:ient)?\s+(?:of\s+)?(?:the\s+)?(?:kappa|permeability)|expand(?:ed|ing)?\s+(?:the\s+)?(?:divergence|conservative)\s+form",
                "support_patterns": [
                    r"smooth(?:ing|ed|ness)\s+(?:assumption|approximation)",
                    r"mollif", r"smooth(?:ed|ing)\s+(?:version|surrogate)\s+of\s+(?:kappa|the\s+permeability)",
                    r"regulariz\w*[^.]{0,50}(?:kappa|permeability|coefficient)",
                ],
                "on_contradiction": "cap_illegal_expansion",
                "selftest": {
                    "gold": "We train on the conservative form div(kappa*grad(h)) in weak/integral form, so kappa is never differentiated across the interfaces.",
                    "tamper": "We expand the residual as kappa*lap(h) + nabla kappa . nabla h and sample collocation points uniformly.",
                },
            },
            {
                "claim_id": "head_normal_derivative_continuity",
                "type": "forbidden_assertion",
                "basis": "spec",
                "facets": ["physics_constraints"],
                "scope": "plan",
                "description": "断言水头法向导数跨界面连续（正确物理是法向通量 κ∂h/∂n 连续）",
                "patterns": [
                    r"normal\s+derivative[^.]{0,40}\b(?:is|are|remains|stays)\s+continuous",
                    r"both\s+(?:the\s+)?head\s+and\s+its\s+normal\s+derivative\s+are\s+continuous",
                    r"continuity\s+of\s+the\s+normal\s+derivative",
                ],
                "on_contradiction": "cap_wrong_interface_physics",
                "selftest": {
                    "gold": "Across an interface the head is continuous and the normal flux kappa*dh/dn is continuous; the normal derivative itself jumps by the permeability ratio.",
                    "tamper": "Across the permeability interface both the head and its normal derivative are continuous.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_illegal_expansion", "trigger": "claim",
             "condition": "trains on an expanded form that differentiates the permeability (or applies the strong Laplacian form across interfaces) without declaring and justifying a smoothing assumption",
             "affected_facets": ["physics_constraints"], "max_score": 2,
             "rationale": "grad(kappa) does not exist on the interfaces; the expansion is mathematically invalid there."},
            {"rule_id": "cap_wrong_interface_physics", "trigger": "claim",
             "condition": "asserts continuity of the normal derivative of the head across a permeability jump (instead of continuity of the normal flux)",
             "affected_facets": ["physics_constraints"], "max_score": 2,
             "rationale": "Wrong physics: the flux kappa*dh/dn is continuous, the derivative jumps."},
            {"rule_id": "cap_no_interface_validation", "trigger": "cue",
             "condition": "validation has no interface-specific check (flux jump across interfaces, local residual concentration)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Global error hides interface failure."},
        ],
        "failure_traps_add": [
            "expands the divergence form across non-smooth kappa",
            "asserts normal-derivative continuity at interfaces",
            "no interface-specific validation",
        ],
        "critical_points_add": {
            "physics_constraints": [
                "trains on the conservative/weak form (or declares and justifies a smoothing assumption)",
                "states head continuity and normal-flux continuity (not derivative continuity) across interfaces",
            ],
        },
        "set": {
            "canonical_pde": "steady Darcy, conservative form: div(kappa(x)*grad(h)) = 0 with kappa piecewise constant (sharp channel-like contrasts)",
            "parameter_values": {"kappa_contrast": "100:1 (private instance)",
                                 "geometry": "two-zone layered medium (private instance; piecewise analytic reference exists)"},
        },
    },
},

# ─────────────────────────────────────────────────────── 020 高频 Helmholtz（轻改）
"hard_helmholtz_high_frequency_020": {
    "revision": "light_edit",
    "public": {
        "problem": (
            "A researcher wants to solve a complex-valued frequency-domain Helmholtz "
            "problem in a bounded two-dimensional domain with a known source term and "
            "prescribed boundary data. The wavelength is short relative to the domain "
            "size — the domain spans roughly twenty wavelengths in each direction — and "
            "both phase and amplitude accuracy matter. Design a physics-informed "
            "modeling workflow and discuss training and validation risks. Quantify your "
            "sampling in points per wavelength and show the resulting total budget is "
            "consistent with the stated domain-to-wavelength ratio; a named "
            "architecture without this arithmetic is not sufficient."
        ),
        "tags_add": ["points_per_wavelength", "sampling_arithmetic"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "ppw_arithmetic",
                "type": "arithmetic_consistency",
                "basis": "plan_internal",
                "facets": ["training_strategy"],
                "description": "声称的 PPW × 波长数 与总配点数的自洽（2D，容差一个数量级）",
                "quantities": {
                    "ppw": [
                        NUM + r"\s*(?:collocation\s+)?points?\s+per\s+wavelength",
                        r"ppw\s*(?:=|of|:)\s*" + NUM,
                    ],
                    "n_wl": [
                        r"(?:spans?|roughly|about|approximately|around)\s+" + NUM + r"\s+wavelengths",
                        NUM + r"\s+wavelengths\s+(?:across|in\s+each|per)",
                    ],
                    "total": POINTS_PATTERNS,
                },
                "expression": "total >= 0.1 * (ppw * n_wl)**2",
                "on_contradiction": "cap_ppw_arithmetic",
                "selftest": {
                    "gold": "We use 10 points per wavelength; the domain spans roughly 20 wavelengths in each direction, giving a total of 40,000 collocation points.",
                    "tamper": "We use 10 points per wavelength; the domain spans roughly 20 wavelengths in each direction, and a total of 2,000 collocation points suffices.",
                },
            },
            {
                "claim_id": "real_only_representation",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["problem_formalization", "physics_constraints"],
                "scope": "plan",
                "description": "声称实值表示但全篇无复数/双通道/相位处理（复值 Helmholtz 场）",
                "pattern": r"real[- ]valued\s+(?:network|output|representation|formulation|scalar)",
                "support_patterns": [
                    r"imaginary", r"complex", r"two[- ](?:output|channel|component)",
                    r"re(?:al)?\s*(?:and|&|/|,)\s*im(?:aginary)?",
                    r"phase\s+(?:variable|field|output)", r"amplitude[- ]phase",
                ],
                "on_contradiction": "cap_real_only",
                "selftest": {
                    "gold": "We use a real-valued network with two output channels for the real and imaginary parts of the field.",
                    "tamper": "We fit a single real-valued network for the field magnitude across the domain.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_arch_without_details", "trigger": "cue",
             "condition": "mentions a high-frequency architecture but omits complex-valued representation, points-per-wavelength sampling, or phase validation",
             "affected_facets": ["model_choice", "training_strategy", "validation_failure_risks"], "max_score": 3,
             "rationale": "Carried from v0.3."},
            {"rule_id": "cap_time_domain_treatment", "trigger": "cue",
             "condition": "treats Helmholtz as time-dependent wave propagation",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "Carried from v0.3."},
            {"rule_id": "cap_real_only", "trigger": "claim",
             "condition": "uses real-only scalar formulation without addressing complex phase",
             "affected_facets": ["problem_formalization", "physics_constraints", "validation_failure_risks"], "max_score": 3,
             "rationale": "v0.3 rule, detection upgraded from cue to claim (co-absence of complex handling)."},
            {"rule_id": "cap_sampling_not_scaled", "trigger": "cue",
             "condition": "training plan does not scale sampling with wavelength or wavenumber",
             "affected_facets": ["training_strategy", "validation_failure_risks"], "max_score": 3,
             "rationale": "Carried from v0.3."},
            {"rule_id": "cap_ppw_arithmetic", "trigger": "claim",
             "condition": "states a points-per-wavelength figure, a domain-to-wavelength ratio, and a total collocation budget that are mutually inconsistent by more than an order of magnitude",
             "affected_facets": ["training_strategy"], "max_score": 3,
             "rationale": "Unverified quantitative claim: the three numbers are all given by the plan itself."},
        ],
        "failure_traps_add": [
            "PPW arithmetic inconsistent",
            "real-only network with phase accuracy claim",
        ],
        "critical_points_set": {
            "training_strategy": [
                "states the arithmetic triple: points-per-wavelength, domain-to-wavelength ratio, total collocation count — mutually consistent",
                "scales sampling (and any Fourier-feature bandwidth) with the wavenumber",
            ],
        },
        "set": {
            "parameter_values": {
                "n_wavelengths_public": "approximately 20 per direction (public magnitude)",
                "k_exact": "private: k = 40*pi on the unit square (20 wavelengths per direction)",
            },
        },
    },
},

# ─────────────────────────────────────────────────────── 021 阶梯 Helmholtz
"hard_plus_helmholtz_staircase_021": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A researcher must solve a frequency-domain Helmholtz problem in a "
            "two-dimensional staircase-shaped domain: the boundary consists of many "
            "axis-aligned steps, so the domain has multiple re-entrant corners, and the "
            "domain spans roughly ten wavelengths. Source and boundary data are known. "
            "The compute budget is fixed: at most 40,000 collocation points and one "
            "network (or an explicitly justified decomposition). Design a "
            "physics-informed modeling workflow. Required content: (i) how the solution "
            "behaves at re-entrant corners and what your representation does about it, "
            "(ii) the points-per-wavelength arithmetic for the oscillatory bulk, (iii) "
            "how the fixed point budget is split between corner refinement and bulk "
            "coverage, with numbers, and (iv) a validation plan that reports corner "
            "neighborhoods separately from the bulk."
        ),
        "tags_add": ["corner_singularity", "budget_allocation", "points_per_wavelength"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            _corner_exponent_claim("cap_wrong_exponent"),
            _budget_claim(
                "budget_points", POINTS_PATTERNS, 40000, "cap_budget_inconsistent",
                "配点数",
                gold="The 40,000-point budget splits into 8,000 corner points around the re-entrant corners and 32,000 bulk points.",
                tamper="We allocate 60,000 collocation points overall to cover both the corners and the oscillatory bulk.",
            ),
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_no_corner_mechanism", "trigger": "cue",
             "condition": "applies a single smooth network with uniform collocation and no corner-specific mechanism",
             "affected_facets": ["model_choice", "training_strategy"], "max_score": 2,
             "rationale": "Corner singularities are half of the decision pivot."},
            {"rule_id": "cap_one_sided_difficulty", "trigger": "cue",
             "condition": "discusses spectral bias or Fourier features for the oscillatory bulk but never addresses the corner singularities (or vice versa)",
             "affected_facets": ["model_choice", "training_strategy"], "max_score": 3,
             "rationale": "One-sided difficulty handling; the combination is the task."},
            {"rule_id": "cap_budget_inconsistent", "trigger": "claim",
             "condition": "the stated budget split is absent or arithmetically inconsistent with the stated budget",
             "affected_facets": ["training_strategy"], "max_score": 3,
             "rationale": "The split-with-numbers is an explicit deliverable."},
            {"rule_id": "cap_wrong_exponent", "trigger": "claim",
             "condition": "states a corner-singularity exponent inconsistent with the re-entrant angle (theory: 2/3)",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 2,
             "rationale": "Hallucinated specification (shared check with task 007r)."},
            {"rule_id": "cap_global_metric_only", "trigger": "cue",
             "condition": "validation reports only a global metric",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Corner neighborhoods must be reported separately."},
        ],
        "failure_traps_replace": [
            "single smooth network, uniform collocation, no corner mechanism",
            "one-sided difficulty handling (bulk-only or corner-only)",
            "budget split absent or arithmetically inconsistent",
            "corner-singularity exponent inconsistent with re-entrant angle",
            "only global validation metric",
        ],
        "critical_points_set": {
            "problem_formalization": [
                "identifies the double difficulty: multiple re-entrant corner singularities x high-frequency bulk",
                "states the r^(2/3)-type corner behaviour",
            ],
            "physics_constraints": [
                "Helmholtz residual with complex-valued field handling",
                "boundary enforcement on all staircase segments",
            ],
            "model_choice": [
                "corner-aware mechanism (refinement/enrichment/decomposition) AND bulk bandwidth matched to the wavenumber",
                "justifies the single-network-or-decomposition choice under the budget",
            ],
            "training_strategy": [
                "points-per-wavelength arithmetic for the bulk",
                "explicit numeric split of the 40,000-point budget between corners and bulk",
            ],
            "validation_failure_risks": [
                "corner-neighborhood errors reported separately from the bulk",
                "phase/amplitude accuracy checks scaled with the wavenumber",
            ],
        },
        "set": {
            "domain_spec": {"space": "staircase polygon (private exact layout; public magnitude: multiple re-entrant corners, ~10 wavelengths across)"},
            "parameter_values": {
                "n_corners": "4 re-entrant corners (private instance)",
                "n_wavelengths_public": "approximately 10 (public magnitude); exact k private",
                "reference": "offline domain-decomposition spectral / boundary-integral reference (private)",
            },
        },
    },
},

# ─────────────────────────────────────────────────────── 022 散射迷宫
"hard_plus_acoustic_scattering_maze_022": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "An acoustics group models time-harmonic wave scattering off a maze-like "
            "arrangement of internal obstacles in an unbounded two-dimensional medium. "
            "The incident wave and the obstacle surface properties (sound-hard) are "
            "known. Since the physical domain is unbounded, any computational domain "
            "must be truncated. Design a physics-informed modeling workflow. Required "
            "content: (i) whether you solve for the total field or the scattered field, "
            "and how the incident wave enters the formulation in your choice, (ii) the "
            "boundary treatment on the obstacle surfaces and — separately — on the "
            "artificial truncation boundary, including how outgoing waves are prevented "
            "from re-entering, and (iii) a validation check that would expose spurious "
            "reflections from the truncation boundary."
        ),
        "tags_add": ["radiation_condition", "field_decomposition", "domain_truncation"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "reflecting_truncation_boundary",
                "type": "forbidden_assertion",
                "basis": "spec",
                "facets": ["physics_constraints", "model_choice"],
                "scope": "plan",
                "description": "把人工截断边界当作反射墙（Dirichlet/Neumann/刚性/零值）处理",
                "patterns": [
                    r"(?:truncation|outer|artificial|far[- ]field|computational)\s+boundar(?:y|ies)[^.;]{0,60}(?:dirichlet|neumann|reflect|rigid|hard\s+wall|zero\s+(?:value|field|pressure)|u\s*=\s*0)",
                    r"(?:dirichlet|neumann)[^.;]{0,50}(?:on|at)\s+the\s+(?:truncation|outer|artificial|far[- ]field)\s+boundar",
                    r"(?:impose|set|apply)\s+u\s*=\s*0\s+(?:on|at)\s+the\s+(?:outer|truncation|artificial)",
                ],
                "on_contradiction": "cap_reflecting_truncation",
                "selftest": {
                    "gold": "On the truncation boundary we apply a PML so outgoing waves are absorbed; the obstacle surfaces are sound-hard (homogeneous Neumann).",
                    "tamper": "We treat the outer truncation boundary as a homogeneous Dirichlet wall to close the computational domain.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_reflecting_truncation", "trigger": "claim",
             "condition": "the truncation boundary is treated as a reflecting (Dirichlet or Neumann) wall",
             "affected_facets": ["physics_constraints", "model_choice"], "max_score": 2,
             "rationale": "Physically wrong: spurious reflections contaminate the whole domain."},
            {"rule_id": "cap_no_absorbing_treatment", "trigger": "cue",
             "condition": "no absorbing/radiation treatment (PML, ABC, Sommerfeld approximation, boundary integral) is specified for the truncation boundary at all",
             "affected_facets": ["physics_constraints", "model_choice"], "max_score": 2,
             "rationale": "Radiation treatment is the binary gate of open-domain scattering."},
            {"rule_id": "cap_no_field_decomposition", "trigger": "cue",
             "condition": "never distinguishes total-field from scattered-field formulation, or injects the incident wave inconsistently with its stated choice",
             "affected_facets": ["problem_formalization", "physics_constraints"], "max_score": 3,
             "rationale": "The decomposition determines how the source and BCs enter."},
            {"rule_id": "cap_conflated_bcs", "trigger": "cue",
             "condition": "obstacle boundary conditions and truncation boundary conditions are conflated into one treatment",
             "affected_facets": ["physics_constraints"], "max_score": 2,
             "rationale": "The two boundary families are physically different."},
            {"rule_id": "cap_no_reflection_validation", "trigger": "cue",
             "condition": "validation cannot detect spurious reflections (no energy-flux check, no comparison of near-field pattern against a reference/analytic case)",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Spurious reflection is the canonical silent failure here."},
        ],
        "failure_traps_replace": [
            "truncation boundary treated as reflecting wall",
            "no absorbing/radiation treatment specified",
            "total/scattered field formulation never distinguished or inconsistently used",
            "obstacle and truncation boundary conditions conflated",
            "validation cannot detect spurious reflections",
        ],
        "critical_points_set": {
            "problem_formalization": [
                "declares total-field vs scattered-field formulation and how the incident wave enters",
                "recognizes the domain truncation and its radiation requirement",
            ],
            "physics_constraints": [
                "Helmholtz residual for the chosen formulation",
                "sound-hard (Neumann) condition on obstacle surfaces; absorbing treatment (PML/ABC/Sommerfeld) on the truncation boundary — separately",
                "if scattered-field: obstacle condition uses the incident-field trace (du_s/dn = -du_inc/dn for sound-hard)",
            ],
            "model_choice": [
                "representation supports complex-valued oscillatory fields",
                "PML/ABC region handled in the architecture or loss",
            ],
            "training_strategy": [
                "samples obstacle boundary, truncation boundary, and interior separately",
                "wavelength-aware sampling in the maze channels",
            ],
            "validation_failure_risks": [
                "a check exposing spurious reflections (energy flux through the truncation boundary, or comparison against the single-cylinder analytic case)",
                "near-field pattern validation",
            ],
        },
        "set": {
            "canonical_pde": "time-harmonic Helmholtz, scattered-field reference formulation: lap(u_s) + k^2*u_s = 0 outside obstacles",
            "constraints": {
                "boundary_conditions": [
                    "obstacle surfaces (sound-hard): du/dn = 0 for the total field, i.e. du_s/dn = -du_inc/dn",
                    "truncation boundary: absorbing/radiation treatment (reference uses PML)",
                ],
            },
            "parameter_values": {
                "degenerate_check": "single-cylinder Mie series solution (private)",
                "maze_layout": "private exact geometry; public magnitude only",
            },
        },
    },
},

# ─────────────────────────────────────────────────────── 024 Rayleigh-Benard
"hard_plus_rayleigh_benard_024": {
    "revision": "rewritten",
    "public": {
        "problem": (
            "A fluid dynamics group models steady (or statistically steady) "
            "Rayleigh-Benard convection in a two-dimensional cell heated from below and "
            "cooled from above, under the Boussinesq approximation. Design a "
            "physics-informed modeling workflow coupling velocity, pressure, and "
            "temperature. Required content: (i) the full residual system you train on, "
            "written term by term, making explicit where the temperature acts on the "
            "momentum balance and where the velocity acts on the heat balance, (ii) "
            "boundary conditions for each field on each wall, (iii) how the pressure is "
            "made unique, and (iv) a validation plan that includes a heat-transport "
            "consistency check between the two plates, with the quantity you will "
            "compute and the tolerance you will accept."
        ),
        "tags_add": ["boussinesq_coupling", "nusselt_balance", "pressure_gauge"],
    },
    "private": {
        "task_type_decl": "forward",
        "human_review": DRAFT_HR,
        "verifiable_claims": [
            {
                "claim_id": "momentum_without_buoyancy",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["physics_constraints"],
                "scope": "plan",
                "description": "逐项列写动量残差但不含浮力项（单向耦合：T 不驱动流）",
                "pattern": r"momentum\s+(?:residual|equation|balance)",
                "support_patterns": [
                    r"buoyan", r"(?:alpha|beta)\s*\*?\s*g\s*\*?\s*t\b",
                    r"g\s*\*?\s*(?:alpha|beta)\s*\*?\s*t\b",
                    r"ra\s*\*?\s*(?:pr\s*\*?\s*)?t\b",
                    r"thermal\s+(?:forcing|driving|buoyancy)",
                    r"temperature[^.]{0,50}(?:momentum|forc\w+|driv\w+)",
                    r"rayleigh[^.]{0,40}(?:term|forcing)",
                ],
                "on_contradiction": "cap_one_way_coupling",
                "selftest": {
                    "gold": "The momentum residual includes the buoyancy term Ra*Pr*T in the vertical component, so the temperature drives the flow.",
                    "tamper": "The momentum equation balances inertia, the pressure gradient, and viscous stresses; the temperature field is handled separately by its own residual.",
                },
            },
            {
                "claim_id": "temperature_without_advection",
                "type": "claim_without_support",
                "basis": "plan_internal",
                "facets": ["physics_constraints"],
                "scope": "plan",
                "description": "逐项列写温度残差但不含速度平流项（单向耦合：流不驱动 T）",
                "pattern": r"(?:temperature|heat|energy)\s+(?:residual|equation|balance)",
                "support_patterns": [
                    r"advect", r"convect(?:ion|ive)?\s+(?:term|transport|of)",
                    r"u\s*·\s*(?:nabla|grad)\s*t\b", r"velocity[^.]{0,50}(?:advect|transport|carr\w+)",
                    r"(?:nabla|grad)\s*t\b[^.]{0,30}(?:velocity|\bu\b)",
                ],
                "on_contradiction": "cap_one_way_coupling",
                "selftest": {
                    "gold": "The temperature equation contains the advective transport u·grad(T) plus thermal diffusion.",
                    "tamper": "The heat equation is a pure diffusion residual for T with the thermal diffusivity as coefficient.",
                },
            },
        ],
        "cap_rules_mode": "replace",
        "cap_rules": [
            {"rule_id": "cap_one_way_coupling", "trigger": "claim",
             "condition": "the momentum residual omits the buoyancy coupling term, or the temperature residual omits advection by the velocity field",
             "affected_facets": ["physics_constraints"], "max_score": 2,
             "rationale": "One-way coupling breaks the physics of convection."},
            {"rule_id": "cap_no_nusselt_check", "trigger": "cue",
             "condition": "no heat-transport consistency check between the plates (Nusselt or flux balance) appears in validation",
             "affected_facets": ["validation_failure_risks"], "max_score": 3,
             "rationale": "Two-plate flux imbalance is direct evidence of broken energy conservation."},
            {"rule_id": "cap_pressure_gauge_unaddressed", "trigger": "cue",
             "condition": "pressure uniqueness is not addressed (as in task 018)",
             "affected_facets": ["physics_constraints", "training_strategy"], "max_score": 3,
             "rationale": "Same gauge degeneracy as task 018."},
        ],
        "failure_traps_add": [
            "one-way coupling (missing buoyancy or advection term)",
            "no two-plate heat-flux consistency check",
            "pressure gauge unaddressed",
        ],
        "critical_points_add": {
            "physics_constraints": [
                "momentum residual contains the buoyancy term (temperature acts on momentum)",
                "temperature residual contains velocity advection (flow acts on heat)",
            ],
            "validation_failure_risks": [
                "two-plate Nusselt/heat-flux consistency check with an explicit tolerance",
            ],
        },
        "set": {
            "canonical_pde": "Boussinesq system (nondimensional): u_t + u·grad(u) = -grad(p) + Pr*lap(u) + Ra*Pr*T*e_z; div(u)=0; T_t + u·grad(T) = lap(T)",
            "parameter_values": {"Ra": "5e3 (laminar steady rolls, private instance)", "Pr": "0.71"},
        },
    },
},

}

# ═══════════════════════════════════════════════════════════════════════
# 执行效度子集 5 题（unchanged）的规格迁移：scorer_v04/claim_verifier.py
# 硬编码 SPECS（协议 §3 冻结于 8e7d3aa）→ 数据侧 verifiable_claims（D1 收尾）。
# 010 的 \bknown 词界为迁移时修正（原模式会误中 "unknown viscosity"）。
# ═══════════════════════════════════════════════════════════════════════

TASK_TYPE_DECLS = {
    "easy_poisson_2d_source_003": "forward",
    "easy_advection_1d_periodic_005": "forward",
    "medium_advection_diffusion_008": "forward",
    "medium_heat_inverse_alpha_009": "inverse",
    "medium_burgers_inverse_viscosity_010": "inverse",
    "hard_allen_cahn_016": "forward",
    "hard_plus_euler_shock_023": "forward",
    "hard_plus_mhd_divergence_025": "forward",
    "hard_plus_multiscale_darcy_026": "forward",
}

EXEC_SUBSET_CLAIMS = {
    "easy_advection_1d_periodic_005": [{
        "claim_id": "advection_speed",
        "type": "param_value", "basis": "spec",
        "facets": ALL_FACETS,
        "description": "声称的传输速度 c 与冻结实例 c=1.0 对账（协议 §3）",
        "param": "c", "true_value": 1.0, "rtol": 0.01,
        "patterns": [
            r"(?:transport|advection)\s+speed\s+c\s*=\s*" + NUM,
            r"\bspeed\s+c\s*=\s*" + NUM,
            r"\bc\s*=\s*" + NUM,
        ],
        "on_contradiction": "cap_hallucinated_value",
        "selftest": {
            "gold": "The advection speed c = 1.0 transports the initial profile around the periodic domain.",
            "tamper": "With transport speed c = 2.0 the profile wraps twice per unit time.",
        },
    }],
    "easy_poisson_2d_source_003": [{
        "claim_id": "source_scale",
        "type": "param_value", "basis": "spec",
        "facets": ALL_FACETS,
        "description": "声称的源项系数与冻结实例 2*pi^2 对账（协议 §3）",
        "param": "source_scale", "true_value": 2.0, "rtol": 0.01,
        "patterns": [NUM + r"\s*\*\s*pi\^2\s*\*\s*sin\(pi\*x\)"],
        "on_contradiction": "cap_hallucinated_value",
        "selftest": {
            "gold": "The manufactured source is 2*pi^2*sin(pi*x)*sin(pi*y).",
            "tamper": "The manufactured source is 4*pi^2*sin(pi*x)*sin(pi*y).",
        },
    }],
    "medium_burgers_inverse_viscosity_010": [{
        "claim_id": "nu_asserted_known",
        "type": "asserted_known_unknown", "basis": "spec",
        "facets": ALL_FACETS,
        "description": "待估未知量 ν 被断言为已知/固定值（反问题任务类型证据）",
        "param": "nu",
        "patterns": [
            r"\bknown\s+viscosity\s+nu\s*=\s*" + NUM,
            r"viscosity\s+nu\s*=\s*" + NUM + r"\s+(?:is\s+)?(?:known|given|fixed)",
        ],
        "on_contradiction": "cap_wrong_task_type",
        "selftest": {
            "gold": "We estimate the unknown viscosity nu jointly with the field, initializing the trainable parameter at nu = 0.05.",
            "tamper": "The known viscosity nu = 0.01 enters the residual directly as a fixed constant.",
        },
    }],
    "hard_allen_cahn_016": [{
        "claim_id": "diffusion_coefficient",
        "type": "param_value", "basis": "spec",
        "facets": ALL_FACETS,
        "description": "声称的扩散系数 d 与冻结实例 1e-4 对账（协议 §3）",
        "param": "d", "true_value": 1e-4, "rtol": 0.01,
        "patterns": [
            r"diffusion\s+coefficient\s+d\s*=\s*" + NUM,
            r"\bd\s*=\s*" + NUM,
        ],
        "on_contradiction": "cap_hallucinated_value",
        "selftest": {
            "gold": "The interface term uses the diffusion coefficient d = 1e-4 stated in the reference instance.",
            "tamper": "We set the diffusion coefficient d = 0.01 for numerical convenience.",
        },
    }],
    "hard_plus_euler_shock_023": [{
        "claim_id": "gamma_value",
        "type": "param_value", "basis": "spec",
        "facets": ALL_FACETS,
        "description": "声称的绝热指数 γ 与冻结实例 1.4 对账（协议 §3）",
        "param": "gamma", "true_value": 1.4, "rtol": 0.01,
        "patterns": [r"gamma\s*=\s*" + NUM],
        "on_contradiction": "cap_hallucinated_value",
        "selftest": {
            "gold": "For the ideal diatomic gas we use gamma = 1.4 throughout the Riemann solve.",
            "tamper": "We adopt gamma = 1.66, the monatomic value, for the shock tube.",
        },
    }],
}

HALLUCINATED_VALUE_RULE = {
    "rule_id": "cap_hallucinated_value",
    "trigger": "claim",
    "condition": "plan asserts a specific numeric value contradicting the private instantiated specification",
    "affected_facets": [],   # 空 = 封顶检出所在 facet（schema §3.3 约定）
    "max_score": 2,
    "rationale": "Hallucination cap, v0.3 semantics: contradicted numeric assertions cap the facet they appear in.",
}
