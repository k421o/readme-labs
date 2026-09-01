"""Capture immutable README artifacts without constraining authoring workspaces."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.agent_evaluation import load_agent_review_response, load_evaluator
from readme_lab.artifacts import resolve_contained
from readme_lab.domain import validate_observation
from readme_lab.inspect import inspect_readme
from readme_lab.static_analysis import load_static_analysis_run

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "readmes"
ARTIFACT_SCHEMA = "artifact-record-v1.schema.json"
EVIDENCE_SCHEMA = "evidence-record-v1.schema.json"


@dataclass(frozen=True)
class ReadmeArtifactTransfer:
    """One reversible custody transfer into the README artifact registry."""

    source: Path
    record_dir: Path
    body_path: Path
    content_sha256: str
    transferred_at: str
    created_record: bool


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


def _replace_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _replace_artifact_record(record_dir: Path, value: dict[str, Any]) -> None:
    record_path = record_dir.resolve() / "record.json"
    original = record_path.read_bytes()
    _replace_json(record_path, value)
    try:
        load_artifact_record(record_dir)
    except Exception:
        record_path.write_bytes(original)
        raise


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

    source = Path(os.path.abspath(source))
    if source.is_symlink():
        raise ValueError("README source cannot be a symlink")
    if not source.is_file():
        raise FileNotFoundError(source)
    source = source.resolve()
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


def transfer_readme_artifact(
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
) -> ReadmeArtifactTransfer:
    """Move one completed README into its sole durable registry location.

    The source is a managed staging body, not an authoring workspace. If an
    identical content-addressed record already exists, the existing body wins
    and the redundant staging body is removed.
    """

    source = Path(os.path.abspath(source))
    if source.is_symlink():
        raise ValueError("managed README source cannot be a symlink")
    if not source.is_file():
        raise FileNotFoundError(source)
    source = source.resolve()
    content_sha256 = _file_sha256(source)
    timestamp = _timestamp(captured_at)
    record_id = record_id_for_digest(content_sha256)
    record_dir = registry.resolve() / record_id
    artifact_path = record_dir / "artifact.md"
    if record_dir.exists():
        record = load_artifact_record(record_dir)
        source_bytes = source.read_bytes()
        if (
            record["artifact"]["content_sha256"] != content_sha256
            or record["artifact"]["storage"]["mode"] != "embedded"
            or artifact_path.read_bytes() != source_bytes
        ):
            raise FileExistsError(record_dir)
        try:
            source.unlink()
            if source.exists() or _file_sha256(artifact_path) != content_sha256:
                raise RuntimeError(
                    "README transfer did not settle on the existing body"
                )
        except Exception as error:
            if not source.exists():
                source.write_bytes(source_bytes)
            if _file_sha256(source) != content_sha256:
                raise RuntimeError(
                    "README transfer failure did not restore managed source bytes"
                ) from error
            raise
        return ReadmeArtifactTransfer(
            source=source,
            record_dir=record_dir,
            body_path=artifact_path,
            content_sha256=content_sha256,
            transferred_at=timestamp,
            created_record=False,
        )

    record_dir.mkdir(parents=True)
    try:
        shutil.move(source, artifact_path)
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
        if source.exists() or _file_sha256(artifact_path) != content_sha256:
            raise RuntimeError("README transfer postconditions failed")
    except Exception:
        if artifact_path.is_file() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(artifact_path, source)
        shutil.rmtree(record_dir, ignore_errors=True)
        raise
    return ReadmeArtifactTransfer(
        source=source,
        record_dir=record_dir,
        body_path=artifact_path,
        content_sha256=content_sha256,
        transferred_at=timestamp,
        created_record=True,
    )


def rollback_readme_artifact_transfer(transfer: ReadmeArtifactTransfer) -> None:
    """Restore the managed source when a wider admission transaction fails."""

    if transfer.source.exists():
        raise FileExistsError(transfer.source)
    transfer.source.parent.mkdir(parents=True, exist_ok=True)
    if transfer.created_record:
        shutil.move(transfer.body_path, transfer.source)
        shutil.rmtree(transfer.record_dir)
    else:
        shutil.copy2(transfer.body_path, transfer.source)
    if _file_sha256(transfer.source) != transfer.content_sha256:
        raise RuntimeError("README transfer rollback did not restore source bytes")


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
        if item["kind"] == "generated" and "producer" not in item:
            raise ValueError("generated provenance requires an identified producer")
    for item in record["occurrences"]:
        _validate_identified("occ", item)
        if item["content_sha256"] != digest:
            raise ValueError("occurrence content digest does not match artifact")
    membership_ids = [
        (item["collection_id"], item["purpose"])
        for item in record["memberships"]
    ]
    if len(membership_ids) != len(set(membership_ids)):
        raise ValueError("artifact collection memberships must be unique")
    lineage_ids = [
        (
            item["relationship"],
            item.get("target_record_id"),
            item.get("target_artifact_id"),
        )
        for item in record["lineage"]
    ]
    if len(lineage_ids) != len(set(lineage_ids)):
        raise ValueError("artifact lineage relationships must be unique")
    if any(
        item.get("target_record_id") == record["record_id"]
        or item.get("target_artifact_id") == record["artifact"]["id"]
        for item in record["lineage"]
    ):
        raise ValueError("artifact lineage cannot point to itself")
    return record


def add_artifact_occurrence(
    record_dir: Path,
    *,
    repository: str,
    revision: str,
    recorded_path: str,
    role: str,
    tree: str | None = None,
    retrieval_url: str | None = None,
) -> dict[str, Any]:
    """Attach another repository placement without changing captured bytes."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    occurrence = _occurrence(
        repository=repository,
        revision=revision,
        recorded_path=recorded_path,
        role=role,
        content_sha256=record["artifact"]["content_sha256"],
        tree=tree,
        retrieval_url=retrieval_url,
    )
    if any(item["id"] == occurrence["id"] for item in record["occurrences"]):
        raise ValueError(f"occurrence already exists: {occurrence['id']}")
    record["occurrences"].append(occurrence)
    record["occurrences"].sort(key=lambda item: item["id"])
    _replace_artifact_record(record_dir, record)
    return occurrence


