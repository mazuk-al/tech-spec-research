#!/usr/bin/env python3
"""Run a tech-spec research pipeline from a task YAML file."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_PROVIDERS = {"codex", "claude-code", "local"}
IMPLEMENTED_PROVIDERS = {"codex"}
SUPPORTED_DRAFT_LANGUAGES = {"ru", "en"}


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_task_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Task YAML file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Unable to read task YAML file '{path}': {exc}")

    try:
        loaded = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        fail(f"Task YAML is invalid in '{path}': {exc}")

    if loaded is None:
        fail(f"Task YAML file is empty: {path}")
    if not isinstance(loaded, dict):
        fail(f"Task YAML root must be an object/mapping: {path}")

    return loaded


def require_string(task: dict[str, Any], key: str) -> str:
    if key not in task:
        fail(f"task.yaml is missing required field '{key}'.")
    value = task.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"task.yaml must define non-empty string field '{key}'.")
    return value


def require_string_list(task: dict[str, Any], key: str) -> list[str]:
    if key not in task:
        fail(f"task.yaml is missing required field '{key}'.")
    value = task.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"task.yaml field '{key}' must be a list of strings.")
    return value


def optional_bool_mapping(task: dict[str, Any], key: str) -> dict[str, bool]:
    value = task.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        fail(f"task.yaml field '{key}' must be an object.")

    normalized: dict[str, bool] = {}
    for field, field_value in value.items():
        if not isinstance(field_value, bool):
            fail(f"task.yaml field '{key}.{field}' must be a boolean.")
        normalized[field] = field_value
    return normalized


def require_projects(task: dict[str, Any]) -> list[dict[str, str]]:
    if "projects" not in task:
        fail("task.yaml is missing required field 'projects'.")
    value = task.get("projects")
    if not isinstance(value, list):
        fail("task.yaml field 'projects' must be a list.")
    if not value:
        fail("task.yaml field 'projects' must not be empty.")

    projects: list[dict[str, str]] = []
    for index, project in enumerate(value, start=1):
        if not isinstance(project, dict):
            fail(f"projects[{index}] must be an object.")
        normalized: dict[str, str] = {}
        for field in ("name", "path", "focus"):
            if field not in project:
                fail(f"projects[{index}] is missing required field '{field}'.")
            field_value = project.get(field)
            if not isinstance(field_value, str) or not field_value.strip():
                fail(f"projects[{index}].{field} must be a non-empty string.")
            normalized[field] = field_value
        projects.append(normalized)

    return projects


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    task_title = require_string(task, "task_title")
    goal = require_string(task, "goal")
    output_dir = require_string(task, "output_dir")
    draft_language = require_string(task, "draft_language")
    llm_provider = require_string(task, "llm_provider")
    projects = require_projects(task)
    constraints = require_string_list(task, "constraints")
    expected_artifacts = require_string_list(task, "expected_artifacts")
    token_saving = {
        "enabled": True,
        "use_summaries_for_later_stages": True,
    }
    token_saving.update(optional_bool_mapping(task, "token_saving"))

    if draft_language not in SUPPORTED_DRAFT_LANGUAGES:
        fail(
            "Unsupported draft_language "
            f"'{draft_language}'. Supported values: ru, en."
        )

    if llm_provider not in SUPPORTED_PROVIDERS:
        fail(
            "Unsupported llm_provider "
            f"'{llm_provider}'. Supported values: codex, claude-code, local."
        )

    if llm_provider not in IMPLEMENTED_PROVIDERS:
        fail(f"Provider '{llm_provider}' is planned but not implemented in v2.2.")

    if (
        token_saving["enabled"] is not True
        or token_saving["use_summaries_for_later_stages"] is not True
    ):
        fail("Non-summary mode is not implemented in v2.2.")

    for project in projects:
        project_path = Path(project["path"]).expanduser()
        if not project_path.is_absolute():
            fail(f"Project '{project['name']}' path must be absolute: {project['path']}")
        project["path"] = str(project_path)

    return {
        "task_title": task_title,
        "goal": goal,
        "output_dir": output_dir,
        "draft_language": draft_language,
        "llm_provider": llm_provider,
        "projects": projects,
        "constraints": constraints,
        "expected_artifacts": expected_artifacts,
        "token_saving": token_saving,
    }


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    slug = slug.strip("-._")
    return slug or "project"


def unique_project_slug(name: str, used: set[str]) -> str:
    base = slugify(name)
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def read_prompt(root_dir: Path, name: str) -> str:
    path = root_dir / "prompts" / name
    if not path.is_file():
        fail(f"Prompt file does not exist: {path}")
    return path.read_text(encoding="utf-8")


def markdown_list(values: list[str]) -> str:
    if not values:
        return "- Not specified"
    return "\n".join(f"- {value}" for value in values)


def run_codex(workdir: Path, prompt: str, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--output-last-message",
        str(output_file),
        prompt,
    ]
    subprocess.run(command, cwd=workdir, check=True)


def require_file(label: str, path: Path) -> None:
    if not path.is_file():
        fail(f"{label} file does not exist: {path}")


def require_existing_file(label: str, path: Path) -> None:
    require_file(label, path)


def require_non_empty_file(label: str, path: Path) -> None:
    require_existing_file(label, path)
    if path.stat().st_size == 0:
        fail(f"{label} file is empty: {path}")


def add_warning(validation: dict[str, list[str]], message: str) -> None:
    validation["warnings"].append(message)
    print(f"Warning: {message}", file=sys.stderr)


def validate_required_sections(
    label: str,
    path: Path,
    sections: list[str],
    validation: dict[str, list[str]],
) -> None:
    content = path.read_text(encoding="utf-8")
    for section in sections:
        pattern = rf"^##\s+{re.escape(section)}\s*$"
        if re.search(pattern, content, flags=re.MULTILINE) is None:
            add_warning(validation, f"{label} is missing section '{section}': {path}")


def validate_full_research_file(path: Path, validation: dict[str, list[str]]) -> None:
    require_non_empty_file("full research", path)
    validate_required_sections(
        "full research",
        path,
        [
            "Project role in this task",
            "Relevant files/classes/methods",
            "Relevant endpoints/routes",
            "Current flow",
            "Change points",
            "Risks",
            "Open questions",
            "What to include in the technical specification",
            "Confirmed facts",
            "Assumptions",
            "Not found",
        ],
        validation,
    )
    content = path.read_text(encoding="utf-8")
    has_file_like_reference = any(
        marker in content
        for marker in (
            "/",
            ".php",
            ".js",
            ".ts",
            ".py",
            ".go",
            ".vue",
            ".xml",
            ".yaml",
            ".yml",
            ".json",
        )
    )
    if not has_file_like_reference and "Not found" not in content:
        add_warning(
            validation,
            f"full research has no file-like references and no 'Not found' text: {path}",
        )


def validate_summary_file(path: Path, validation: dict[str, list[str]]) -> None:
    require_non_empty_file("summary", path)
    validate_required_sections(
        "summary",
        path,
        [
            "Project role",
            "Confirmed facts",
            "Key files/classes/methods",
            "Key endpoints/routes/contracts",
            "Current flow",
            "Change points",
            "Risks",
            "Open questions",
            "Assumptions",
            "Not found",
        ],
        validation,
    )


def validate_pipeline_output(label: str, path: Path) -> None:
    require_non_empty_file(label, path)


def require_summary_files(
    summary_report_paths: list[tuple[str, Path]],
    validation: dict[str, list[str]],
) -> None:
    for project_name, summary_path in summary_report_paths:
        require_existing_file(f"summary report for project '{project_name}'", summary_path)
        validate_summary_file(summary_path, validation)


def normalize_stage_mode(skip_research: bool, from_stage: str | None) -> str:
    if skip_research and from_stage in {None, "research", "merge"}:
        print("--skip-research aliases --from merge.")
        return "merge"
    if skip_research and from_stage in {"draft", "critic"}:
        fail("--skip-research can only be combined with --from research or --from merge.")
    return from_stage or "research"


def require_project_dirs(projects: list[dict[str, str]]) -> None:
    for project in projects:
        project_path = Path(project["path"])
        if not project_path.is_dir():
            fail(f"Project '{project['name']}' directory does not exist: {project_path}")


def task_path_for_command(root_dir: Path, task_path: Path) -> str:
    try:
        return str(task_path.relative_to(root_dir))
    except ValueError:
        return str(task_path)


def markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_index(
    task: dict[str, Any],
    task_path: Path,
    root_dir: Path,
    output_dir: Path,
    full_report_paths: list[tuple[str, Path]],
    summary_report_paths: list[tuple[str, Path]],
    cross_project_analysis: Path,
    draft_tech_spec: Path,
    critic_review: Path,
    stage_mode: str,
    validation: dict[str, list[str]],
) -> Path:
    index_path = output_dir / "index.md"
    task_arg = task_path_for_command(root_dir, task_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Research Pipeline Index",
        "",
        "## Task",
        "",
        f"- Task title: {task['task_title']}",
        f"- Goal: {task['goal']}",
        f"- Output directory: {output_dir}",
        f"- Draft language: {task['draft_language']}",
        f"- LLM provider: {task['llm_provider']}",
        f"- Stage mode used: {stage_mode}",
        "",
        "## Token Saving",
        "",
        f"- enabled: {str(task['token_saving']['enabled']).lower()}",
        "- use_summaries_for_later_stages: "
        f"{str(task['token_saving']['use_summaries_for_later_stages']).lower()}",
        "",
        "## Projects",
        "",
        "| # | Name | Path | Focus |",
        "|---|------|------|-------|",
    ]

    for index, project in enumerate(task["projects"], start=1):
        lines.append(
            "| "
            f"{index} | "
            f"{markdown_table_cell(project['name'])} | "
            f"{markdown_table_cell(project['path'])} | "
            f"{markdown_table_cell(project['focus'])} |"
        )

    lines.extend(["", "## Artifacts", "", "### Full Research", ""])
    for _, path in full_report_paths:
        lines.append(f"- {path}")

    lines.extend(["", "### Summaries", ""])
    for _, path in summary_report_paths:
        lines.append(f"- {path}")

    lines.extend(
        [
            "",
            "### Pipeline Outputs",
            "",
            f"- Cross-project analysis: {cross_project_analysis}",
            f"- Draft tech spec: {draft_tech_spec}",
            f"- Critic review: {critic_review}",
            "",
            "## Validation Summary",
            "",
            "### Errors",
            "",
        ]
    )

    if validation["errors"]:
        lines.extend(f"- {message}" for message in validation["errors"])
    else:
        lines.append("- None")

    lines.extend(["", "### Warnings", ""])
    if validation["warnings"]:
        lines.extend(f"- {message}" for message in validation["warnings"])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Continue Commands",
            "",
            "```bash",
            f"python3 scripts/run_task.py {task_arg} --skip-research",
            f"python3 scripts/run_task.py {task_arg} --from merge",
            f"python3 scripts/run_task.py {task_arg} --from draft",
            f"python3 scripts/run_task.py {task_arg} --from critic",
            "```",
            "",
        ]
    )

    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path


def render_project_research_prompt(
    base_prompt: str,
    task: dict[str, Any],
    project: dict[str, str],
) -> str:
    return f"""{base_prompt}

