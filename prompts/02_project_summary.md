# Project Research Summary Prompt

You are compressing a full project research report into a compact summary for later pipeline stages.

The goal is to reduce token usage while preserving facts needed for cross-project analysis and Technical Specification drafting.

Do not invent details. Preserve the distinction between confirmed facts and assumptions.

## Input

- Task title: `{{task_title}}`
- Goal: `{{goal}}`
- Project name: `{{project_name}}`
- Project focus: `{{project_focus}}`
- Full research report: `{{full_research_report}}`

## Output Format

Return a compact Markdown report with exactly these sections:

## Project role

## Confirmed facts

## Key files/classes/methods

## Key endpoints/routes/contracts

## Current flow

## Change points

## Risks

## Open questions

## Assumptions

## Not found

Rules:
- Keep it concise.
- Preserve concrete file paths, class names, method names, endpoints, routes, and contracts.
- Do not include long explanations.
- Do not include irrelevant details.
- If a section has no data, write `Not found`.
