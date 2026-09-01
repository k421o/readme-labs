from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from readme_lab.readme_artifacts import (
    add_artifact_lineage,
    add_artifact_membership,
    add_artifact_occurrence,
    add_artifact_provenance,
    attach_observation_evidence,
    attach_soft_review_evidence,
    attach_static_analysis_evidence,
    capture_readme_artifact,
    inspect_captured_artifact,
    load_artifact_evidence,
    load_artifact_record,
    record_id_for_digest,
    register_reference_artifact,
    rollback_readme_artifact_transfer,
    transfer_readme_artifact,
    verify_artifact_package,
)
from readme_lab.readme_catalog import (
    build_sqlite_catalog,
    render_artifact_report,
    write_artifact_report,
)

ANALYZER = Path(
    "experiments/analyzers/markdown-structure-v1/analyzer.json"
)
STATIC_RUN = Path(
    "experiments/runs/reademe-temp-forward-test-markdown-structure-v1/run.json"
)
SOFT_RUN = Path("experiments/runs/reademe-temp-forward-test-linux-maintainer-v1")
EVALUATOR = Path(
    "experiments/evaluators/popular-linux-open-source-maintainer-v1/evaluator.json"
)
GENERATED_README = Path(
    "readmes/records/rm-f96b8e9d6c94dee9/artifact.md"
)
CORPUS_OBSERVATIONS = Path("corpus/observations/pilot-high-exposure-v1.jsonl")
COMMITTED_RECORDS = Path("readmes/records")


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


def test_transfer_moves_completed_readme_into_its_artifact_record(
    tmp_path: Path,
) -> None:
    source = tmp_path / "managed-checkout/README.md"
    source.parent.mkdir()
    body = b"# Landed README\n\nTransferred once.\n"
    source.write_bytes(body)
    captured_at = datetime(2026, 9, 1, 12, tzinfo=UTC)

    transfer = transfer_readme_artifact(
        source,
        registry=tmp_path / "records",
        provenance_kind="ingested",
        boundary="ingestion_selection",
        pre_capture_editability="not_applicable",
        ownership="owned",
        visibility="local_only",
        repository="local:source",
        revision="workspace@2026-09-01T12:00:00Z",
        recorded_path="README.md",
        role="repository_root",
        captured_at=captured_at,
    )

    assert transfer.created_record is True
    assert transfer.transferred_at == "2026-09-01T12:00:00Z"
    assert transfer.content_sha256 == hashlib.sha256(body).hexdigest()
    assert not source.exists()
    assert transfer.body_path.read_bytes() == body
    record = load_artifact_record(transfer.record_dir)
    assert record["record_id"] == record_id_for_digest(transfer.content_sha256)
    assert record["capture"]["boundary"] == "ingestion_selection"
    assert record["artifact"]["storage"]["path"] == "artifact.md"


def test_identical_transfer_can_rollback_without_removing_existing_record(
    tmp_path: Path,
) -> None:
    body = b"# One canonical body\n"
    initial_source = tmp_path / "first-checkout/README.md"
    initial_source.parent.mkdir()
    initial_source.write_bytes(body)
    first = transfer_readme_artifact(
        initial_source,
        registry=tmp_path / "records",
        provenance_kind="ingested",
        boundary="ingestion_selection",
        pre_capture_editability="not_applicable",
        ownership="owned",
        visibility="local_only",
        repository="local:first",
        revision="workspace@first",
        recorded_path="README.md",
        captured_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )
    record_bytes = (first.record_dir / "record.json").read_bytes()

    duplicate_source = tmp_path / "second-checkout/README.md"
    duplicate_source.parent.mkdir()
    duplicate_source.write_bytes(body)
    duplicate = transfer_readme_artifact(
        duplicate_source,
        registry=tmp_path / "records",
        provenance_kind="ingested",
        boundary="ingestion_selection",
        pre_capture_editability="not_applicable",
        ownership="owned",
        visibility="local_only",
        repository="local:second",
        revision="workspace@second",
        recorded_path="README.md",
        captured_at=datetime(2026, 9, 1, 13, tzinfo=UTC),
    )

    assert duplicate.created_record is False
    assert duplicate.record_dir == first.record_dir
    assert not duplicate_source.exists()
    rollback_readme_artifact_transfer(duplicate)

    assert duplicate_source.read_bytes() == body
    assert first.record_dir.is_dir()
    assert first.body_path.read_bytes() == body
    assert (first.record_dir / "record.json").read_bytes() == record_bytes
    load_artifact_record(first.record_dir)


