"""Capture immutable README artifacts without constraining authoring workspaces."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.artifacts import resolve_contained

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "readmes"
ARTIFACT_SCHEMA = "artifact-record-v1.schema.json"
EVIDENCE_SCHEMA = "evidence-record-v1.schema.json"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / name
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", name).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError(f"{name} must contain a JSON object")
    return schema


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(value: datetime | None) -> str:
    timestamp = value or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("captured_at must include a timezone")
    return timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def record_id_for_digest(content_sha256: str) -> str:
    """Return the readable package identifier for one complete content digest."""

    if len(content_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in content_sha256
    ):
        raise ValueError("content_sha256 must be 64 lowercase hexadecimal characters")
    return f"rm-{content_sha256[:16]}"


def _identified(prefix: str, value: dict[str, Any]) -> dict[str, Any]:
    identified = {**value}
    identified["id"] = f"{prefix}-{_canonical_sha256(value)[:16]}"
    return identified


def _membership(raw: tuple[str, str], recorded_at: str) -> dict[str, Any]:
    collection_id, purpose = raw
    return {
        "collection_id": collection_id,
        "purpose": purpose,
        "recorded_at": recorded_at,
    }


def _occurrence(
    *,
    repository: str,
    revision: str,
    recorded_path: str,
    role: str,
    content_sha256: str,
    tree: str | None = None,
    retrieval_url: str | None = None,
) -> dict[str, Any]:
    occurrence: dict[str, Any] = {
        "repository": repository,
        "revision": revision,
        "path": recorded_path,
        "role": role,
        "content_sha256": content_sha256,
    }
    if tree is not None:
        occurrence["tree"] = tree
    if retrieval_url is not None:
        occurrence["retrieval_url"] = retrieval_url
    return _identified("occ", occurrence)


def _provenance(
    *,
    kind: str,
    recorded_at: str,
    repository: str | None,
    revision: str | None,
    recorded_path: str | None,
    locator: str | None,
    producer: dict[str, Any] | None,
    limitations: list[str],
) -> dict[str, Any]:
    source = {
        "repository": repository,
        "revision": revision,
        "path": recorded_path,
        "locator": locator,
    }
    value: dict[str, Any] = {
        "kind": kind,
        "recorded_at": recorded_at,
        "limitations": limitations,
    }
    if any(item is not None for item in source.values()):
        value["source"] = source
    if producer is not None:
        value["producer"] = producer
    return _identified("prov", value)


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _base_record(
    *,
    content_sha256: str,
    byte_length: int | None,
    original_name: str,
    storage: dict[str, Any],
    boundary: str,
    pre_capture_editability: str,
    captured_at: str,
    ownership: str,
    visibility: str,
    body_policy: str,
    license_spdx: str | None,
    provenance_kind: str,
    repository: str | None,
    revision: str | None,
    recorded_path: str | None,
    locator: str | None,
    producer: dict[str, Any] | None,
    role: str,
    tree: str | None,
    memberships: list[tuple[str, str]],
    limitations: list[str],
) -> dict[str, Any]:
    record_id = record_id_for_digest(content_sha256)
    provenance = _provenance(
        kind=provenance_kind,
        recorded_at=captured_at,
        repository=repository,
        revision=revision,
        recorded_path=recorded_path,
        locator=locator,
        producer=producer,
        limitations=limitations,
    )
    occurrences = []
    if repository is not None and revision is not None and recorded_path is not None:
        occurrences.append(
            _occurrence(
                repository=repository,
                revision=revision,
                recorded_path=recorded_path,
                role=role,
                content_sha256=content_sha256,
                tree=tree,
                retrieval_url=(
                    locator if locator and locator.startswith("http") else None
                ),
            )
        )
    custody: dict[str, Any] = {
        "ownership": ownership,
        "visibility": visibility,
        "body_policy": body_policy,
    }
    if license_spdx is not None:
        custody["license_spdx"] = license_spdx
    return {
        "schema_version": 1,
        "record_id": record_id,
        "artifact": {
            "id": f"sha256:{content_sha256}",
            "content_sha256": content_sha256,
            "media_type": "text/markdown",
            "byte_length": byte_length,
            "original_name": original_name,
            "storage": storage,
        },
        "capture": {
            "state": "captured",
            "boundary": boundary,
            "captured_at": captured_at,
            "pre_capture_editability": pre_capture_editability,
        },
        "custody": custody,
        "provenance": [provenance],
        "occurrences": occurrences,
        "memberships": [
            _membership(item, captured_at) for item in sorted(memberships)
        ],
        "lineage": [],
        "limitations": limitations,
    }


def capture_readme_artifact(
    source: Path,
    *,
    registry: Path,
    provenance_kind: str,
    boundary: str,
    pre_capture_editability: str,
    ownership: str,
    visibility: str,
    repository: str | None = None,
    revision: str | None = None,
    recorded_path: str | None = None,
    role: str = "unspecified",
    tree: str | None = None,
    producer: dict[str, Any] | None = None,
    memberships: list[tuple[str, str]] | None = None,
    captured_at: datetime | None = None,
    license_spdx: str | None = None,
    limitations: list[str] | None = None,
) -> Path:
    """Capture selected Markdown bytes after authoring has completed."""

    source = source.resolve()
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(source)
    content_sha256 = _file_sha256(source)
    record_id = record_id_for_digest(content_sha256)
    record_dir = registry.resolve() / record_id
    if record_dir.exists():
        raise FileExistsError(record_dir)
    timestamp = _timestamp(captured_at)
    record_dir.mkdir(parents=True)
    try:
        artifact_path = record_dir / "artifact.md"
        shutil.copyfile(source, artifact_path)
        record = _base_record(
            content_sha256=content_sha256,
            byte_length=artifact_path.stat().st_size,
            original_name=source.name,
            storage={
                "mode": "embedded",
                "path": "artifact.md",
                "sha256": content_sha256,
            },
            boundary=boundary,
            pre_capture_editability=pre_capture_editability,
            captured_at=timestamp,
            ownership=ownership,
            visibility=visibility,
            body_policy="embedded",
            license_spdx=license_spdx,
            provenance_kind=provenance_kind,
            repository=repository,
            revision=revision,
            recorded_path=recorded_path,
            locator=None,
            producer=producer,
            role=role,
            tree=tree,
            memberships=memberships or [],
            limitations=limitations or [],
        )
        _write_new_json(record_dir / "record.json", record)
        load_artifact_record(record_dir)
    except Exception:
        shutil.rmtree(record_dir)
        raise
    return record_dir


def register_reference_artifact(
    *,
    registry: Path,
    content_sha256: str,
    locator: str,
    repository: str,
    revision: str,
    recorded_path: str,
    role: str,
    ownership: str = "third_party",
    visibility: str = "public",
    byte_length: int | None = None,
    original_name: str = "README.md",
    memberships: list[tuple[str, str]] | None = None,
    captured_at: datetime | None = None,
    license_spdx: str | None = None,
    limitations: list[str] | None = None,
) -> Path:
    """Register immutable source identity without retaining third-party bytes."""

    record_id = record_id_for_digest(content_sha256)
    record_dir = registry.resolve() / record_id
    if record_dir.exists():
        raise FileExistsError(record_dir)
    timestamp = _timestamp(captured_at)
    record_dir.mkdir(parents=True)
    try:
        reference = {
            "schema_version": 1,
            "artifact_id": f"sha256:{content_sha256}",
            "locator": locator,
            "repository": repository,
            "revision": revision,
            "path": recorded_path,
        }
        reference_path = record_dir / "artifact.ref.json"
        _write_new_json(reference_path, reference)
        reference_sha256 = _file_sha256(reference_path)
        record = _base_record(
            content_sha256=content_sha256,
            byte_length=byte_length,
            original_name=original_name,
            storage={
                "mode": "external_reference",
                "reference_path": "artifact.ref.json",
                "reference_sha256": reference_sha256,
                "locator": locator,
            },
            boundary="observed_source_snapshot",
            pre_capture_editability="not_applicable",
            captured_at=timestamp,
            ownership=ownership,
            visibility=visibility,
            body_policy="reference_only",
            license_spdx=license_spdx,
            provenance_kind="retrieved",
            repository=repository,
            revision=revision,
            recorded_path=recorded_path,
            locator=locator,
            producer=None,
            role=role,
            tree=None,
            memberships=memberships or [],
            limitations=limitations or [],
        )
        _write_new_json(record_dir / "record.json", record)
        load_artifact_record(record_dir)
    except Exception:
        shutil.rmtree(record_dir)
        raise
    return record_dir


def _validate_identified(prefix: str, item: dict[str, Any]) -> None:
    value = {key: content for key, content in item.items() if key != "id"}
    expected = f"{prefix}-{_canonical_sha256(value)[:16]}"
    if item["id"] != expected:
        raise ValueError(f"{prefix} identity mismatch: expected {expected}")


def load_artifact_record(record_dir: Path) -> dict[str, Any]:
    """Load and verify one artifact package and its stored or referenced bytes."""

    record_dir = record_dir.resolve()
    record_path = record_dir / "record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    Draft202012Validator(
        _load_schema(ARTIFACT_SCHEMA), format_checker=FormatChecker()
    ).validate(record)
    digest = record["artifact"]["content_sha256"]
    expected_record_id = record_id_for_digest(digest)
    if (
        record["record_id"] != expected_record_id
        or record_dir.name != expected_record_id
    ):
        raise ValueError("artifact record identity does not match its content digest")
    if record["artifact"]["id"] != f"sha256:{digest}":
        raise ValueError("artifact id does not match content_sha256")

    storage = record["artifact"]["storage"]
    if storage["mode"] == "embedded":
        artifact = resolve_contained(record_dir, storage["path"])
        if artifact.is_symlink() or not artifact.is_file():
            raise ValueError("embedded README artifact is missing or is a symlink")
        actual = _file_sha256(artifact)
        if actual != digest or storage["sha256"] != digest:
            raise ValueError("embedded README artifact digest mismatch")
        if artifact.stat().st_size != record["artifact"]["byte_length"]:
            raise ValueError("embedded README artifact byte length mismatch")
        if record["custody"]["body_policy"] != "embedded":
            raise ValueError("embedded storage requires embedded body policy")
    else:
        reference = resolve_contained(record_dir, storage["reference_path"])
        if reference.is_symlink() or not reference.is_file():
            raise ValueError("artifact reference is missing or is a symlink")
        if _file_sha256(reference) != storage["reference_sha256"]:
            raise ValueError("artifact reference digest mismatch")
        reference_value = json.loads(reference.read_text(encoding="utf-8"))
        if reference_value["artifact_id"] != record["artifact"]["id"]:
            raise ValueError("artifact reference identity mismatch")
        if reference_value["locator"] != storage["locator"]:
            raise ValueError("artifact reference locator mismatch")
        if record["custody"]["body_policy"] != "reference_only":
            raise ValueError(
                "external reference storage requires reference-only policy"
            )

    if record["capture"]["boundary"] == "completed_generation" and record[
        "capture"
    ]["pre_capture_editability"] != "mutable":
        raise ValueError("completed generation must record a mutable authoring phase")
    provenance_ids = [item["id"] for item in record["provenance"]]
    occurrence_ids = [item["id"] for item in record["occurrences"]]
    if len(provenance_ids) != len(set(provenance_ids)):
        raise ValueError("artifact provenance ids must be unique")
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise ValueError("artifact occurrence ids must be unique")
    for item in record["provenance"]:
        _validate_identified("prov", item)
    for item in record["occurrences"]:
        _validate_identified("occ", item)
        if item["content_sha256"] != digest:
            raise ValueError("occurrence content digest does not match artifact")
    return record
