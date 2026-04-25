# tech-spec-research-runner

`tech-spec-research-runner` is a minimal local workflow for researching several codebases before drafting a Technical Specification.

It is intended for tasks where a change spans multiple projects, for example frontend, backend, and gateway repositories. The tool runs a sequence of Codex prompts that:

1. Research each project independently.
2. Merge findings into cross-project analysis.
3. Draft a Technical Specification in Russian.
4. Review the draft for risks, gaps, assumptions, and open questions.

This repository is intentionally small. It does not include dependency management, package scripts, Python code, or a YAML parser.

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
  02_cross_project_merge.md
  03_draft_tech_spec.md
  04_critic_review.md
artifacts/
  .gitkeep
scripts/
  run-example-task.sh
README.md
```

`artifacts/` is ignored except for `.gitkeep`, so generated research reports and draft specifications are not committed by default.

`scripts/run-current-task.sh` is also ignored. Use it as a local working copy if you need task-specific values that should not be published.

## Flow

The expected first-version flow is:

1. Describe the task in `tasks/example-task.yaml`.
2. Run read-only research for each listed project.
3. Merge project reports into cross-project analysis.
4. Draft a Technical Specification.
5. Review the draft for risks, gaps, and open questions.

The first version is intended to run locally. It should not modify researched repositories: all project research must be read-only.

Every research output should reference real files, classes, methods, endpoints, routes, or contracts when they are found. Unconfirmed statements must be clearly marked as assumptions.

## Usage

The first runner is `scripts/run-example-task.sh`. It does not parse YAML automatically yet; the values from `tasks/example-task.yaml` are mirrored as explicit shell variables at the top of the script.

Before running, edit these variables in `scripts/run-example-task.sh`:

- `TASK_TITLE`
- `GOAL`
- `OUTPUT_DIR`
- `FRONTEND_PATH`
- `BACKEND_PATH`
- `GATEWAY_PATH`

The project paths must point to existing local directories. The runner uses `codex exec` in read-only mode for each researched project:

```bash
bash scripts/run-example-task.sh
```

Generated artifacts are written to `OUTPUT_DIR`. The runner saves final Codex responses with `--output-last-message` so CLI technical output is not mixed into the Markdown artifacts.

## Local task copy

For an actual task, create a local copy of the example runner and fill real values there:

```bash
cp scripts/run-example-task.sh scripts/run-current-task.sh
```

Then edit the variables at the top of `scripts/run-current-task.sh` and run:

```bash
bash scripts/run-current-task.sh
```

`scripts/run-current-task.sh` is ignored by git, so local paths, task names, and generated workflow experiments are not published by default.

## Requirements

- Bash
- Codex CLI available as `codex`
- Local access to the projects listed in the runner variables

The runner uses:

- `codex exec`
- `--skip-git-repo-check`
- `--sandbox read-only`
- `--output-last-message`

## Outputs

The pipeline writes these Markdown artifacts to `OUTPUT_DIR`:

1. `01_frontend.research.md`
2. `02_backend.research.md`
3. `03_gateway.research.md`
4. `04_cross_project_analysis.md`
5. `05_draft_tech_spec.md`
6. `06_critic_review.md`

These files are local working artifacts and are ignored by git.