def test_existing_record_transfer_failure_restores_managed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"# Canonical body\n"
    registry_source = tmp_path / "first/README.md"
    registry_source.parent.mkdir()
    registry_source.write_bytes(body)
    first = transfer_readme_artifact(
        registry_source,
        registry=tmp_path / "records",
        provenance_kind="ingested",
        boundary="ingestion_selection",
        pre_capture_editability="not_applicable",
        ownership="owned",
        visibility="local_only",
        repository="local:first",
        revision="workspace@first",
        recorded_path="README.md",
        captured_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )
    duplicate_source = tmp_path / "second/README.md"
    duplicate_source.parent.mkdir()
    duplicate_source.write_bytes(body)
    original_unlink = Path.unlink

    def unlink_and_corrupt(path: Path, *args: object, **kwargs: object) -> None:
        original_unlink(path, *args, **kwargs)
        if path.resolve() == duplicate_source.resolve():
            first.body_path.write_text("corrupt\n", encoding="utf-8")

    monkeypatch.setattr(Path, "unlink", unlink_and_corrupt)

    with pytest.raises(RuntimeError, match="did not settle"):
        transfer_readme_artifact(
            duplicate_source,
            registry=tmp_path / "records",
            provenance_kind="ingested",
            boundary="ingestion_selection",
            pre_capture_editability="not_applicable",
            ownership="owned",
            visibility="local_only",
            captured_at=datetime(2026, 9, 1, 13, tzinfo=UTC),
        )

    assert duplicate_source.read_bytes() == body


def test_transfer_refuses_reference_only_collision_without_removing_source(
    tmp_path: Path,
) -> None:
    body = b"# Externally referenced README\n"
    digest = hashlib.sha256(body).hexdigest()
    registry = tmp_path / "records"
    reference_record = register_reference_artifact(
        registry=registry,
        content_sha256=digest,
        locator="https://example.invalid/project/README.md",
        repository="example/project",
        revision="a" * 40,
        recorded_path="README.md",
        role="repository_root",
        captured_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )
    source = tmp_path / "managed-checkout/README.md"
    source.parent.mkdir()
    source.write_bytes(body)

    with pytest.raises(FileExistsError, match=reference_record.name):
        transfer_readme_artifact(
            source,
            registry=registry,
            provenance_kind="ingested",
            boundary="ingestion_selection",
            pre_capture_editability="not_applicable",
            ownership="owned",
            visibility="local_only",
            repository="local:source",
            revision="workspace@source",
            recorded_path="README.md",
            captured_at=datetime(2026, 9, 1, 13, tzinfo=UTC),
        )

    assert source.read_bytes() == body
    assert reference_record.is_dir()
    assert not (reference_record / "artifact.md").exists()
    assert load_artifact_record(reference_record)["artifact"]["storage"][
        "mode"
    ] == "external_reference"


def test_transfer_rejects_symlink_without_moving_its_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside target\n", encoding="utf-8")
    source = tmp_path / "managed/README.md"
    source.parent.mkdir()
    source.symlink_to(outside)

    with pytest.raises(ValueError, match="cannot be a symlink"):
        transfer_readme_artifact(
            source,
            registry=tmp_path / "records",
            provenance_kind="ingested",
            boundary="ingestion_selection",
            pre_capture_editability="not_applicable",
            ownership="owned",
            visibility="local_only",
        )

    assert source.is_symlink()
    assert outside.read_text(encoding="utf-8") == "# Outside target\n"
    assert not (tmp_path / "records").exists()


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


def test_captured_artifact_can_record_multiple_repository_occurrences(
    tmp_path: Path,
) -> None:
    working = tmp_path / "README.md"
    working.write_text("# Example\n", encoding="utf-8")
    record_dir = capture_readme_artifact(
        working,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        repository="local:generation",
        revision="working-tree",
        recorded_path="README.md",
        role="repository_root",
        producer={"kind": "workflow", "id": "generator"},
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )

    occurrence = add_artifact_occurrence(
        record_dir,
        repository="local:evaluation",
        revision="1" * 40,
        tree="2" * 40,
        recorded_path="README.md",
        role="repository_root",
    )

    record = load_artifact_record(record_dir)
    assert occurrence["id"].startswith("occ-")
    assert {item["repository"] for item in record["occurrences"]} == {
        "local:generation",
        "local:evaluation",
    }