## Task / Project Context

- Task title: {task["task_title"]}
- Goal: {task["goal"]}
- Project name: {project["name"]}
- Project path: {project["path"]}
- Project focus: {project["focus"]}
- Draft language: {task["draft_language"]}

## Constraints

{markdown_list(task["constraints"])}

## Expected Artifacts

{markdown_list(task["expected_artifacts"])}

Use the project path above as the codebase root. Research must be read-only.
"""


def render_project_summary_prompt(
    base_prompt: str,
    task: dict[str, Any],
    project: dict[str, str],
    full_research_report: Path,
) -> str:
    return f"""{base_prompt}

## Task / Project Context

- Task title: {task["task_title"]}
- Goal: {task["goal"]}
- Project name: {project["name"]}
- Project focus: {project["focus"]}

## Full Research Report

{full_research_report.read_text(encoding="utf-8")}
"""


def render_reports_section(report_paths: list[tuple[str, Path]]) -> str:
    sections: list[str] = []
    for project_name, report_path in report_paths:
        sections.append(
            f"""### {project_name}

{report_path.read_text(encoding="utf-8")}
"""
        )
    return "\n".join(sections)


def render_cross_project_prompt(
    base_prompt: str,
    task: dict[str, Any],
    report_paths: list[tuple[str, Path]],
) -> str:
    return f"""{base_prompt}

