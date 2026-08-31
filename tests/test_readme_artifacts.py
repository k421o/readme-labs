from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from readme_lab.readme_artifacts import (
    add_artifact_occurrence,
    attach_observation_evidence,
    attach_soft_review_evidence,
    attach_static_analysis_evidence,
    capture_readme_artifact,
    inspect_captured_artifact,
    load_artifact_evidence,
    load_artifact_record,
    record_id_for_digest,
    register_reference_artifact,
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
    "intake/snapshots/reademe-temp-forward-test/forward-test/assembled/README.md"
)
CORPUS_OBSERVATIONS = Path("corpus/observations/pilot-high-exposure-v1.jsonl")


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
