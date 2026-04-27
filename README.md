# tech-spec-research-runner

`tech-spec-research-runner` is a minimal local workflow for researching several codebases before drafting a Technical Specification.

It is intended for tasks where a change spans multiple projects. The tool runs a sequence of Codex prompts that:

1. Research each project independently.
2. Compress each full project report into a compact summary.
3. Merge project summaries into cross-project analysis.
4. Draft a Technical Specification in Russian or English.
5. Review the draft for risks, gaps, assumptions, and open questions.

This repository is intentionally small. It does not include dependency management or package scripts.

## Principles

- Research must be read-only.
- The runner must not change researched codebases.
- Reports should reference real files, classes, methods, endpoints, routes, or contracts when they are found.
- Unconfirmed statements must be clearly marked as assumptions.
- Missing evidence should be listed explicitly instead of invented.

## Project structure

```text
tasks/
  example-task.yaml
prompts/
  01_project_research.md
  02_project_summary.md
  03_cross_project_merge.md
  04_draft_tech_spec.md
  05_critic_review.md
artifacts/
  .gitkeep
scripts/
  run_task.py
  run-example-task.sh
README.md
```

`artifacts/` is ignored except for `.gitkeep`, so generated research reports and draft specifications are not committed by default.

`scripts/run-current-task.sh` is also ignored. Use it as a local working copy if you need task-specific values that should not be published.

## Flow

The v2.2 flow is:

1. Describe the task in a task YAML file.
2. Run read-only full research for each listed project.
3. Summarize each full project report.
4. Merge project summaries into cross-project analysis.
5. Draft a Technical Specification from cross-project analysis and project summaries.
6. Review the draft using the same summary-based context.

The runner is intended to run locally. It should not modify researched repositories: all project research must be read-only.

Every research output should reference real files, classes, methods, endpoints, routes, or contracts when they are found. Unconfirmed statements must be clearly marked as assumptions.

Later pipeline stages use project summaries instead of full research reports to reduce token usage while preserving critical facts.

## Usage

The v2.2 runner reads `task.yaml` directly:

```bash
python scripts/run_task.py tasks/example-task.yaml
```

`task.yaml` is the source of truth. The runner supports any number of projects in `projects[]`.

## Task Format

```yaml
task_title: "Example cross-project technical specification research"
goal: "Research the current implementation across projects."
output_dir: "artifacts/example-task"
draft_language: "ru"
llm_provider: "codex"

token_saving:
  enabled: true
  use_summaries_for_later_stages: true

projects:
  - name: "project-a"
    path: "/absolute/path/to/project-a"
    focus: "What to research in this project."
  - name: "project-b"
    path: "/absolute/path/to/project-b"
    focus: "What to research in this project."

constraints:
  - "Research must be read-only."
  - "Do not change source code."

expected_artifacts:
  - "Per-project research reports"
  - "Cross-project analysis"
  - "Draft Technical Specification"
  - "Critic review"
```

Supported `draft_language` values:

- `ru`: draft Technical Specification in Russian
- `en`: draft Technical Specification in English

Supported `llm_provider` values:

- `codex`: implemented
- `claude-code`: planned, not implemented in v2.2
- `local`: planned, not implemented in v2.2

The runner includes a small built-in parser for the supported task YAML shape. It is not a general-purpose YAML parser.

In v2.2, `token_saving.enabled` and `token_saving.use_summaries_for_later_stages` default to `true`. Non-summary mode is not implemented.

## Legacy Bash Runner

`scripts/run-example-task.sh` is the v1 bash MVP. It does not parse YAML automatically; the values from `tasks/example-task.yaml` are mirrored as explicit shell variables at the top of the script.

Before running, edit these variables in `scripts/run-example-task.sh`:

- `TASK_TITLE`
- `GOAL`
- `OUTPUT_DIR`
- `FRONTEND_PATH`
- `BACKEND_PATH`
- `GATEWAY_PATH`

The project paths must point to existing local directories. The bash runner calls `codex exec` in read-only mode for each researched project:

```bash
bash scripts/run-example-task.sh
```

Generated artifacts are written to `OUTPUT_DIR`. The runner saves final Codex responses with `--output-last-message` so CLI technical output is not mixed into the Markdown artifacts.

## Local Task Files

For an actual task, create a local copy of the example task and fill real values there:

```bash
cp tasks/example-task.yaml tasks/current-task.yaml
```

Then edit `tasks/current-task.yaml` and run:

```bash
python scripts/run_task.py tasks/current-task.yaml
```

Additional task files in `tasks/` are ignored by git by default, so local paths and task-specific details are not published. `scripts/run-current-task.sh` is also ignored for compatibility with the v1 bash workflow.

## Requirements

- Python 3
- Bash
- Codex CLI available as `codex`
- Local access to the projects listed in `task.yaml`

Codex invocation flags used by the runners:

- `codex exec`
- `--skip-git-repo-check`
- `--sandbox read-only`
- `--output-last-message`

## Outputs

The pipeline writes these Markdown artifacts to `OUTPUT_DIR`:

```text
OUTPUT_DIR/
  01_research/
    full/
      01_<project>.research.md
      02_<project>.research.md
    summary/
      01_<project>.summary.md
      02_<project>.summary.md
  02_cross_project_analysis.md
  03_draft_tech_spec.md
  04_critic_review.md
```

These files are local working artifacts and are ignored by git.