## Task Context

- Task title: {task["task_title"]}
- Goal: {task["goal"]}
- Draft language: {task["draft_language"]}

## Constraints

{markdown_list(task["constraints"])}

## Project Reports

{render_reports_section(report_paths)}
"""


def render_draft_prompt(
    base_prompt: str,
    task: dict[str, Any],
    cross_project_analysis: Path,
    report_paths: list[tuple[str, Path]],
) -> str:
    if task["draft_language"] == "ru":
        language_instruction = "Prepare the draft Technical Specification in Russian."
    else:
        language_instruction = "Prepare the draft Technical Specification in English."

    return f"""{base_prompt}

## Language Instruction

{language_instruction}

## Task Context

- Task title: {task["task_title"]}
- Goal: {task["goal"]}
- Draft language: {task["draft_language"]}

## Cross-project analysis

{cross_project_analysis.read_text(encoding="utf-8")}

## Project Reports

{render_reports_section(report_paths)}
"""


def render_critic_prompt(
    base_prompt: str,
    task: dict[str, Any],
    draft_tech_spec: Path,
    cross_project_analysis: Path,
    report_paths: list[tuple[str, Path]],
) -> str:
    return f"""{base_prompt}

## Task Context

- Task title: {task["task_title"]}
- Goal: {task["goal"]}
- Draft language: {task["draft_language"]}