def add_artifact_provenance(
    record_dir: Path,
    *,
    kind: str,
    recorded_at: datetime,
    repository: str | None = None,
    revision: str | None = None,
    recorded_path: str | None = None,
    locator: str | None = None,
    producer: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Append another origin event while preserving the artifact identity."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    provenance = _provenance(
        kind=kind,
        recorded_at=_timestamp(recorded_at),
        repository=repository,
        revision=revision,
        recorded_path=recorded_path,
        locator=locator,
        producer=producer,
        limitations=limitations or [],
    )
    if any(item["id"] == provenance["id"] for item in record["provenance"]):
        raise ValueError(f"provenance already exists: {provenance['id']}")
    record["provenance"].append(provenance)
    record["provenance"].sort(key=lambda item: item["id"])
    _replace_artifact_record(record_dir, record)
    return provenance


def add_artifact_membership(
    record_dir: Path,
    *,
    collection_id: str,
    purpose: str,
    recorded_at: datetime,
) -> dict[str, Any]:
    """Add a lab use without rewriting the artifact's historical provenance."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    membership = _membership(
        (collection_id, purpose), _timestamp(recorded_at)
    )
    identity = (collection_id, purpose)
    if any(
        (item["collection_id"], item["purpose"]) == identity
        for item in record["memberships"]
    ):
        raise ValueError(f"membership already exists: {collection_id}={purpose}")
    record["memberships"].append(membership)
    record["memberships"].sort(
        key=lambda item: (item["collection_id"], item["purpose"])
    )
    _replace_artifact_record(record_dir, record)
    return membership


def add_artifact_lineage(
    record_dir: Path,
    *,
    relationship: str,
    target_record_id: str | None = None,
    target_artifact_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Link a captured revision to another immutable artifact or record."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    lineage: dict[str, Any] = {"relationship": relationship}
    if target_record_id is not None:
        lineage["target_record_id"] = target_record_id
    if target_artifact_id is not None:
        lineage["target_artifact_id"] = target_artifact_id
    if note is not None:
        lineage["note"] = note
    if lineage in record["lineage"]:
        raise ValueError("lineage relationship already exists")
    record["lineage"].append(lineage)
    record["lineage"].sort(
        key=lambda item: (
            item["relationship"],
            item.get("target_record_id", ""),
            item.get("target_artifact_id", ""),
        )
    )
    _replace_artifact_record(record_dir, record)
    return lineage


def _repository_source(
    path: Path, *, repository_root: Path, role: str, selector: str | None = None
) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    path = path.resolve()
    try:
        relative = path.relative_to(repository_root)
    except ValueError as error:
        raise ValueError(
            f"evidence source is outside repository root: {path}"
        ) from error
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(path)
    return {
        "role": role,
        "path": relative.as_posix(),
        "sha256": _file_sha256(path),
        "selector": selector,
    }


def _occurrence_by_id(record: dict[str, Any], occurrence_id: str) -> dict[str, Any]:
    matches = [
        occurrence
        for occurrence in record["occurrences"]
        if occurrence["id"] == occurrence_id
    ]
    if len(matches) != 1:
        raise ValueError(f"unknown artifact occurrence: {occurrence_id}")
    return matches[0]


def _matching_occurrence(
    record: dict[str, Any], *, repository: str, revision: str, path: str
) -> dict[str, Any]:
    matches = [
        occurrence
        for occurrence in record["occurrences"]
        if occurrence["repository"] == repository
        and occurrence["revision"] == revision
        and occurrence["path"] == path
    ]
    if len(matches) != 1:
        raise ValueError(
            "evidence must match exactly one recorded repository occurrence"
        )
    return matches[0]


def _write_evidence(record_dir: Path, value: dict[str, Any]) -> Path:
    evidence = {**value}
    evidence["evidence_id"] = f"ev-{_canonical_sha256(value)[:16]}"
    Draft202012Validator(
        _load_schema(EVIDENCE_SCHEMA), format_checker=FormatChecker()
    ).validate(evidence)
    evidence_dir = record_dir.resolve() / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    path = evidence_dir / f"{evidence['evidence_id']}.json"
    _write_new_json(path, evidence)
    return path


def _evidence_base(
    record: dict[str, Any],
    *,
    kind: str,
    subject_scope: str,
    occurrence_id: str | None,
    recorded_at: str,
    producer: dict[str, Any],
    source_records: list[dict[str, Any]],
    result: str,
    summary: str,
    payload: dict[str, Any],
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_id": record["record_id"],
        "artifact_id": record["artifact"]["id"],
        "kind": kind,
        "subject_scope": subject_scope,
        "occurrence_id": occurrence_id,
        "recorded_at": recorded_at,
        "producer": producer,
        "source_records": source_records,
        "result": result,
        "authority": "evidence_only",
        "decision_disposition": "not_decided",
        "summary": summary,
        "payload": payload,
        "limitations": limitations,
    }


def inspect_captured_artifact(
    record_dir: Path,
    *,
    occurrence_id: str,
    repository_root: Path,
    observed_at: datetime | None = None,
) -> Path:
    """Create one structural observation for an embedded captured artifact."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    storage = record["artifact"]["storage"]
    if storage["mode"] != "embedded":
        raise ValueError("structural inspection requires available README bytes")
    occurrence = _occurrence_by_id(record, occurrence_id)
    artifact_path = resolve_contained(record_dir, storage["path"])
    timestamp = observed_at or datetime.fromisoformat(
        record["capture"]["captured_at"].replace("Z", "+00:00")
    )
    observation = inspect_readme(
        artifact_path,
        repository=occurrence["repository"],
        revision=occurrence["revision"],
        role=occurrence["role"],
        role_assignment="declared",
        observed_at=timestamp,
        source_path=occurrence["path"],
        retrieval_url=occurrence.get("retrieval_url"),
        license_spdx=record["custody"].get("license_spdx"),
    )
    structure = observation["structure"]
    value = _evidence_base(
        record,
        kind="structural_observation",
        subject_scope="occurrence",
        occurrence_id=occurrence_id,
        recorded_at=observation["observed_at"],
        producer={
            "kind": "structural_inspector",
            "id": observation["derivation"]["extractor"]["name"],
            "version": observation["derivation"]["extractor"]["version"],
            "spec_sha256": observation["derivation"]["taxonomy"]["sha256"],
        },
        source_records=[
            _repository_source(
                artifact_path, repository_root=repository_root, role="artifact"
            )
        ],
        result="completed",
        summary=(
            f"{structure['line_count']} lines, {structure['word_count']} words, "
            f"{structure['heading_count']} headings, and "
            f"{structure['link_count']} links observed."
        ),
        payload=observation,
        limitations=observation["limitations"],
    )
    return _write_evidence(record_dir, value)


