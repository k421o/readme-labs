"""Prove owned Git-to-Git migrations without retaining duplicate bytes."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.git_sources import remote_records, run_git
from readme_lab.intake import fingerprint_git_path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAME = "git-migration-receipt-v1.schema.json"
SCHEMA_PATH = REPOSITORY_ROOT / "intake" / SCHEMA_NAME


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_schema() -> dict[str, Any]:
    if SCHEMA_PATH.is_file():
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", SCHEMA_NAME).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError("migration receipt schema must be an object")
    return schema


def load_git_migration_receipt(path: Path) -> dict[str, Any]:
    """Load and validate one settled migration receipt."""

    receipt = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(_load_schema(), format_checker=FormatChecker()).validate(
        receipt
    )
    return receipt


def _remote(repository: Path) -> str | None:
    records = remote_records(repository)
    if not records:
        return None
    origin = next((record for record in records if record["name"] == "origin"), None)
    return (origin or records[0])["fetch_url"]


def _is_ancestor(repository: Path, before: str, after: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", before, after],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _path_exists(repository: Path, revision: str, source_path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}:{source_path}"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def build_git_migration_receipt(
    *,
    receipt_id: str,
    source_repository: Path,
    source_repository_id: str,
    source_revision: str,
    source_path: str,
    source_deletion_revision: str,
    destination_repository: Path,
    destination_repository_id: str,
    destination_revision: str,
    destination_path: str,
    artifact_type: str,
    source_settlement: str,
    destination_settlement: str,
    references: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Build a receipt only after content landed and the source path disappeared."""

    source_repository = source_repository.resolve()
    destination_repository = destination_repository.resolve()
    source = fingerprint_git_path(
        source_repository,
        revision=source_revision,
        source_path=source_path,
        artifact_type=artifact_type,
    )
    destination = fingerprint_git_path(
        destination_repository,
        revision=destination_revision,
        source_path=destination_path,
        artifact_type=artifact_type,
    )
    resolved_deletion = run_git(
        source_repository, "rev-parse", f"{source_deletion_revision}^{{commit}}"
    )
    assert isinstance(resolved_deletion, str)
    if resolved_deletion.strip() != source_deletion_revision:
        raise ValueError("source deletion revision must be a full commit id")
    if not _is_ancestor(source_repository, source_revision, source_deletion_revision):
        raise ValueError(
            "source deletion revision does not descend from source revision"
        )
    if _path_exists(source_repository, source_deletion_revision, source_path):
        raise ValueError("source path still exists in the declared deletion revision")
    if source["sha256"] != destination["sha256"]:
        raise ValueError("source and destination content digests differ")

    receipt = {
        "schema_version": 1,
        "id": receipt_id,
        "recorded_at": _now(),
        "source": {
            "repository_id": source_repository_id,
            "remote": _remote(source_repository),
            "revision": source_revision,
            "path": source_path,
            "artifact_type": artifact_type,
            "sha256": source["sha256"],
            "deletion_revision": source_deletion_revision,
            "path_absent": True,
        },
        "destination": {
            "repository_id": destination_repository_id,
            "remote": _remote(destination_repository),
            "revision": destination_revision,
            "path": destination_path,
            "artifact_type": artifact_type,
            "sha256": destination["sha256"],
        },
        "content_equivalent": True,
        "duplicate_snapshot_retained": False,
        "settlement": {
            "source": source_settlement,
            "destination": destination_settlement,
            "references": references or [],
        },
        "limitations": limitations or [],
    }
    Draft202012Validator(_load_schema(), format_checker=FormatChecker()).validate(
        receipt
    )
    return receipt


def write_git_migration_receipt(path: Path, receipt: dict[str, Any]) -> None:
    """Write a validated receipt without copying the migrated artifact."""

    Draft202012Validator(_load_schema(), format_checker=FormatChecker()).validate(
        receipt
    )
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