## Draft Technical Specification

{draft_tech_spec.read_text(encoding="utf-8")}

## Cross-project analysis

{cross_project_analysis.read_text(encoding="utf-8")}

## Project Reports

{render_reports_section(report_paths)}
"""


def run_pipeline(task_path: Path, stage_mode: str) -> None:
    root_dir = Path(__file__).resolve().parent.parent
    task = validate_task(parse_task_yaml(task_path))
    validation: dict[str, list[str]] = {"warnings": [], "errors": []}

    output_dir = Path(task["output_dir"]).expanduser()
    if not output_dir.is_absolute():
        output_dir = root_dir / output_dir

    full_research_dir = output_dir / "01_research" / "full"
    summary_research_dir = output_dir / "01_research" / "summary"
    project_research_prompt = read_prompt(root_dir, "01_project_research.md")
    project_summary_prompt = read_prompt(root_dir, "02_project_summary.md")
    cross_project_prompt = read_prompt(root_dir, "03_cross_project_merge.md")
    draft_prompt = read_prompt(root_dir, "04_draft_tech_spec.md")
    critic_prompt = read_prompt(root_dir, "05_critic_review.md")

    full_report_paths: list[tuple[str, Path]] = []
    summary_report_paths: list[tuple[str, Path]] = []
    used_slugs: set[str] = set()

    for index, project in enumerate(task["projects"], start=1):
        slug = unique_project_slug(project["name"], used_slugs)
        full_report_path = full_research_dir / f"{index:02d}_{slug}.research.md"
        summary_report_path = summary_research_dir / f"{index:02d}_{slug}.summary.md"
        full_report_paths.append((project["name"], full_report_path))
        summary_report_paths.append((project["name"], summary_report_path))

    cross_project_analysis = output_dir / "02_cross_project_analysis.md"
    draft_tech_spec = output_dir / "03_draft_tech_spec.md"
    critic_review = output_dir / "04_critic_review.md"

    if stage_mode == "research":
        require_project_dirs(task["projects"])
        full_research_dir.mkdir(parents=True, exist_ok=True)
        summary_research_dir.mkdir(parents=True, exist_ok=True)

        for index, project in enumerate(task["projects"], start=1):
            full_report_path = full_report_paths[index - 1][1]
            summary_report_path = summary_report_paths[index - 1][1]

            prompt = render_project_research_prompt(project_research_prompt, task, project)
            print(f"Running project research: {project['name']}")
            run_codex(Path(project["path"]), prompt, full_report_path)
            validate_full_research_file(full_report_path, validation)

            summary_prompt = render_project_summary_prompt(
                project_summary_prompt,
                task,
                project,
                full_report_path,
            )
            print(f"Running project summary: {project['name']}")
            run_codex(Path(project["path"]), summary_prompt, summary_report_path)
            validate_summary_file(summary_report_path, validation)

    if stage_mode in {"merge", "draft", "critic"}:
        require_summary_files(summary_report_paths, validation)

    if stage_mode in {"research", "merge"}:
        print("Running cross-project merge")
        run_codex(
            root_dir,
            render_cross_project_prompt(cross_project_prompt, task, summary_report_paths),
            cross_project_analysis,
        )
        validate_pipeline_output("cross-project analysis", cross_project_analysis)

    if stage_mode in {"research", "merge", "draft"}:
        validate_pipeline_output("cross-project analysis", cross_project_analysis)
        print("Running draft technical specification")
        run_codex(
            root_dir,
            render_draft_prompt(
                draft_prompt,
                task,
                cross_project_analysis,
                summary_report_paths,
            ),
            draft_tech_spec,
        )
        validate_pipeline_output("draft technical specification", draft_tech_spec)

    if stage_mode in {"research", "merge", "draft", "critic"}:
        validate_pipeline_output("cross-project analysis", cross_project_analysis)
        validate_pipeline_output("draft technical specification", draft_tech_spec)
        print("Running critic review")
        run_codex(
            root_dir,
            render_critic_prompt(
                critic_prompt,
                task,
                draft_tech_spec,
                cross_project_analysis,
                summary_report_paths,
            ),
            critic_review,
        )
        validate_pipeline_output("critic review", critic_review)

    print()
    if validation["warnings"]:
        print("Validation warnings:")
        for message in validation["warnings"]:
            print(f"- {message}")
    else:
        print("Validation: no warnings.")

    index_path = write_index(
        task,
        task_path,
        root_dir,
        output_dir,
        full_report_paths,
        summary_report_paths,
        cross_project_analysis,
        draft_tech_spec,
        critic_review,
        stage_mode,
        validation,
    )

    print()
    print("Created artifacts:")
    for _, report_path in full_report_paths:
        print(f"- {report_path}")
    for _, report_path in summary_report_paths:
        print(f"- {report_path}")
    print(f"- {cross_project_analysis}")
    print(f"- {draft_tech_spec}")
    print(f"- {critic_review}")
    print(f"- {index_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the tech-spec research pipeline from task.yaml."
    )
    parser.add_argument("task_yaml", help="Path to task YAML file.")
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Alias for --from merge. Reuse existing project summary files.",
    )
    parser.add_argument(
        "--from",
        dest="from_stage",
        choices=("research", "merge", "draft", "critic"),
        help="Start pipeline from the selected stage.",
    )
    args = parser.parse_args()

    task_path = Path(args.task_yaml).expanduser()
    if not task_path.is_absolute():
        task_path = Path.cwd() / task_path
    if not task_path.is_file():
        fail(f"Task YAML file does not exist: {task_path}")

    stage_mode = normalize_stage_mode(args.skip_research, args.from_stage)
    run_pipeline(task_path, stage_mode)


if __name__ == "__main__":
    main()
