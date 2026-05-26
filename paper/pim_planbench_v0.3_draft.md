# PIM-PlanBench: Evaluating Planning-Stage Reasoning for Physics-Informed Modeling

## Status

Draft aligned to repository state on 2026-05-26.

Evidence source:

- Public tasks: `dataset/tasks_public_v0.3.jsonl`
- Private references: `dataset/references_private_v0.3.jsonl`
- Rubric: `docs/rubric_v0.3.md`
- Prompt: `prompts/planner_prompt.md`
- Runs: `runs/pilot_v0.3/`
- Scores: `scores/pilot_v0.3/`
- Readiness audit: `docs/benchmark_readiness_audit_v0.3.md`
- Manual calibration subset: `outputs/scoring_v0.3/manual_auto_comparison_v0.3/`

Important boundary: this draft presents PIM-PlanBench as a benchmark and evaluation resource for planning-stage scientific reasoning. It does not claim to be a complete autonomous PDE-solving agent, and it does not claim execution validation or inter-annotator agreement unless those experiments are added.

## Abstract Draft

Physics-informed modeling workflows require more than selecting a neural architecture: a practitioner must formalize the physical problem, identify governing constraints, choose a model class, design a training strategy, and anticipate validation risks. Current language-model evaluations for scientific computing often emphasize final answer generation or end-to-end tool execution, leaving this intermediate planning stage under-specified. We introduce PIM-PlanBench, a compact benchmark for evaluating planning-stage reasoning in physics-informed modeling. The benchmark contains 26 natural-language physics tasks across heat transfer, wave propagation, transport, fluid dynamics, phase-field modeling, porous media, magnetohydrodynamics, acoustics, and related domains. Each task is paired with private scoring references and a five-facet PlanScore rubric covering problem formalization, physics constraints, model choice, training strategy, and validation or failure risks. To discourage generic physics-informed neural network templates, the v0.3 rubric includes explicit cap rules for hallucinated specifications, missing constraints, and hard-trap cases such as shocks, high-frequency Helmholtz problems, multiscale Darcy flow, Cahn-Hilliard dynamics, and divergence-controlled magnetohydrodynamics. In a direct-planner pilot over six contemporary language models, all models produce schema-valid plans for all 26 tasks, but scores reveal persistent saturation and limited task-level discrimination: 297 of 780 facet scores reach the ceiling threshold, and 14 tasks show low model separation. A manual calibration subset of 180 rows indicates that automatic first-pass scores are broadly useful for screening, with mean absolute human-auto difference of 0.442, but still require human adjudication for paper-facing claims. PIM-PlanBench provides task files, private references, scoring scripts, and review workbooks for studying whether language models can reason about physics-informed modeling before code execution begins.

## 1. Introduction

Physics-informed modeling is often framed as a coding or solver-construction problem. However, before any model can be trained, a practitioner must make a sequence of planning decisions: What are the unknown fields? Which information is specified and which is missing? Which governing equations, boundary conditions, conservation constraints, or data terms must be enforced? Is a standard PINN appropriate, or does the problem require a weak form, a divergence-free parameterization, a neural operator, domain decomposition, or a hybrid numerical-neural workflow? What validation metrics would reveal physical failure rather than only pointwise prediction error?

These questions define an intermediate scientific reasoning stage between natural-language problem understanding and executable modeling. Large language models are increasingly used as assistants for scientific computing, but existing evaluations often under-measure whether a model can produce a task-specific modeling plan rather than a fluent generic recipe. In physics-informed modeling, this distinction matters because a generic answer can look plausible while omitting the exact constraints that make the problem solvable or physically meaningful.

We introduce PIM-PlanBench, a benchmark for evaluating planning-stage reasoning in physics-informed modeling. The input to each benchmark item is a natural-language physics problem. The expected output is a structured plan with five facets: Problem Formalization, Physics Constraints, Model Choice, Training Strategy, and Validation Failure Risks. The benchmark is not designed to reward final numerical accuracy directly. Instead, it evaluates whether a model can construct a scientifically valid and operational modeling plan before implementation.

