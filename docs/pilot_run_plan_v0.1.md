# PIM-PlanBench Pilot v0.1 Run Plan

## Goal

Run a 26-task pilot to test whether the benchmark can distinguish language models on physics-informed modeling workflow planning.

The pilot is not intended to prove final performance. It is intended to check whether the task wording, output schema, private references, and rubric produce interpretable model differences.

## Versioned Inputs

- `dataset/tasks_public_v0.1.jsonl`: public task inputs shown to models.
- `dataset/references_private_v0.1.jsonl`: private references and scoring facets; do not include in prompts.
- `dataset/tasks_pool_v0.1.csv`: task construction ledger for researchers; do not include in prompts.
- `docs/rubric_v0.1.md`: 0-2 scoring rubric for five planning facets.
- `prompts/planner_prompt.md`: canonical JSON planner prompt template.

## Model Input

For each task, the model should receive only:

- task `id`
- task `problem`
- task `output_schema`
- the canonical prompt instruction

Optional metadata such as `difficulty`, `domain`, `pde_system`, and `task_type` may be logged by the runner, but should not be necessary for the model prompt in the first canonical run.

Do not provide:

- private reference fields
- failure traps
- expected loss terms
- analytic or numerical reference solutions
- task-pool review notes
- source provenance notes

## Prompt Rendering

For each line in `dataset/tasks_public_v0.1.jsonl`, render `prompts/planner_prompt.md` by replacing:

- `{id}` with the task id
- `{problem}` with the public task problem
- `{output_schema}` with the JSON representation of the public task output schema

## Raw Model Response Format

The model should return exactly one JSON object:

```json
{
  "id": "easy_heat_1d_dirichlet_001",
  "answer": {
    "Problem Formalization": "...",
    "Physics Constraints": "...",
    "Model Choice": "...",
    "Training Strategy": "...",
    "Validation Failure Risks": "..."
  }
}
```

If a model cannot produce valid JSON, store the raw response in a `raw_answer` field and normalize it later.

## Normalized Run Output

The runner should write one JSONL record per task to:

```text
runs/pilot_v0.1/{model_name}__canonical_v0.1.jsonl
```

Each normalized record should have this structure:

```json
{
  "id": "easy_heat_1d_dirichlet_001",
  "model": "MODEL_NAME",
  "prompt_setting": "canonical_v0.1",
  "answer": {
    "Problem Formalization": "...",
    "Physics Constraints": "...",
    "Model Choice": "...",
    "Training Strategy": "...",
    "Validation Failure Risks": "..."
  }
}
```

## First Pilot Models

Start with 2-3 models:

- one strong closed or frontier model
- one medium open or accessible model
- one smaller or weaker model if available

Use the same canonical prompt and the same 26 public tasks for all models.

## First Manual Scoring Subset

Score these six representative tasks first:

- `easy_heat_1d_dirichlet_001`
- `medium_heat_inverse_alpha_009`
- `medium_wave_sparse_sensors_012`
- `hard_cahn_hilliard_017`
- `hard_helmholtz_high_frequency_020`
- `hard_plus_mhd_divergence_025`

These cover easy forward solving, inverse parameter estimation, missing-condition detection, high-order phase-field modeling, high-frequency wave modeling, and a hard-plus coupled physics constraint.

## Scoring Facets

Each facet is scored from 0 to 2:

- `problem_formalization`
- `physics_constraints`
- `model_choice`
- `training_strategy`
- `validation_failure_risks`

Total score per task: 0-10.

## Error Tags

Use one or more tags when scoring:

- `missing_ic_bc`
- `hallucinated_condition`
- `wrong_pde_form`
- `missing_loss_term`
- `wrong_inverse_formulation`
- `weak_model_choice`
- `weak_training_strategy`
- `weak_validation`
- `ignores_stiffness_or_multiscale`
- `ignores_identifiability`
- `ignores_high_frequency_risk`
- `schema_violation`

## Pilot Success Criteria

The benchmark is ready for broader runs if:

1. Most model outputs follow the required JSON structure and five-section schema.
2. Human scoring can be completed without frequent ambiguity.
3. Strong and weaker models show visible score differences.
4. Error tags reveal interpretable failure patterns.
5. Missing-condition tasks penalize unsupported hallucination while rewarding explicit uncertainty.

## Next Decisions After Pilot

After scoring the first six tasks:

- revise ambiguous public task wording if needed;
- revise private scoring notes if multiple answers are reasonable;
- decide whether to score all 26 tasks manually;
- decide whether to add an automatic or LLM-assisted scorer;
- select 5-8 easy/medium tasks for execution validation.