from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from readme_lab.capsule import load_capsule, materialize_capsule

CAPSULE = Path("evals/scenarios/missing-first-path/capsule.toml")


def test_capsule_contract_is_valid() -> None:
    capsule = load_capsule(CAPSULE)
    assert capsule["id"] == "missing-first-path"
    assert capsule["environment"]["fidelity_level"] == 4


def test_materialize_capsule_builds_mutated_git_repository(tmp_path: Path) -> None:
    destination = tmp_path / "scenario"
    result = materialize_capsule(CAPSULE, destination)

    assert result["network"] == "disabled"
    assert (destination / ".git").is_dir()
    assert not (destination / "scorecard.json").exists()
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "## Getting started" not in readme
    assert "## Development" in readme

    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert log == [
        "Apply missing-first-path mutation",
        "Materialize base fixture",
    ]


def test_materialize_refuses_existing_destination(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        materialize_capsule(CAPSULE, tmp_path)