The current v0.3 release contains 26 public tasks and private scoring references. Tasks span easy forward PDE examples, medium inverse or sparse-observation problems, hard stiffness and high-frequency cases, and hard-plus stress tasks designed to expose generic reasoning. The scoring protocol uses a 0-5 scale per facet, giving 25 points per task. Private references include critical points, failure traps, and cap rules that limit scores for generic PINN workflows, unsupported assumptions, missing observations, wrong task type, or validation based only on generic MSE.

Our pilot evaluation runs a direct-planner prompt over six models and scores 780 facet-level outputs. The results show that current models can produce complete structured plans, but the benchmark also reveals substantial saturation and incomplete discrimination. These findings motivate two uses of PIM-PlanBench: as a resource for measuring planning-stage scientific reasoning, and as an iterative diagnostic tool for designing harder task variants and stronger rubrics.

### Contributions

1. We define physics-informed modeling workflow planning as a distinct evaluation target between problem statement understanding and executable solver construction.
2. We release a 26-task benchmark with public model-facing tasks and private scoring references for physics-informed modeling plans.
3. We introduce PlanScore v0.3, a five-facet 0-5 rubric with explicit cap rules for generic workflows, hallucinated specifications, missing physical constraints, and hard-trap cases.
4. We provide an implemented evaluation pipeline: JSONL task files, model runners, normalization, facet-row construction, deterministic first-pass scoring, HTML reports, and human-review workbooks.
5. We report a direct-planner pilot over six models and analyze score coverage, saturation, model separation, and human-auto calibration on a 180-row subset.

## 2. Benchmark Scope

PIM-PlanBench evaluates planning-stage scientific reasoning, not final PDE solver accuracy. This boundary is deliberate. In many physics-informed modeling workflows, a plan can fail before code is written: it may misidentify the unknown field, ignore missing boundary conditions, treat an inverse problem as a forward problem, omit a data-misfit term, choose a model class incompatible with shocks or high-frequency waves, or validate only with pointwise MSE while missing conservation or divergence errors.

### 2.1 Input and Output

The model-facing input is a public natural-language task from `dataset/tasks_public_v0.3.jsonl`. The model is prompted with `prompts/planner_prompt.md` and must output a JSON object with five sections:

- Problem Formalization
- Physics Constraints
- Model Choice
- Training Strategy
- Validation Failure Risks

The private scoring file `dataset/references_private_v0.3.jsonl` is never included in model prompts. It contains task-specific references, critical points, failure traps, and cap rules used for scoring and human review.

### 2.2 Task Set

The v0.3 benchmark contains 26 tasks:

| Difficulty | Count |
| --- | ---: |
| easy | 7 |
| medium | 8 |
| hard | 5 |
| hard_plus | 6 |

The tasks cover 19 task types and 13 domains. Domains include heat transfer, wave propagation, transport, fluid dynamics, potential fields, phase-field modeling, porous media, acoustics, compressible flow, magnetohydrodynamics, thermal-fluid dynamics, chemical biology, and wave physics.

### 2.3 Hard-Trap Design

The v0.3 revision intentionally reduces method leakage in several public prompts and tightens private scoring references. The hard-trap cases require task-specific decisions:

- Euler shock tasks require weak, conservative, or shock-aware treatment rather than smooth pointwise residual fitting.
- Periodic advection-diffusion tasks require periodic compatibility beyond value matching.
- Multiscale Darcy tasks require distinguishing a single high-contrast solve from reusable operator learning.
- High-frequency Helmholtz tasks require complex-valued fields, points-per-wavelength sampling, and phase-aware validation.
- MHD tasks require divergence control for magnetic fields, not only a soft unexamined penalty.
- Cahn-Hilliard tasks require chemical-potential or mixed-form reasoning, mass conservation, and energy or long-time drift validation.

## 3. PlanScore v0.3

Each model answer is scored on five facets. Each facet receives 0-5 points, for a maximum of 25 points per task.

| Facet | What It Measures |
| --- | --- |
| Problem Formalization | Whether the model identifies unknowns, known inputs, task type, domain, missing specifications, and objective. |
| Physics Constraints | Whether the model states governing residuals, IC/BC/data terms, conservation laws, compatibility conditions, and task-specific physics. |
| Model Choice | Whether the model selects an architecture or method justified by the PDE type, data regime, constraints, and failure modes. |
| Training Strategy | Whether the model specifies losses, sampling, optimization, weighting, normalization, and stability measures. |
| Validation Failure Risks | Whether the model proposes physical validation metrics and anticipates task-specific failure modes. |