def _load_observation_source(
    path: Path, *, document_id: str | None, artifact_digest: str
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        candidates = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        candidates = parsed if isinstance(parsed, list) else [parsed]
    matches = [
        item
        for item in candidates
        if item.get("source", {}).get("content_sha256") == artifact_digest
        and (document_id is None or item.get("document_id") == document_id)
    ]
    if len(matches) != 1:
        raise ValueError("observation source must identify exactly one artifact record")
    validate_observation(matches[0])
    return matches[0]


def attach_observation_evidence(
    record_dir: Path,
    *,
    observations_path: Path,
    repository_root: Path,
    document_id: str | None = None,
) -> Path:
    """Project one existing READMEObservation into its document package."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    observation = _load_observation_source(
        observations_path,
        document_id=document_id,
        artifact_digest=record["artifact"]["content_sha256"],
    )
    source = observation["source"]
    occurrence = _matching_occurrence(
        record,
        repository=source["repository"],
        revision=source["revision"],
        path=source["path"],
    )
    structure = observation["structure"]
    value = _evidence_base(
        record,
        kind="structural_observation",
        subject_scope="occurrence",
        occurrence_id=occurrence["id"],
        recorded_at=observation["observed_at"],
        producer={
            "kind": "structural_inspector",
            "id": observation["derivation"]["extractor"]["name"],
            "version": observation["derivation"]["extractor"]["version"],
            "spec_sha256": observation["derivation"]["taxonomy"]["sha256"],
        },
        source_records=[
            _repository_source(
                observations_path,
                repository_root=repository_root,
                role="observation_collection",
                selector=f"document_id={observation['document_id']}",
            )
        ],
        result="completed",
        summary=(
            f"{structure['line_count']} lines, {structure['word_count']} words, "
            f"{structure['heading_count']} headings, and "
            f"{structure['link_count']} links observed."
        ),
        payload=observation,
        limitations=observation["limitations"],
    )
    return _write_evidence(record_dir, value)


def attach_static_analysis_evidence(
    record_dir: Path,
    *,
    run_path: Path,
    analyzer_path: Path,
    subject_id: str,
    repository_root: Path,
) -> Path:
    """Project one subject from a static-analysis run into a document package."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    run = load_static_analysis_run(run_path, analyzer_path=analyzer_path)
    matches = [
        subject for subject in run["subjects"] if subject["subject_id"] == subject_id
    ]
    if len(matches) != 1:
        raise ValueError(f"static run has no unique subject {subject_id!r}")
    subject = matches[0]
    if subject["source"]["content_sha256"] != record["artifact"]["content_sha256"]:
        raise ValueError("static-analysis subject does not match README artifact")
    diagnostic_count = len(subject["diagnostics"])
    value = _evidence_base(
        record,
        kind="static_analysis",
        subject_scope="artifact",
        occurrence_id=None,
        recorded_at=run["recorded_at"],
        producer={
            "kind": "static_analyzer",
            "id": run["analyzer"]["id"],
            "version": run["analyzer"]["version"],
            "spec_sha256": run["analyzer"]["spec_sha256"],
        },
        source_records=[
            _repository_source(
                run_path,
                repository_root=repository_root,
                role="static_analysis_run",
                selector=f"subject_id={subject_id}",
            ),
            _repository_source(
                analyzer_path, repository_root=repository_root, role="analyzer_spec"
            ),
        ],
        result=subject["result"],
        summary=(
            f"{diagnostic_count} diagnostics from {run['analyzer']['id']} "
            f"using the {run['configuration']['profile']} profile."
        ),
        payload={
            "run_id": run["run_id"],
            "mode": run["mode"],
            "analyzer": run["analyzer"],
            "configuration": run["configuration"],
            "subject": subject,
        },
        limitations=run["limitations"],
    )
    return _write_evidence(record_dir, value)


def _soft_run_sources(
    run_dir: Path,
    run: dict[str, Any],
    evaluator: dict[str, Any],
    *,
    repository_root: Path,
) -> list[dict[str, Any]]:
    sources = [
        _repository_source(
            run_dir / "run.json", repository_root=repository_root, role="review_run"
        ),
        _repository_source(
            evaluator["_spec_path"],
            repository_root=repository_root,
            role="evaluator_spec",
        ),
        _repository_source(
            evaluator["_instructions_path"],
            repository_root=repository_root,
            role="evaluator_instructions",
        ),
        _repository_source(
            evaluator["_response_schema_path"],
            repository_root=repository_root,
            role="evaluator_response_schema",
        ),
    ]
    run_response_schema = run_dir / "response.schema.json"
    if run_response_schema.is_file():
        sources.append(
            _repository_source(
                run_response_schema,
                repository_root=repository_root,
                role="execution_response_schema",
            )
        )
    seen = {source["path"] for source in sources}
    for role, name in sorted(run["artifacts"].items()):
        if not isinstance(name, str) or role.endswith("_sha256"):
            continue
        path = run_dir / name
        if path.resolve().relative_to(repository_root.resolve()).as_posix() in seen:
            continue
        sources.append(
            _repository_source(path, repository_root=repository_root, role=role)
        )
        seen.add(sources[-1]["path"])
    return sources


def attach_soft_review_evidence(
    record_dir: Path,
    *,
    run_dir: Path,
    evaluator_path: Path,
    occurrence_id: str,
    repository_root: Path,
) -> Path:
    """Attach a repository-contextual advisory review to one occurrence."""

    record_dir = record_dir.resolve()
    run_dir = run_dir.resolve()
    record = load_artifact_record(record_dir)
    occurrence = _occurrence_by_id(record, occurrence_id)
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    evaluator = load_evaluator(evaluator_path)
    if run.get("automated_authority") != "evidence_only" or run.get(
        "hypothesis_disposition"
    ) != "not_decided":
        raise ValueError("soft-review run exceeds evidence-only authority")
    if run["evaluator"]["id"] != evaluator["id"]:
        raise ValueError("soft-review run does not match evaluator id")
    if run["evaluator"]["spec_sha256"] != _file_sha256(
        evaluator["_spec_path"]
    ):
        raise ValueError("soft-review run does not match evaluator spec")
    if run["evaluator"]["instructions_sha256"] != _file_sha256(
        evaluator["_instructions_path"]
    ):
        raise ValueError("soft-review run does not match evaluator instructions")
    for role in ("events", "stderr", "response"):
        name = run["artifacts"].get(role)
        if not isinstance(name, str):
            continue
        if _file_sha256(run_dir / name) != run["artifacts"].get(f"{role}_sha256"):
            raise ValueError(f"soft-review {role} artifact digest mismatch")
    subject = run["subject"]
    if subject["readme_sha256"] != record["artifact"]["content_sha256"]:
        raise ValueError("soft-review subject does not match README artifact")
    if (
        occurrence["revision"] != subject["repository_head"]
        or occurrence["path"] != subject["readme_path"]
        or (
            occurrence.get("tree") is not None
            and occurrence["tree"] != subject["repository_tree"]
        )
    ):
        raise ValueError("soft-review context does not match recorded occurrence")
    response_path = run_dir / "response.json"
    response = (
        load_agent_review_response(response_path, evaluator)
        if run["result"] == "completed"
        else None
    )
    if response is not None:
        if run.get("recommendation") != response["recommendation"]:
            raise ValueError("soft-review run recommendation does not match response")
        if run.get("confidence") != response["confidence"]:
            raise ValueError("soft-review run confidence does not match response")
        summary = response["summary"]
        limitations = response["limitations"]
    else:
        summary = f"Soft review incomplete: {run.get('incomplete_reason', 'unknown')}"
        limitations = ["The evaluator did not produce a completed response."]
    value = _evidence_base(
        record,
        kind="soft_agent_review",
        subject_scope="occurrence",
        occurrence_id=occurrence_id,
        recorded_at=run["execution"]["finished_at"],
        producer={
            "kind": "soft_agent_evaluator",
            "id": evaluator["id"],
            "version": None,
            "spec_sha256": _file_sha256(evaluator["_spec_path"]),
        },
        source_records=_soft_run_sources(
            run_dir, run, evaluator, repository_root=repository_root
        ),
        result=run["result"],
        summary=summary,
        payload={
            "run_id": run["run_id"],
            "candidate_id": run["candidate_id"],
            "evaluator": run["evaluator"],
            "subject": subject,
            "executor": run["executor"],
            "execution": run["execution"],
            "recommendation": run.get("recommendation"),
            "confidence": run.get("confidence"),
            "response": response,
        },
        limitations=limitations,
    )
    return _write_evidence(record_dir, value)


def load_evidence_record(
    path: Path, *, record: dict[str, Any], repository_root: Path
) -> dict[str, Any]:
    """Validate one document evidence record and its immutable source bindings."""

    evidence = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(
        _load_schema(EVIDENCE_SCHEMA), format_checker=FormatChecker()
    ).validate(evidence)
    value = {
        key: content for key, content in evidence.items() if key != "evidence_id"
    }
    expected_id = f"ev-{_canonical_sha256(value)[:16]}"
    if evidence["evidence_id"] != expected_id or path.stem != expected_id:
        raise ValueError("evidence record identity mismatch")
    if evidence["record_id"] != record["record_id"]:
        raise ValueError("evidence record points to another artifact record")
    if evidence["artifact_id"] != record["artifact"]["id"]:
        raise ValueError("evidence record points to another README artifact")
    if evidence["subject_scope"] == "occurrence":
        _occurrence_by_id(record, evidence["occurrence_id"])
    repository_root = repository_root.resolve()
    for source in evidence["source_records"]:
        source_path = resolve_contained(repository_root, source["path"])
        if source_path.is_symlink() or not source_path.is_file():
            raise ValueError(f"evidence source is missing: {source['path']}")
        if _file_sha256(source_path) != source["sha256"]:
            raise ValueError(f"evidence source digest mismatch: {source['path']}")
    return evidence


def load_artifact_evidence(
    record_dir: Path, *, repository_root: Path
) -> list[dict[str, Any]]:
    """Load every attached evidence result in stable identity order."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    evidence_dir = record_dir / "evidence"
    if not evidence_dir.exists():
        return []
    return [
        load_evidence_record(
            path, record=record, repository_root=repository_root.resolve()
        )
        for path in sorted(evidence_dir.glob("ev-*.json"))
    ]


def verify_artifact_package(
    record_dir: Path, *, repository_root: Path
) -> dict[str, Any]:
    """Verify artifact bytes or reference plus every document-centered result."""

    record = load_artifact_record(record_dir)
    evidence = load_artifact_evidence(record_dir, repository_root=repository_root)
    return {
        "record_id": record["record_id"],
        "artifact_id": record["artifact"]["id"],
        "storage_mode": record["artifact"]["storage"]["mode"],
        "evidence_count": len(evidence),
        "evidence_kinds": sorted({item["kind"] for item in evidence}),
        "valid": True,
    }
