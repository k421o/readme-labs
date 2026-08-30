"""Load and materialize held-out README evaluation task capsules."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CAPSULE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / ("task-capsule-v1.schema.json")
)


def _load_schema() -> dict[str, Any]:
    if CAPSULE_SCHEMA_PATH.is_file():
        text = CAPSULE_SCHEMA_PATH.read_text(encoding="utf-8")
    else:
        packaged = resources.files("readme_lab").joinpath(
            "data", "task-capsule-v1.schema.json"
        )
        text = packaged.read_text(encoding="utf-8")
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError("task capsule schema must be a JSON object")
    return schema


def load_capsule(path: Path) -> dict[str, Any]:
    """Load and validate a task capsule."""

    capsule = tomllib.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(_load_schema()).validate(capsule)
    return capsule


def _git(
    destination: Path,
    *arguments: str,
    timestamp: str | None = None,
) -> str:
    environment = os.environ.copy()
    if timestamp is not None:
        environment.update(
            {
                "GIT_AUTHOR_DATE": timestamp,
                "GIT_COMMITTER_DATE": timestamp,
            }
        )
    result = subprocess.run(
        ["git", *arguments],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_capsule(capsule_path: Path, destination: Path) -> dict[str, Any]:
    """Create an isolated local Git repository for a task capsule."""

    capsule_path = capsule_path.resolve()
    destination = destination.resolve()
    capsule = load_capsule(capsule_path)
    environment = capsule["environment"]
    fixture = (capsule_path.parent / environment["fixture"]).resolve()
    git_timestamp = environment["git_timestamp"]

    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    if not fixture.is_dir():
        raise FileNotFoundError(f"fixture directory does not exist: {fixture}")

    shutil.copytree(fixture, destination)
    _git(destination, "init", "--quiet", "--initial-branch=main")
    _git(destination, "config", "user.name", "readme-labs")
    _git(destination, "config", "user.email", "eval@readme-labs.invalid")
    _git(destination, "config", "commit.gpgsign", "false")
    _git(destination, "config", "core.autocrlf", "false")
    _git(destination, "add", ".")
    _git(
        destination,
        "commit",
        "--quiet",
        "-m",
        "Materialize base fixture",
        timestamp=git_timestamp,
    )
    base_commit = _git(destination, "rev-parse", "HEAD")
    base_tree = _git(destination, "rev-parse", "HEAD^{tree}")

    mutation_name = environment.get("mutation")
    mutation_sha256 = None
    if mutation_name:
        mutation = (capsule_path.parent / mutation_name).resolve()
        mutation_sha256 = _sha256(mutation)
        subprocess.run(
            ["git", "apply", "--unidiff-zero", str(mutation)],
            cwd=destination,
            check=True,
            capture_output=True,
            text=True,
        )
        _git(destination, "add", ".")
        _git(
            destination,
            "commit",
            "--quiet",
            "-m",
            "Apply evaluation mutation",
            timestamp=git_timestamp,
        )

    final_commit = _git(destination, "rev-parse", "HEAD")
    final_tree = _git(destination, "rev-parse", "HEAD^{tree}")

    return {
        "scenario_id": capsule["id"],
        "task": capsule["task"],
        "destination": destination.as_posix(),
        "fidelity_level": environment["fidelity_level"],
        "network": environment["network"],
        "capsule_sha256": _sha256(capsule_path),
        "mutation_sha256": mutation_sha256,
        "git_timestamp": git_timestamp,
        "base_commit": base_commit,
        "base_tree": base_tree,
        "final_commit": final_commit,
        "final_tree": final_tree,
    }
