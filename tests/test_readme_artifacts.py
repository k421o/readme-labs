from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from readme_lab.readme_artifacts import (
    capture_readme_artifact,
    load_artifact_record,
    record_id_for_digest,
    register_reference_artifact,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_completed_generation_stays_mutable_until_explicit_capture(
    tmp_path: Path,
) -> None:
    working = tmp_path / "work" / "README.md"
    working.parent.mkdir()
    working.write_text("# First draft\n", encoding="utf-8")
    registry = tmp_path / "records"

    record_dir = capture_readme_artifact(
        working,
        registry=registry,
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        repository="local:example",
        revision="working-tree",
        recorded_path="README.md",
        role="repository_root",
        producer={
            "kind": "skill",
            "id": "example-readme-skill",
            "version": "1.0.0",
            "run_id": "generation-run-1",
        },
        memberships=[("example-generation", "generated_output")],
        captured_at=datetime(2026, 8, 30, 12, tzinfo=UTC),
    )

    captured = record_dir / "artifact.md"
    assert record_dir.name == record_id_for_digest(sha256(working))
    assert captured.read_bytes() == working.read_bytes()
    assert not (record_dir / "README.md").exists()

    working.write_text("# Revised after capture\n", encoding="utf-8")
    assert captured.read_text(encoding="utf-8") == "# First draft\n"
    record = load_artifact_record(record_dir)
    assert record["capture"] == {
        "state": "captured",
        "boundary": "completed_generation",
        "captured_at": "2026-08-30T12:00:00Z",
        "pre_capture_editability": "mutable",
    }
    assert record["provenance"][0]["kind"] == "generated"
    assert record["memberships"][0]["purpose"] == "generated_output"


def test_capture_never_injects_registry_metadata_into_subject(tmp_path: Path) -> None:
    working = tmp_path / "README.md"
    body = b"# Subject\n\nNo lab frontmatter belongs here.\n"
    working.write_bytes(body)

    record_dir = capture_readme_artifact(
        working,
        registry=tmp_path / "records",
        provenance_kind="authored",
        boundary="explicit_manual_capture",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="private",
        producer={"kind": "human", "id": "owner"},
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )

    assert (record_dir / "artifact.md").read_bytes() == body
    assert (record_dir / "record.json").is_file()


def test_reference_record_keeps_third_party_body_outside_git(tmp_path: Path) -> None:
    digest = "1" * 64
    record_dir = register_reference_artifact(
        registry=tmp_path / "records",
        content_sha256=digest,
        locator="https://example.invalid/project/README.md",
        repository="example/project",
        revision="2" * 40,
        recorded_path="README.md",
        role="repository_root",
        ownership="third_party",
        visibility="public",
        memberships=[("public-reference-v1", "reference_sample")],
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
        license_spdx="MIT",
    )

    record = load_artifact_record(record_dir)
    assert not (record_dir / "artifact.md").exists()
    assert not (record_dir / "README.md").exists()
    assert (record_dir / "artifact.ref.json").is_file()
    assert record["artifact"]["id"] == f"sha256:{digest}"
    assert record["artifact"]["storage"]["mode"] == "external_reference"
    assert record["provenance"][0]["kind"] == "retrieved"
    assert record["memberships"][0]["purpose"] == "reference_sample"


def test_artifact_package_rejects_mutated_captured_bytes(tmp_path: Path) -> None:
    working = tmp_path / "README.md"
    working.write_text("# Stable\n", encoding="utf-8")
    record_dir = capture_readme_artifact(
        working,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "workflow", "id": "generator"},
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )
    (record_dir / "artifact.md").write_text("# Mutated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        load_artifact_record(record_dir)


def test_reference_package_rejects_tampered_locator(tmp_path: Path) -> None:
    record_dir = register_reference_artifact(
        registry=tmp_path / "records",
        content_sha256="a" * 64,
        locator="https://example.invalid/README.md",
        repository="example/project",
        revision="b" * 40,
        recorded_path="README.md",
        role="repository_root",
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )
    reference_path = record_dir / "artifact.ref.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    reference["locator"] = "https://attacker.invalid/README.md"
    reference_path.write_text(json.dumps(reference), encoding="utf-8")

    with pytest.raises(ValueError, match="reference digest mismatch"):
        load_artifact_record(record_dir)


def test_completed_generation_requires_mutable_pre_capture_state(
    tmp_path: Path,
) -> None:
    working = tmp_path / "README.md"
    working.write_text("# Example\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mutable authoring phase"):
        capture_readme_artifact(
            working,
            registry=tmp_path / "records",
            provenance_kind="generated",
            boundary="completed_generation",
            pre_capture_editability="unknown",
            ownership="owned",
            visibility="local_only",
            producer={"kind": "workflow", "id": "generator"},
            captured_at=datetime(2026, 8, 30, tzinfo=UTC),
        )

    assert not (tmp_path / "records").exists() or not any(
        (tmp_path / "records").iterdir()
    )