def test_purpose_and_lineage_can_evolve_without_mutating_captured_bytes(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "records"
    first_source = tmp_path / "first.md"
    second_source = tmp_path / "second.md"
    first_source.write_text("# First\n", encoding="utf-8")
    second_source.write_text("# Second\n", encoding="utf-8")
    first = capture_readme_artifact(
        first_source,
        registry=registry,
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "workflow", "id": "generator"},
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )
    second = capture_readme_artifact(
        second_source,
        registry=registry,
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "workflow", "id": "generator"},
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    original_bytes = (second / "artifact.md").read_bytes()
    first_record = load_artifact_record(first)

    add_artifact_membership(
        second,
        collection_id="personal-readmes",
        purpose="personal_corpus",
        recorded_at=datetime(2026, 8, 31, 1, tzinfo=UTC),
    )
    add_artifact_provenance(
        second,
        kind="ingested",
        recorded_at=datetime(2026, 8, 31, 2, tzinfo=UTC),
        repository="local:archive",
        revision="working-tree",
        recorded_path="README.md",
    )
    add_artifact_lineage(
        second,
        relationship="supersedes",
        target_record_id=first_record["record_id"],
        target_artifact_id=first_record["artifact"]["id"],
    )

    record = load_artifact_record(second)
    assert (second / "artifact.md").read_bytes() == original_bytes
    assert record["memberships"][0]["purpose"] == "personal_corpus"
    assert {item["kind"] for item in record["provenance"]} == {
        "generated",
        "ingested",
    }
    assert record["lineage"] == [
        {
            "relationship": "supersedes",
            "target_record_id": first_record["record_id"],
            "target_artifact_id": first_record["artifact"]["id"],
        }
    ]

    with pytest.raises(ValueError, match="cannot point to itself"):
        add_artifact_lineage(
            second,
            relationship="variant_of",
            target_record_id=record["record_id"],
        )


def test_embedded_artifact_gets_document_centered_structural_evidence(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    working = repository_root / "working" / "README.md"
    working.parent.mkdir(parents=True)
    working.write_text("# Example\n\n## Usage\n\nRun it.\n", encoding="utf-8")
    record_dir = capture_readme_artifact(
        working,
        registry=repository_root / "readmes" / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        repository="local:example",
        revision="working-tree",
        recorded_path="README.md",
        role="repository_root",
        producer={"kind": "workflow", "id": "generator"},
        captured_at=datetime(2026, 8, 30, tzinfo=UTC),
    )
    occurrence_id = load_artifact_record(record_dir)["occurrences"][0]["id"]

    evidence_path = inspect_captured_artifact(
        record_dir,
        occurrence_id=occurrence_id,
        repository_root=repository_root,
    )

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["kind"] == "structural_observation"
    assert evidence["subject_scope"] == "occurrence"
    assert evidence["payload"]["structure"]["heading_count"] == 2
    assert verify_artifact_package(
        record_dir, repository_root=repository_root
    )["evidence_count"] == 1


def test_static_analysis_subject_is_attached_by_artifact_identity(
    tmp_path: Path,
) -> None:
    record_dir = capture_readme_artifact(
        GENERATED_README,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "candidate", "id": "reademe-temp-modular-readme-v1"},
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )

    evidence_path = attach_static_analysis_evidence(
        record_dir,
        run_path=STATIC_RUN,
        analyzer_path=ANALYZER,
        subject_id="reademe-temp-forward-test-readme",
        repository_root=Path.cwd(),
    )

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["kind"] == "static_analysis"
    assert evidence["subject_scope"] == "artifact"
    assert evidence["occurrence_id"] is None
    assert evidence["payload"]["subject"]["diagnostics"] == []
    assert evidence["authority"] == "evidence_only"