PlanScore v0.3 is designed to prevent generic high scores. A fluent generic PINN recipe is capped when it does not include task-specific residuals, constraints, validation criteria, or missing-information handling. Unsupported concrete assumptions are penalized because benchmark models should not guess private-only information. A response can still receive high credit when it labels assumptions and explains how alternative conditions would change the workflow.

## 4. Evaluation Pipeline

The current repository implements the following pipeline:

1. `scripts/run_llm_planner.py` renders the canonical prompt and writes raw plus normalized outputs under `runs/pilot_v0.3/`.
2. `scripts/build_model_output_rows_v03.py` converts normalized outputs into facet-level CSV rows.
3. `scripts/score_3modeloutput_v03.py` produces deterministic first-pass scores and summaries.
4. `scripts/visualize_model_scores.py` generates an HTML score report.
5. `scripts/build_selected_manual_scoring.mjs` and `scripts/build_random_manual_scoring_v03.mjs` build review workbooks.
6. `scripts/compare_manual_auto_scores_v03.py` compares manual and automatic scores on selected subsets.
7. `scripts/audit_benchmark_readiness.py` checks coverage, saturation, discrimination, and reference coverage.

The pipeline separates public tasks from private references. This avoids leaking scoring keys into prompts while retaining enough public information for models to reason about the physical problem.

## 5. Pilot Evaluation

### 5.1 Models

The v0.3 direct-planner pilot contains normalized outputs for six models:

- Pro/moonshotai/Kimi-K2.6
- Pro/zai-org/GLM-4.7
- Pro/zai-org/GLM-5.1
- deepseek-ai/DeepSeek-V4-Flash
- deepseek/deepseek-v4-pro
- qwen/qwen3.7-max

All six models cover all 26 public tasks and all five facets, producing 780 scored facet rows.

### 5.2 Overall Scores

The current all-existing v0.3 score summary is:

| Model | Facets | Total Points | Avg Facet | Avg Task / 25 |
| --- | ---: | ---: | ---: | ---: |
| Pro/moonshotai/Kimi-K2.6 | 130 | 576.0 | 4.431 | 22.154 |
| Pro/zai-org/GLM-5.1 | 130 | 567.0 | 4.362 | 21.808 |
| qwen/qwen3.7-max | 130 | 551.0 | 4.238 | 21.192 |
| deepseek-ai/DeepSeek-V4-Flash | 130 | 549.0 | 4.223 | 21.115 |
| deepseek/deepseek-v4-pro | 130 | 549.0 | 4.223 | 21.115 |
| Pro/zai-org/GLM-4.7 | 130 | 518.0 | 3.985 | 19.923 |

These numbers should be presented as deterministic first-pass scores unless and until full human adjudication is completed.

### 5.3 Facet Patterns

Across models, Model Choice tends to score high, while Physics Constraints and Validation Failure Risks reveal more variation. This pattern suggests that models are often able to name plausible architectures but are less consistently specific about exact physical constraints and validation criteria.

Kimi-K2.6 obtains the highest average task score in the current pilot. GLM-4.7 is lower overall but remains close enough that stronger discrimination may require harder tasks, stricter cap rules, or manual adjudication.

### 5.4 Saturation and Discrimination

The readiness audit reports:

- 297 of 780 facet scores reach the ceiling threshold of at least 4.5.
- 297 of 780 facet scores are exact 5.0 scores.
- 14 tasks have low model separation, using task score range at most 3.0.
- 28 task-facet groups have low separation, using facet range at most 0.5.

This indicates that the benchmark is usable for pilot analysis but still has saturation. The paper should not overstate model ranking precision. A stronger framing is that PIM-PlanBench provides an inspectable evaluation framework and reveals where task design must be sharpened.

## 6. Human Calibration

The repository includes two v0.3 manual comparison workbooks covering 180 rows from selected tasks. The manual-auto comparison reports:

