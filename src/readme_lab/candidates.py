"""Validate and materialize flexible experimental candidates."""

from __future__ import annotations

import json
import shutil
import subprocess
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from readme_lab.artifacts import resolve_contained, tree_sha256
from readme_lab.intake import load_intake_manifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAME = "candidate-v1.schema.json"
SCHEMA_PATH = REPOSITORY_ROOT / "candidates" / SCHEMA_NAME


def _load_schema() -> dict[str, Any]:
    if SCHEMA_PATH.is_file():
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", SCHEMA_NAME).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError("candidate schema must be a JSON object")
    return schema


def load_candidate(path: Path) -> dict[str, Any]:
    """Load one candidate descriptor without imposing a skill shape."""

    candidate = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(_load_schema()).validate(candidate)
    entrypoint_ids = [entrypoint["id"] for entrypoint in candidate["entrypoints"]]
    if len(entrypoint_ids) != len(set(entrypoint_ids)):
        raise ValueError("candidate entrypoint ids must be unique")
    return candidate


def _git_root(path: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def verify_candidate(path: Path) -> dict[str, Any]:
    """Verify candidate bytes, entrypoint containment, and source bindings."""

    path = path.resolve()
    candidate = load_candidate(path)
    repository_root = _git_root(path)
    storage = candidate["storage"]
    if storage["mode"] == "external":
        return {
            "candidate_id": candidate["id"],
            "storage_mode": "external",
            "verified": False,
            "reason": "external candidate bytes require a source-specific verifier",
        }

    artifact_root = resolve_contained(path.parent, storage["artifact_root"])
    actual_digest = tree_sha256(artifact_root)
    entrypoint_results = []
    for entrypoint in candidate["entrypoints"]:
        entrypoint_path = resolve_contained(artifact_root, entrypoint["path"])
        entrypoint_results.append(
            {
                "id": entrypoint["id"],
                "path": entrypoint["path"],
                "exists": entrypoint_path.exists(),
            }
        )

    source_results = []
    for binding in candidate["source_bindings"]:
        manifest_path = resolve_contained(repository_root, binding["manifest"])
        manifest = load_intake_manifest(manifest_path)
        manifest_ids = {item["id"] for item in manifest["items"]}
        missing = sorted(set(binding["item_ids"]) - manifest_ids)
        source_results.append(
            {
                "manifest": binding["manifest"],
                "missing_item_ids": missing,
                "verified": not missing,
            }
        )

    verified = (
        actual_digest == storage["tree_sha256"]
        and all(item["exists"] for item in entrypoint_results)
        and all(item["verified"] for item in source_results)
    )
    return {
        "candidate_id": candidate["id"],
        "storage_mode": "embedded",
        "tree_sha256": actual_digest,
        "declared_tree_sha256": storage["tree_sha256"],
        "entrypoints": entrypoint_results,
        "source_bindings": source_results,
        "verified": verified,
    }


def materialize_candidate(path: Path, destination: Path) -> dict[str, Any]:
    """Copy an embedded candidate into a new isolated destination."""

    path = path.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    verification = verify_candidate(path)
    if not verification["verified"]:
        raise ValueError("candidate failed verification")
    candidate = load_candidate(path)
    if candidate["storage"]["mode"] != "embedded":
        raise ValueError("external candidates need a source-specific materializer")
    artifact_root = resolve_contained(
        path.parent, candidate["storage"]["artifact_root"]
    )
    shutil.copytree(artifact_root, destination)
    return {
        "candidate_id": candidate["id"],
        "destination": destination.as_posix(),
        "tree_sha256": tree_sha256(destination),
    }