def test_soft_review_attaches_to_exact_repository_occurrence(tmp_path: Path) -> None:
    record_dir = capture_readme_artifact(
        GENERATED_README,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "candidate", "id": "reademe-temp-modular-readme-v1"},
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    run = json.loads((SOFT_RUN / "run.json").read_text(encoding="utf-8"))
    occurrence = add_artifact_occurrence(
        record_dir,
        repository="local:reademe-temp-evaluation",
        revision=run["subject"]["repository_head"],
        tree=run["subject"]["repository_tree"],
        recorded_path=run["subject"]["readme_path"],
        role="repository_root",
    )

    evidence_path = attach_soft_review_evidence(
        record_dir,
        run_dir=SOFT_RUN,
        evaluator_path=EVALUATOR,
        occurrence_id=occurrence["id"],
        repository_root=Path.cwd(),
    )

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["kind"] == "soft_agent_review"
    assert evidence["subject_scope"] == "occurrence"
    assert evidence["payload"]["recommendation"] == "request_changes"
    assert len(evidence["payload"]["response"]["concerns"]) == 2
    assert evidence["decision_disposition"] == "not_decided"


def test_public_reference_collects_observation_without_retaining_body(
    tmp_path: Path,
) -> None:
    observation = next(
        json.loads(line)
        for line in CORPUS_OBSERVATIONS.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["source"]["repository"] == "pallets/flask"
    )
    source = observation["source"]
    record_dir = register_reference_artifact(
        registry=tmp_path / "records",
        content_sha256=source["content_sha256"],
        locator=source["retrieval_url"],
        repository=source["repository"],
        revision=source["revision"],
        recorded_path=source["path"],
        role=observation["role"]["primary"],
        memberships=[("pilot-high-exposure-v1", "reference_sample")],
        captured_at=datetime.fromisoformat(
            observation["observed_at"].replace("Z", "+00:00")
        ),
        license_spdx=source["license_spdx"],
    )

    attach_observation_evidence(
        record_dir,
        observations_path=CORPUS_OBSERVATIONS,
        document_id=observation["document_id"],
        repository_root=Path.cwd(),
    )

    evidence = load_artifact_evidence(record_dir, repository_root=Path.cwd())
    assert len(evidence) == 1
    assert evidence[0]["payload"]["source"]["repository"] == "pallets/flask"
    assert not (record_dir / "artifact.md").exists()


