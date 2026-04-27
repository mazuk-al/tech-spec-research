# Cross-Project Merge Prompt

You are combining multiple per-project research reports into one cross-project analysis for a future Technical Specification.

Do not invent implementation details. Preserve the distinction between confirmed facts and assumptions. If reports conflict, call that out explicitly instead of choosing silently.

## Input

- Task title: `{{task_title}}`
- Goal: `{{goal}}`
- Project reports: `{{project_reports}}`

## Output Format

Return a Markdown report with exactly these sections:

## End-to-end flow

Describe the current cross-project flow from user/client entry point through backend services, gateways, integrations, storage, and responses. Cite project names and source references from the reports.

## Cross-project dependencies

List dependencies between projects: calls, events, shared contracts, shared data models, auth dependencies, deployment/runtime dependencies, and operational dependencies.

## API/contracts

Summarize known API endpoints, route contracts, request/response shapes, events, schemas, DTOs, or integration contracts. Mark missing or inferred contracts as assumptions.

## Ownership by project

Describe which project owns each part of the flow, logic, UI, API, validation, persistence, integration, or operational concern.

## Conflicts between reports

List contradictions, mismatched endpoint names, unclear ownership, incompatible assumptions, missing links, or inconsistent terminology.

## Risks

List cross-project risks, including sequencing, compatibility, migrations, partial rollout, security, privacy, observability, data consistency, and ownership risks.

## Open questions

List unanswered questions for business, product, architecture, backend, frontend, QA, security, and operations.

## Recommended technical specification structure

Recommend a structure for the final Technical Specification based on the evidence and gaps.

