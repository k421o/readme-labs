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
    assert len(result["base_commit"]) == 40
    assert len(result["base_tree"]) == 40
    assert len(result["final_commit"]) == 40
    assert len(result["final_tree"]) == 40
    assert len(result["capsule_sha256"]) == 64
    assert len(result["mutation_sha256"]) == 64


def test_materialize_capsule_has_reproducible_history(tmp_path: Path) -> None:
    first = materialize_capsule(CAPSULE, tmp_path / "first")
    second = materialize_capsule(CAPSULE, tmp_path / "second")

    assert first["base_commit"] == second["base_commit"]
    assert first["base_tree"] == second["base_tree"]
    assert first["final_commit"] == second["final_commit"]
    assert first["final_tree"] == second["final_tree"]


def test_materialize_refuses_existing_destination(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        materialize_capsule(CAPSULE, tmp_path)
