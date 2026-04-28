import tempfile
import unittest
from pathlib import Path

from scripts import run_task


VALID_TASK_YAML = """
task_title: "Example task"
goal: "Research several projects."
output_dir: "artifacts/example-task"
draft_language: "ru"
llm_provider: "codex"

token_saving:
  enabled: true
  use_summaries_for_later_stages: true

projects:
  - name: "frontend"
    path: "/absolute/path/to/frontend"
    focus: "Frontend behavior."

constraints:
  - "Research must be read-only."

expected_artifacts:
  - "Per-project research reports"
"""


class RunTaskTests(unittest.TestCase):
    def write_task(self, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "task.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_parse_task_yaml_valid_task(self) -> None:
        task = run_task.parse_task_yaml(self.write_task(VALID_TASK_YAML))

        self.assertEqual(task["task_title"], "Example task")
        self.assertEqual(task["llm_provider"], "codex")
        self.assertEqual(task["projects"][0]["name"], "frontend")

    def test_validate_task_fails_when_required_field_is_missing(self) -> None:
        task = run_task.parse_task_yaml(
            self.write_task(VALID_TASK_YAML.replace('goal: "Research several projects."\n', ""))
        )

        with self.assertRaises(SystemExit):
            run_task.validate_task(task)

    def test_validate_task_fails_when_projects_missing_or_empty(self) -> None:
        missing_projects = run_task.parse_task_yaml(
            self.write_task(VALID_TASK_YAML.replace(
                'projects:\n  - name: "frontend"\n    path: "/absolute/path/to/frontend"\n'
                '    focus: "Frontend behavior."\n\n',
                "",
            ))
        )
        with self.assertRaises(SystemExit):
            run_task.validate_task(missing_projects)

        empty_projects = run_task.parse_task_yaml(
            self.write_task(VALID_TASK_YAML.replace(
                'projects:\n  - name: "frontend"\n    path: "/absolute/path/to/frontend"\n'
                '    focus: "Frontend behavior."',
                "projects: []",
            ))
        )
        with self.assertRaises(SystemExit):
            run_task.validate_task(empty_projects)

    def test_validate_task_fails_when_project_required_fields_are_missing(self) -> None:
        field_lines = (
            '  - name: "frontend"\n',
            '    path: "/absolute/path/to/frontend"\n',
            '    focus: "Frontend behavior."\n',
        )
        for field_line in field_lines:
            task = run_task.parse_task_yaml(
                self.write_task(VALID_TASK_YAML.replace(field_line, ""))
            )
            with self.assertRaises(SystemExit):
                run_task.validate_task(task)

    def test_create_codex_provider(self) -> None:
        provider = run_task.create_llm_provider("codex")

        self.assertIsInstance(provider, run_task.CodexProvider)

    def test_create_unknown_provider_fails(self) -> None:
        with self.assertRaises(SystemExit):
            run_task.create_llm_provider("unknown")

    def test_placeholder_providers_exist_without_running_external_commands(self) -> None:
        claude = run_task.create_llm_provider("claude-code")
        local = run_task.create_llm_provider("local")

        self.assertIsInstance(claude, run_task.ClaudeCodeProvider)
        self.assertIsInstance(local, run_task.LocalProvider)


if __name__ == "__main__":
    unittest.main()
