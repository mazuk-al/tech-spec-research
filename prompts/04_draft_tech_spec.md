# Draft Technical Specification Prompt

Prepare the draft Technical Specification in the requested draft language.

Do not invent unconfirmed details. If information is not supported by the research reports or cross-project analysis, explicitly mark it as an assumption. If information is missing, add it to `Open questions`.

Write all section headings and body text in the requested draft language.

## Input

- Task title: `{{task_title}}`
- Goal: `{{goal}}`
- Draft language: `{{draft_language}}`
- Cross-project analysis: `{{cross_project_analysis}}`
- Project reports: `{{project_reports}}`

## Output Format

Return a Markdown document with the following canonical structure.

Use these English section names as canonical meaning, but translate or adapt the headings to the requested draft language:

## Goal

## Context

## Current process

## Required change

## User scenarios

## Backend changes

## Frontend changes

## API / contracts

## Roles and permissions

## Validations

## Integrations

## Logging

## Information security

## Errors and edge cases

## Acceptance criteria

## Open questions

## Risks
