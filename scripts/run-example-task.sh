#!/usr/bin/env bash
set -euo pipefail

TASK_TITLE="Example cross-project technical specification research"
GOAL="Research the current implementation across frontend, backend, and gateway projects to prepare a draft Technical Specification."
OUTPUT_DIR="artifacts/example-task"
FRONTEND_PATH="/path/to/frontend"
BACKEND_PATH="/path/to/backend"
GATEWAY_PATH="/path/to/gateway"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$OUTPUT_DIR" != /* ]]; then
  OUTPUT_DIR="$ROOT_DIR/$OUTPUT_DIR"
fi

PROJECT_RESEARCH_PROMPT="$ROOT_DIR/prompts/01_project_research.md"
CROSS_PROJECT_PROMPT="$ROOT_DIR/prompts/02_cross_project_merge.md"
DRAFT_TECH_SPEC_PROMPT="$ROOT_DIR/prompts/03_draft_tech_spec.md"
CRITIC_REVIEW_PROMPT="$ROOT_DIR/prompts/04_critic_review.md"

mkdir -p "$OUTPUT_DIR"

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex command is not available. Install or configure Codex CLI before running this script." >&2
  exit 1
fi

require_dir() {
  local label="$1"
  local path="$2"

  if [[ ! -d "$path" ]]; then
    echo "Error: $label directory does not exist: $path" >&2
    echo "Edit the project paths at the top of scripts/run-example-task.sh and run again." >&2
    exit 1
  fi
}

run_codex_read_only() {
  local workdir="$1"
  local prompt="$2"
  local output_file="$3"

  (
    cd "$workdir"
    codex exec \
      --skip-git-repo-check \
      --sandbox read-only \
      --output-last-message "$output_file" \
      "$prompt"
  )
}

run_project_research() {
  local project_name="$1"
  local project_path="$2"
  local project_focus="$3"
  local output_file="$4"
  local base_prompt
  local prompt

  base_prompt="$(<"$PROJECT_RESEARCH_PROMPT")"
  prompt="$base_prompt

## Task / Project Context

- Task title: $TASK_TITLE
- Goal: $GOAL
- Project name: $project_name
- Project path: $project_path
- Project focus: $project_focus

Use the project path above as the codebase root. Research must be read-only."

  echo "Running project research: $project_name"
  run_codex_read_only "$project_path" "$prompt" "$output_file"
}

require_dir "frontend" "$FRONTEND_PATH"
require_dir "backend" "$BACKEND_PATH"
require_dir "gateway" "$GATEWAY_PATH"

FRONTEND_REPORT="$OUTPUT_DIR/01_frontend.research.md"
BACKEND_REPORT="$OUTPUT_DIR/02_backend.research.md"
GATEWAY_REPORT="$OUTPUT_DIR/03_gateway.research.md"
CROSS_PROJECT_ANALYSIS="$OUTPUT_DIR/04_cross_project_analysis.md"
DRAFT_TECH_SPEC="$OUTPUT_DIR/05_draft_tech_spec.md"
CRITIC_REVIEW="$OUTPUT_DIR/06_critic_review.md"

run_project_research \
  "frontend" \
  "$FRONTEND_PATH" \
  "User flows, UI states, client-side validation, API calls, and routes related to the task." \
  "$FRONTEND_REPORT"

run_project_research \
  "backend" \
  "$BACKEND_PATH" \
  "Domain logic, services, data models, permissions, validations, and persistence related to the task." \
  "$BACKEND_REPORT"

run_project_research \
  "gateway" \
  "$GATEWAY_PATH" \
  "External/internal API routing, request/response contracts, authorization, and integration boundaries." \
  "$GATEWAY_REPORT"

cross_project_prompt="$(<"$CROSS_PROJECT_PROMPT")

## Task Context

- Task title: $TASK_TITLE
- Goal: $GOAL

## Project Reports

### Frontend

$(<"$FRONTEND_REPORT")

### Backend

$(<"$BACKEND_REPORT")

### Gateway

$(<"$GATEWAY_REPORT")"

echo "Running cross-project merge"
run_codex_read_only "$ROOT_DIR" "$cross_project_prompt" "$CROSS_PROJECT_ANALYSIS"

draft_prompt="$(<"$DRAFT_TECH_SPEC_PROMPT")

## Task Context

- Название задачи: $TASK_TITLE
- Цель: $GOAL

## Cross-project analysis

$(<"$CROSS_PROJECT_ANALYSIS")

## Project Reports

### Frontend

$(<"$FRONTEND_REPORT")

### Backend

$(<"$BACKEND_REPORT")

### Gateway

$(<"$GATEWAY_REPORT")"

echo "Running draft technical specification"
run_codex_read_only "$ROOT_DIR" "$draft_prompt" "$DRAFT_TECH_SPEC"

critic_prompt="$(<"$CRITIC_REVIEW_PROMPT")

## Task Context

- Task title: $TASK_TITLE
- Goal: $GOAL

## Draft Technical Specification

$(<"$DRAFT_TECH_SPEC")

## Cross-project analysis

$(<"$CROSS_PROJECT_ANALYSIS")

## Project Reports

### Frontend

$(<"$FRONTEND_REPORT")

### Backend

$(<"$BACKEND_REPORT")

### Gateway

$(<"$GATEWAY_REPORT")"

echo "Running critic review"
run_codex_read_only "$ROOT_DIR" "$critic_prompt" "$CRITIC_REVIEW"

echo
echo "Created artifacts:"
echo "- $FRONTEND_REPORT"
echo "- $BACKEND_REPORT"
echo "- $GATEWAY_REPORT"
echo "- $CROSS_PROJECT_ANALYSIS"
echo "- $DRAFT_TECH_SPEC"
echo "- $CRITIC_REVIEW"