| Metric | Value |
| --- | ---: |
| Compared rows | 180 |
| Human mean | 4.381 |
| Auto mean | 4.278 |
| Mean human minus auto | 0.103 |
| Mean absolute difference | 0.442 |
| Exact match rate | 0.378 |
| Within 0.5 rate | 0.783 |
| Within 1.0 rate | 0.972 |

These results support using deterministic scores as a screening and audit tool, not as a substitute for final human adjudication. The largest differences cluster around Problem Formalization and hard-trap cases, especially where models identify a phenomenon correctly but the automatic scorer under- or over-applies caps.

## 7. Discussion

The pilot suggests that current LLMs can produce structured physics-informed modeling plans, but high fluency does not guarantee task-specific correctness. Many answers receive strong scores because they mention plausible PINN components, optimizers, and validation ideas. However, hard-trap tasks show why explicit scoring caps are necessary: planning quality depends on whether the model handles the central mathematical difficulty, such as shocks, high-frequency phase, divergence-free fields, mass conservation, multiscale flux continuity, or missing specifications.

PIM-PlanBench therefore serves two roles. First, it evaluates model behavior at a stage that is important in real scientific modeling but often hidden in end-to-end code-generation benchmarks. Second, it provides a diagnostic design loop: score saturation, low model separation, and human-auto disagreements identify which tasks or rubrics should be refined.

## 8. Limitations

The current release is a compact pilot rather than a large-scale benchmark. It contains 26 tasks, which is enough for qualitative and diagnostic analysis but not enough for broad claims about all scientific reasoning. The current scoring pipeline includes deterministic first-pass scoring and a manual calibration subset, but full inter-annotator agreement has not yet been reported. Execution validation is also not yet implemented as a systematic experiment. Therefore, the current paper should frame numerical results as direct-planner pilot evidence and leave execution validation as future work or a planned extension unless the corresponding experiments are added.

The benchmark focuses on physics-informed modeling planning. It does not evaluate whether a generated plan can be implemented without errors, whether a trained neural solver converges, or whether a downstream agent can manage simulation tools. These are important but distinct targets.

## 9. Future Work

Future versions should add:

- Full human adjudication or inter-annotator agreement over a broader subset.
- Execution-validation subsets for tasks with analytic or numerical reference solutions.
- Additional weak-model baselines to improve ranking discrimination.
- More hard-trap variants for shock, discontinuity, conservation, geometry, and coefficient-field reasoning.
- A larger public/private split for leaderboard-style evaluation.

## Claims Ledger

| Claim | Current Evidence | Paper Status |
| --- | --- | --- |
| The benchmark has 26 tasks. | `dataset/tasks_public_v0.3.jsonl`; audit reports 26 public tasks. | Safe to claim. |
| The benchmark uses five facets and 0-5 scoring. | `docs/rubric_v0.3.md`. | Safe to claim. |
| Private references are separated from public prompts. | `dataset/references_private_v0.3.jsonl`; README; scripts. | Safe to claim. |
| Six models have complete normalized v0.3 runs. | `runs/pilot_v0.3/normalized/`; audit reports 6 models, 780 rows. | Safe to claim. |
| Kimi-K2.6 is highest in the current direct-planner pilot. | `scores/pilot_v0.3/score_summary_by_model_all_existing_v0.3.csv`. | Safe as current pilot result; do not overgeneralize. |
| Automatic first-pass scores are close enough for screening. | 180-row manual-auto comparison, mean absolute difference 0.442. | Safe with caveat. |
| The benchmark still has saturation. | Audit: 297/780 ceiling rows; 14 low-discrimination tasks. | Safe to claim. |
| Inter-annotator agreement is complete. | No current artifact. | Do not claim. |
| Execution validation is complete. | No current systematic artifact. | Do not claim. |

## Immediate Writing Tasks

1. Decide target venue and format, likely an NLP benchmark/resource track.
2. Replace related-work placeholders with verified citations.
3. Convert this Markdown into the target LaTeX template.
4. Add a figure showing the pipeline: public task -> planner prompt -> normalized plan -> private-reference scoring -> human calibration.
5. Add a table of task examples across difficulty levels.
6. Decide whether to report all six first-pass scores or only a human-adjudicated subset.
