"""Load, fingerprint, and verify provenance-bearing source intake records."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from importlib import resources
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from readme_lab.artifacts import artifact_sha256, resolve_contained

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAMES = {
    1: "source-manifest-v1.schema.json",
    2: "source-manifest-v2.schema.json",
}


def _load_schema(schema_version: int) -> dict[str, Any]:
    try:
        schema_name = SCHEMA_NAMES[schema_version]
    except KeyError as error:
        raise ValueError(
            f"unsupported source manifest schema version: {schema_version}"
        ) from error
    schema_path = REPOSITORY_ROOT / "intake" / schema_name
    if schema_path.is_file():
        text = schema_path.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", schema_name).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError("source intake schema must be a JSON object")
    return schema


def load_intake_manifest(path: Path) -> dict[str, Any]:
    """Load and validate one intake manifest and its internal references."""

    manifest = json.loads(path.read_text(encoding="utf-8"))
    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, int):
        raise ValueError("source manifest schema_version must be an integer")
    Draft202012Validator(
        _load_schema(schema_version), format_checker=FormatChecker()
    ).validate(manifest)
    item_ids = [item["id"] for item in manifest["items"]]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("intake item ids must be unique")
    known = set(item_ids)
    for relationship in manifest.get("relationships", []):
        if relationship["from"] not in known or relationship["to"] not in known:
            raise ValueError("intake relationship refers to an unknown item")
    for item in manifest["items"]:
        reconstruction = item.get("reconstruction")
        if reconstruction is None:
            continue
        for insertion in reconstruction["insertions"]:
            if insertion["source_item_id"] not in known:
                raise ValueError("intake reconstruction refers to an unknown item")
    return manifest


def _git(repository: Path, *arguments: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return result.stdout


def _git_tree_sha256(repository: Path, revision: str, source_path: str) -> str:
    raw_entries = _git(
        repository,
        "ls-tree",
        "-r",
        "-z",
        revision,
        "--",
        source_path,
        binary=True,
    )
    assert isinstance(raw_entries, bytes)
    entries = [entry for entry in raw_entries.split(b"\0") if entry]
    if not entries:
        raise ValueError(f"Git tree contains no files: {revision}:{source_path}")
    digest = hashlib.sha256()
    prefix = Path(source_path)
    for entry in entries:
        metadata, raw_path = entry.split(b"\t", 1)
        object_id = metadata.split()[-1].decode()
        full_path = Path(raw_path.decode())
        relative = full_path.relative_to(prefix).as_posix().encode()
        blob = _git(repository, "cat-file", "blob", object_id, binary=True)
        assert isinstance(blob, bytes)
        digest.update(relative)
        digest.update(b"\0")
        digest.update(blob)
        digest.update(b"\0")
    return digest.hexdigest()


def fingerprint_git_path(
    repository: Path,
    *,
    revision: str,
    source_path: str,
    artifact_type: str,
) -> dict[str, str]:
    """Describe one immutable file or tree from a local Git repository."""

    repository = repository.resolve()
    resolved_revision = str(
        _git(repository, "rev-parse", f"{revision}^{{commit}}")
    ).strip()
    if resolved_revision != revision:
        raise ValueError("revision must be the full immutable commit id")
    object_id = str(_git(repository, "rev-parse", f"{revision}:{source_path}")).strip()
    object_type = str(_git(repository, "cat-file", "-t", object_id)).strip()
    expected_type = "blob" if artifact_type == "file" else "tree"
    if object_type != expected_type:
        raise ValueError(
            f"expected {artifact_type} at {revision}:{source_path}, got {object_type}"
        )
    if artifact_type == "file":
        content = _git(repository, "cat-file", "blob", object_id, binary=True)
        assert isinstance(content, bytes)
        digest = hashlib.sha256(content).hexdigest()
    elif artifact_type == "tree":
        digest = _git_tree_sha256(repository, revision, source_path)
    else:
        raise ValueError(f"unsupported artifact type: {artifact_type}")
    return {
        "state": "committed",
        "revision": revision,
        "path": source_path,
        "artifact_type": artifact_type,
        "git_oid": object_id,
        "sha256": digest,
    }


def _verify_reconstruction(
    item: dict[str, Any],
    *,
    items_by_id: dict[str, dict[str, Any]],
    repository_root: Path,
) -> bool:
    snapshot = item.get("snapshot")
    reconstruction = item["reconstruction"]
    if snapshot is None or snapshot["artifact_type"] != "tree":
        return False
    if reconstruction["artifact_type"] != "tree":
        return False
    with TemporaryDirectory(prefix="readme-labs-reconstruction-") as temporary:
        materialized = Path(temporary) / "tree"
        shutil.copytree(
            resolve_contained(repository_root, snapshot["path"]), materialized
        )
        for insertion in reconstruction["insertions"]:
            source_item = items_by_id[insertion["source_item_id"]]
            landing = source_item.get("landing")
            if landing is None or landing["sha256"] != insertion["sha256"]:
                return False
            landing_verified, source = _verify_landing_record(
                source_item, repository_root=repository_root
            )
            if not landing_verified or source is None:
                return False
            destination = resolve_contained(materialized, insertion["path"])
            if destination.exists() or destination.is_symlink():
                return False
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return (
            artifact_sha256(materialized, "tree") == reconstruction["sha256"]
            and reconstruction["sha256"] == item["source"].get("sha256")
        )


def _verify_landing_record(
    item: dict[str, Any], *, repository_root: Path
) -> tuple[bool, Path | None]:
    landing = item.get("landing")
    if landing is None:
        return False, None
    digest = landing["sha256"]
    expected_record_id = f"rm-{digest[:16]}"
    expected_path = f"readmes/records/{expected_record_id}/artifact.md"
    if (
        landing["record_id"] != expected_record_id
        or landing["path"] != expected_path
        or item["source"].get("sha256") != digest
    ):
        return False, None
    landing_path = resolve_contained(repository_root, landing["path"])
    try:
        # Local import keeps the intake schema loader independent at import time.
        from readme_lab.readme_artifacts import load_artifact_record

        record = load_artifact_record(landing_path.parent)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ValidationError,
    ):
        return False, landing_path
    storage = record["artifact"]["storage"]
    return (
        record["record_id"] == expected_record_id
        and record["artifact"]["content_sha256"] == digest
        and storage["mode"] == "embedded"
        and storage["path"] == landing_path.name == "artifact.md"
    ), landing_path


def verify_intake_manifest(
    manifest_path: Path,
    *,
    source_root: Path | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Verify checked-in snapshots and, when supplied, the original source."""

    manifest_path = manifest_path.resolve()
    manifest = load_intake_manifest(manifest_path)
    repository_root = (repository_root or REPOSITORY_ROOT).resolve()
    items_by_id = {item["id"]: item for item in manifest["items"]}
    item_results: list[dict[str, Any]] = []
    all_verified = True

    for item in manifest["items"]:
        result: dict[str, Any] = {
            "id": item["id"],
            "source_verified": None,
            "snapshot_verified": None,
            "landing_verified": None,
            "source_absent_verified": None,
            "reconstruction_verified": None,
        }
        source = item["source"]
        if source_root is not None and source["state"] == "committed":
            actual = fingerprint_git_path(
                source_root,
                revision=source["revision"],
                source_path=source["path"],
                artifact_type=source["artifact_type"],
            )
            result["source_verified"] = actual == source
        elif source_root is not None and source["state"] == "workspace":
            source_path = resolve_contained(source_root, source["path"])
            if item["intake_mode"] == "landed":
                result["source_verified"] = source["sha256"] == item["landing"][
                    "sha256"
                ]
            else:
                result["source_verified"] = (
                    artifact_sha256(source_path, source["artifact_type"])
                    == source["sha256"]
                )

        snapshot = item.get("snapshot")
        if snapshot is not None:
            snapshot_path = resolve_contained(repository_root, snapshot["path"])
            result["snapshot_verified"] = (
                artifact_sha256(snapshot_path, snapshot["artifact_type"])
                == snapshot["sha256"]
            )

        landing = item.get("landing")
        if landing is not None:
            landing_verified, _landing_path = _verify_landing_record(
                item, repository_root=repository_root
            )
            result["landing_verified"] = landing_verified
            if source_root is not None:
                original = resolve_contained(
                    source_root, landing["managed_source_path"]
                )
                result["source_absent_verified"] = (
                    landing["managed_source_absent"]
                    and landing["managed_source_path"] == source["path"]
                    and not original.exists()
                    and not original.is_symlink()
                )

        reconstruction = item.get("reconstruction")
        if reconstruction is not None:
            result["reconstruction_verified"] = _verify_reconstruction(
                item,
                items_by_id=items_by_id,
                repository_root=repository_root,
            )
        elif snapshot is not None and source.get("sha256") not in {
            None,
            snapshot["sha256"],
        }:
            result["reconstruction_verified"] = False

        checked = [
            value
            for key, value in result.items()
            if key.endswith("_verified") and value is not None
        ]
        result["verified"] = bool(checked) and all(checked)
        all_verified = all_verified and result["verified"]
        item_results.append(result)

    return {
        "manifest_id": manifest["id"],
        "source_root_supplied": source_root is not None,
        "verified": all_verified,
        "items": item_results,
    }
