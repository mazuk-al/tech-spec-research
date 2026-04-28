# tech-spec-research-runner

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

`tech-spec-research-runner` is a minimal local workflow for researching several codebases before drafting a Technical Specification.

It is intended for tasks where a change spans multiple projects. The tool runs a sequence of Codex prompts that:

1. Research each project independently.
2. Compress each full project report into a compact summary.
3. Merge project summaries into cross-project analysis.
4. Draft a Technical Specification in Russian or English.
5. Review the draft for risks, gaps, assumptions, and open questions.

This repository is intentionally small and uses a lightweight Python dependency list via `requirements.txt`.

## Current Capabilities

- Python runner
- `task.yaml` as the source of truth
- Any number of `projects[]`
- Codex provider implemented through a provider abstraction
- `draft_language: ru` and `draft_language: en`
- Full research plus summary research artifacts
- Stage control and resume support
- Artifact validation
- `index.md` generation
- Basic tests and GitHub Actions CI
- Apache-2.0 license

## Principles

- Research must be read-only.
- The runner must not change researched codebases.
- Reports should reference real files, classes, methods, endpoints, routes, or contracts when they are found.
- Unconfirmed statements must be clearly marked as assumptions.
- Missing evidence should be listed explicitly instead of invented.

## Project structure

```text
.github/
  workflows/
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
tests/
requirements.txt
LICENSE
README.md
```

`artifacts/` is ignored except for `.gitkeep`, so generated research reports and draft specifications are not committed by default.

`scripts/run-current-task.sh` is also ignored. Use it as a local working copy if you need task-specific values that should not be published.

## Pipeline Flow

Current flow:

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

The runner reads `task.yaml` directly. `tasks/example-task.yaml` is a template and is not intended to run until placeholder paths are replaced.

```bash
python3 -m pip install -r requirements.txt
cp tasks/example-task.yaml tasks/current-task.yaml
# edit tasks/current-task.yaml and replace /absolute/path/to/... placeholders
python3 scripts/run_task.py tasks/current-task.yaml
```

`task.yaml` is the source of truth. The runner supports any number of projects in `projects[]`.

The `/absolute/path/to/...` values in `tasks/example-task.yaml` are placeholder paths. Replace them with real absolute paths to local projects before running the pipeline.

## Stage Control

Continue from an existing stage when earlier artifacts already exist:

```bash
python3 scripts/run_task.py tasks/current-task.yaml --skip-research
python3 scripts/run_task.py tasks/current-task.yaml --from merge
python3 scripts/run_task.py tasks/current-task.yaml --from draft
python3 scripts/run_task.py tasks/current-task.yaml --from critic
```

- `--skip-research` aliases `--from merge`.
- `--from merge` uses existing summary files and runs merge, draft, and critic.
- `--from draft` uses existing summary files and cross-project analysis, then runs draft and critic.
- `--from critic` uses existing summary files, cross-project analysis, and draft tech spec, then runs critic.

## Validation

The runner performs basic artifact validation between stages:

- Missing or empty files are fatal errors.
- Missing required Markdown sections are warnings.
- Full research should contain file-like references or `Not found`.
- Warnings do not stop the pipeline.

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
- `claude-code`: planned, not implemented yet
- `local`: planned, not implemented yet

The Python runner uses a provider abstraction internally. `CodexProvider` is the only implemented provider; `ClaudeCodeProvider` and `LocalProvider` are placeholders for future integrations.

The runner uses PyYAML to parse task files.

`token_saving.enabled` and `token_saving.use_summaries_for_later_stages` default to `true`. Non-summary mode is not implemented.

## Trust and Review

- Generated draft Technical Specifications are not a source of truth.
- All generated specs must be reviewed by engineers and product owners.
- Code references and assumptions must be verified before sharing.
- Missing evidence must not be treated as confirmed behavior.

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
python3 scripts/run_task.py tasks/current-task.yaml
```

Additional task files in `tasks/` are ignored by git by default, so local paths and task-specific details are not published. `scripts/run-current-task.sh` is also ignored for compatibility with the v1 bash workflow.

## Requirements

- Python 3
- Python dependencies from `requirements.txt`:
  - `PyYAML`
- Bash
- Codex CLI available as `codex`
- Local access to the projects listed in `task.yaml`

Codex invocation flags used by the runners:

- `codex exec`
- `--skip-git-repo-check`
- `--sandbox read-only`
- `--output-last-message`

## Development Checks

Run the basic local checks before pushing changes:

```bash
python3 -m py_compile scripts/run_task.py
python3 -m unittest
```

GitHub Actions CI runs these checks on push and pull request.

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
  index.md
```

## Index

`index.md` is created in `OUTPUT_DIR` after each successful run. It contains task metadata, projects, artifact paths, validation summary, and continue commands.

All generated files under `OUTPUT_DIR` are local working artifacts. When `OUTPUT_DIR` is under `artifacts/`, they are ignored by git.

## License

Apache-2.0.