def test_evidence_tampering_breaks_content_addressed_identity(tmp_path: Path) -> None:
    record_dir = capture_readme_artifact(
        GENERATED_README,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "candidate", "id": "reademe-temp-modular-readme-v1"},
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    evidence_path = attach_static_analysis_evidence(
        record_dir,
        run_path=STATIC_RUN,
        analyzer_path=ANALYZER,
        subject_id="reademe-temp-forward-test-readme",
        repository_root=Path.cwd(),
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["summary"] = "Invented replacement summary."
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    with pytest.raises(ValueError, match="evidence record identity mismatch"):
        load_artifact_evidence(record_dir, repository_root=Path.cwd())


def test_report_joins_static_and_contextual_review_without_scoring(
    tmp_path: Path,
) -> None:
    record_dir = capture_readme_artifact(
        GENERATED_README,
        registry=tmp_path / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "candidate", "id": "reademe-temp-modular-readme-v1"},
        memberships=[("reademe-temp-forward-test", "generated_output")],
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    run = json.loads((SOFT_RUN / "run.json").read_text(encoding="utf-8"))
    occurrence = add_artifact_occurrence(
        record_dir,
        repository="local:reademe-temp-evaluation",
        revision=run["subject"]["repository_head"],
        tree=run["subject"]["repository_tree"],
        recorded_path=run["subject"]["readme_path"],
        role="repository_root",
    )
    attach_static_analysis_evidence(
        record_dir,
        run_path=STATIC_RUN,
        analyzer_path=ANALYZER,
        subject_id="reademe-temp-forward-test-readme",
        repository_root=Path.cwd(),
    )
    attach_soft_review_evidence(
        record_dir,
        run_dir=SOFT_RUN,
        evaluator_path=EVALUATOR,
        occurrence_id=occurrence["id"],
        repository_root=Path.cwd(),
    )

    report_path = write_artifact_report(
        record_dir, repository_root=Path.cwd()
    )
    report = report_path.read_text(encoding="utf-8")

    assert "schema: readme-artifact-report-v1" in report
    assert "[`artifact.md`](artifact.md)" in report
    assert "`static_analysis`" in report
    assert "No enabled rule emitted a diagnostic" in report
    assert "`soft_agent_review`" in report
    assert "`request_changes`" in report
    assert "does not carry a combined quality score" in report
    assert render_artifact_report(record_dir, repository_root=Path.cwd()) == report

    report_path.write_text(report + "stale\n", encoding="utf-8")
    with pytest.raises(ValueError, match="stale or missing"):
        write_artifact_report(record_dir, repository_root=Path.cwd(), check=True)


def test_sqlite_catalog_is_rebuilt_from_generated_and_reference_records(
    tmp_path: Path,
) -> None:
    records = tmp_path / "records"
    generated = capture_readme_artifact(
        GENERATED_README,
        registry=records,
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        producer={"kind": "candidate", "id": "reademe-temp-modular-readme-v1"},
        memberships=[("reademe-temp-forward-test", "generated_output")],
        captured_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    attach_static_analysis_evidence(
        generated,
        run_path=STATIC_RUN,
        analyzer_path=ANALYZER,
        subject_id="reademe-temp-forward-test-readme",
        repository_root=Path.cwd(),
    )

    observation = next(
        json.loads(line)
        for line in CORPUS_OBSERVATIONS.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["source"]["repository"] == "pallets/flask"
    )
    source = observation["source"]
    reference = register_reference_artifact(
        registry=records,
        content_sha256=source["content_sha256"],
        locator=source["retrieval_url"],
        repository=source["repository"],
        revision=source["revision"],
        recorded_path=source["path"],
        role=observation["role"]["primary"],
        memberships=[("pilot-high-exposure-v1", "reference_sample")],
        captured_at=datetime.fromisoformat(
            observation["observed_at"].replace("Z", "+00:00")
        ),
        license_spdx=source["license_spdx"],
    )
    attach_observation_evidence(
        reference,
        observations_path=CORPUS_OBSERVATIONS,
        document_id=observation["document_id"],
        repository_root=Path.cwd(),
    )

    output = tmp_path / "catalog.sqlite"
    result = build_sqlite_catalog(
        records, output=output, repository_root=Path.cwd()
    )

    assert result["artifact_count"] == 2
    assert result["evidence_count"] == 2
    with sqlite3.connect(output) as connection:
        assert connection.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 2
        assert {
            row[0]
            for row in connection.execute("SELECT kind FROM provenance").fetchall()
        } == {"generated", "retrieved"}
        assert {
            row[0]
            for row in connection.execute("SELECT purpose FROM memberships").fetchall()
        } == {"generated_output", "reference_sample"}
        assert {
            row[0]
            for row in connection.execute("SELECT kind FROM evidence").fetchall()
        } == {"static_analysis", "structural_observation"}
        assert connection.execute(
            "SELECT diagnostic_count FROM evidence WHERE kind = 'static_analysis'"
        ).fetchone()[0] == 0

    rebuilt = build_sqlite_catalog(
        records, output=output, repository_root=Path.cwd()
    )
    assert rebuilt["artifact_count"] == 2


def test_committed_generated_and_reference_packages_are_complete(
    tmp_path: Path,
) -> None:
    generated = COMMITTED_RECORDS / "rm-f96b8e9d6c94dee9"
    reference = COMMITTED_RECORDS / "rm-1f2de14735b1ee9d"

    generated_result = verify_artifact_package(
        generated, repository_root=Path.cwd()
    )
    reference_result = verify_artifact_package(
        reference, repository_root=Path.cwd()
    )
    assert generated_result["evidence_kinds"] == [
        "soft_agent_review",
        "static_analysis",
        "structural_observation",
    ]
    assert reference_result["storage_mode"] == "external_reference"
    assert reference_result["evidence_kinds"] == [
        "static_analysis",
        "structural_observation",
    ]
    write_artifact_report(generated, repository_root=Path.cwd(), check=True)
    write_artifact_report(reference, repository_root=Path.cwd(), check=True)

    result = build_sqlite_catalog(
        COMMITTED_RECORDS,
        output=tmp_path / "catalog.sqlite",
        repository_root=Path.cwd(),
    )
    assert result == {
        "catalog": (tmp_path / "catalog.sqlite").resolve().as_posix(),
        "schema_version": 1,
        "artifact_count": 2,
        "evidence_count": 5,
    }
