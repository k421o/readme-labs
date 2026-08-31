#!/usr/bin/env python3
"""End-to-end tests for the modular README workflow helper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("readme_components.py")


class ReadmeComponentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.target = root / "target"
        self.workspace = root / "work"
        self.target.mkdir()
        (self.target / "pyproject.toml").write_text(
            '[project]\nname = "demo-project"\nversion = "1.0.0"\n', encoding="utf-8"
        )
        self.run_cli(
            "prepare",
            "--run-id",
            "demo",
            "--target-root",
            str(self.target),
            "--profile",
            "minimal",
            "--include",
            "table-of-contents",
            "--include",
            "license",
            "--workspace-root",
            str(self.workspace),
        )
        self.run_dir = self.workspace / "demo"
        (self.run_dir / "shared-context.md").write_text(
            "# Shared project context\n\n"
            "## Verified repository facts\n\nThe test fixture is authoritative.\n\n"
            "## Cross-component decisions\n\nUse the Demo Project name.\n",
            encoding="utf-8",
        )
        fragments = {
            "project-title": "# Demo Project\n",
            "short-description": "A small project used to verify modular README assembly.\n",
            "usage-quickstart": (
                "## Usage\n\nRun the verified command:\n\n"
                "```bash\npython3 --version\n```\n"
            ),
            "license": "## License\n\nLicensed under the terms in `LICENSE`.\n",
        }
        for component_id, markdown in fragments.items():
            (self.run_dir / "components" / f"{component_id}.md").write_text(
                markdown, encoding="utf-8"
            )
            report = {
                "component_id": component_id,
                "status": "ready",
                "source_files": ["pyproject.toml"],
                "verified": ["The test fixture supplies the documented project fact."],
                "unverified": [],
                "notes": "",
            }
            (self.run_dir / "reports" / f"{component_id}.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )

    def run_cli(
        self, *arguments: str, expected: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def test_validate_and_assemble_in_catalog_order(self) -> None:
        self.run_cli("status", "--run", str(self.run_dir))
        self.run_cli("validate", "--run", str(self.run_dir))
        result = self.run_cli("assemble", "--run", str(self.run_dir))
        self.assertIn("Assembled README preview", result.stdout)

        assembled = (self.run_dir / "assembled" / "README.md").read_text(
            encoding="utf-8"
        )
        expected_order = [
            "# Demo Project",
            "A small project",
            "## Table of contents",
            "## Usage",
            "## License",
        ]
        positions = [assembled.index(value) for value in expected_order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("- [Usage](#usage)", assembled)
        self.assertIn("- [License](#license)", assembled)

    def test_validation_rejects_template_placeholder(self) -> None:
        path = self.run_dir / "components" / "usage-quickstart.md"
        path.write_text("## Usage\n\nRun `{{COMMAND}}`.\n", encoding="utf-8")
        result = self.run_cli("validate", "--run", str(self.run_dir), expected=1)
        self.assertIn("unresolved template placeholder", result.stderr)

    def test_owner_extension_folds_into_owner_packet(self) -> None:
        self.run_cli(
            "prepare",
            "--run-id",
            "alias",
            "--target-root",
            str(self.target),
            "--profile",
            "custom",
            "--include",
            "repository-alias",
            "--workspace-root",
            str(self.workspace),
        )
        alias_run = self.workspace / "alias"
        manifest = json.loads((alias_run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["worker_components"], ["project-title"])
        self.assertFalse((alias_run / "briefs" / "repository-alias.md").exists())
        title_packet = (alias_run / "briefs" / "project-title.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("02-repository-alias.md", title_packet)
        result = self.run_cli("status", "--run", str(alias_run), expected=1)
        self.assertIn("shared-context | incomplete", result.stdout)

    def test_blocked_report_cannot_be_assembled(self) -> None:
        report_path = self.run_dir / "reports" / "usage-quickstart.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["status"] = "blocked"
        report["unverified"] = ["The supported command could not be established."]
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        result = self.run_cli("assemble", "--run", str(self.run_dir), expected=1)
        self.assertIn("report status is not ready", result.stderr)
        self.assertIn("report still contains unverified claims", result.stderr)


if __name__ == "__main__":
    unittest.main()
