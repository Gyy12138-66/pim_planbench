# Planner Prompt Template v0.1

You are given a natural-language physics modeling task. Produce a structured physics-informed modeling workflow plan.

You must return exactly one valid JSON object and nothing else. Do not wrap the JSON in Markdown fences. Do not include commentary outside the JSON.

## Task Metadata

Task ID: `{id}`

Required answer sections:

```json
{output_schema}
```

## Task

```text
{problem}
```

## Output Requirements

Return exactly this JSON structure:

```json
{
  "id": "{id}",
  "answer": {
    "Problem Formalization": "...",
    "Physics Constraints": "...",
    "Model Choice": "...",
    "Training Strategy": "...",
    "Validation Failure Risks": "..."
  }
}
```

The `answer` object must contain exactly the five required section keys shown above.

## Planning Rules

- Do not invent missing physical conditions.
- If a boundary condition, initial condition, parameter value, geometry, observation setting, or coefficient field is not specified, explicitly state what is missing and how it affects the workflow.
- When choosing a model, justify why it fits the PDE type, available data, constraints, and expected failure modes.
- Include physics-informed loss terms, sampling strategy, optimization or stabilization choices, and validation metrics.
- Do not reveal chain-of-thought. Provide concise, decision-focused explanations in each section.
