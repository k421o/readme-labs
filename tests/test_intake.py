from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from readme_lab.artifacts import artifact_sha256
from readme_lab.intake import fingerprint_git_path, verify_intake_manifest
from readme_lab.readme_artifacts import transfer_readme_artifact


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def write_landed_manifest(tmp_path: Path) -> tuple[Path, Path, Path]:
    body = b"# Landed README\n"
    digest = hashlib.sha256(body).hexdigest()
    record_id = f"rm-{digest[:16]}"
    source_root = tmp_path / "managed-checkout"
    source_root.mkdir()
    managed_source = source_root / "README.md"
    managed_source.write_bytes(body)
    transfer = transfer_readme_artifact(
        managed_source,
        registry=tmp_path / "readmes/records",
        provenance_kind="ingested",
        boundary="ingestion_selection",
        pre_capture_editability="not_applicable",
        ownership="owned",
        visibility="local_only",
        repository="local:source",
        revision="workspace@2026-09-01T12:00:00Z",
        recorded_path="README.md",
        captured_at=datetime(2026, 9, 1, 12, 1, tzinfo=UTC),
    )
    destination = transfer.body_path
    manifest = {
        "schema_version": 2,
        "id": "landed-readme-intake",
        "title": "Landed README intake",
        "observed_at": "2026-09-01T12:00:00Z",
        "source_repository": {
            "repository_id": "local:source",
            "remote": None,
            "default_branch": None,
            "availability": "local_only",
        },
        "items": [
            {
                "id": "completed-readme",
                "kind": "readme_artifact",
                "source": {
                    "state": "workspace",
                    "observed_at": "2026-09-01T12:00:00Z",
                    "path": "README.md",
                    "artifact_type": "file",
                    "sha256": digest,
                },
                "landing": {
                    "record_id": record_id,
                    "path": destination.relative_to(tmp_path).as_posix(),
                    "artifact_type": "file",
                    "sha256": digest,
                    "transferred_at": "2026-09-01T12:01:00Z",
                    "managed_source_path": "README.md",
                    "managed_source_absent": True,
                },
                "intake_mode": "landed",
                "status": "admitted",
                "authority": "evidence_only",
                "limitations": [],
            }
        ],
        "relationships": [],
        "limitations": [],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, source_root, destination


def test_checked_in_reademe_temp_custody_verifies_without_source_checkout() -> None:
    result = verify_intake_manifest(
        Path("intake/manifests/reademe-temp-v1.json")
    )

    assert result["verified"] is True
    assert all(
        item["snapshot_verified"] is True or item["landing_verified"] is True
        for item in result["items"]
    )
    assert all(item["source_verified"] is None for item in result["items"])
    forward_test = next(
        item for item in result["items"] if item["id"] == "modular-readme-forward-test"
    )
    assert forward_test["reconstruction_verified"] is True


def test_v2_landing_verifies_destination_and_managed_source_absence(
    tmp_path: Path,
) -> None:
    manifest, source_root, _ = write_landed_manifest(tmp_path)

    result = verify_intake_manifest(
        manifest, source_root=source_root, repository_root=tmp_path
    )

    assert result["verified"] is True
    assert result["items"] == [
        {
            "id": "completed-readme",
            "source_verified": True,
            "snapshot_verified": None,
            "landing_verified": True,
            "source_absent_verified": True,
            "reconstruction_verified": None,
            "verified": True,
        }
    ]
    without_checkout = verify_intake_manifest(manifest, repository_root=tmp_path)
    assert without_checkout["verified"] is True
    assert without_checkout["items"][0]["source_absent_verified"] is None


def test_v2_landing_rejects_managed_source_reappearance(tmp_path: Path) -> None:
    manifest, source_root, destination = write_landed_manifest(tmp_path)
    (source_root / "README.md").write_bytes(destination.read_bytes())

    result = verify_intake_manifest(
        manifest, source_root=source_root, repository_root=tmp_path
    )

    assert result["verified"] is False
    assert result["items"][0]["landing_verified"] is True
    assert result["items"][0]["source_absent_verified"] is False


def test_v2_landing_rejects_destination_tampering(tmp_path: Path) -> None:
    manifest, source_root, destination = write_landed_manifest(tmp_path)
    destination.write_text("# Mutated\n", encoding="utf-8")

    result = verify_intake_manifest(
        manifest, source_root=source_root, repository_root=tmp_path
    )

    assert result["verified"] is False
    assert result["items"][0]["landing_verified"] is False
    assert result["items"][0]["source_absent_verified"] is True


def test_v2_landing_rejects_body_without_a_valid_artifact_record(
    tmp_path: Path,
) -> None:
    manifest, source_root, destination = write_landed_manifest(tmp_path)
    (destination.parent / "record.json").unlink()

    result = verify_intake_manifest(
        manifest, source_root=source_root, repository_root=tmp_path
    )

    assert result["verified"] is False
    assert result["items"][0]["landing_verified"] is False


def test_v2_reconstructs_a_pruned_tree_with_its_landed_readme(
    tmp_path: Path,
) -> None:
    manifest_path, _, destination = write_landed_manifest(tmp_path)
    snapshot = tmp_path / "intake/snapshots/trial"
    snapshot.mkdir(parents=True)
    (snapshot / "notes.txt").write_text("trial context\n", encoding="utf-8")
    original = tmp_path / "original"
    (original / "assembled").mkdir(parents=True)
    (original / "notes.txt").write_text("trial context\n", encoding="utf-8")
    (original / "assembled/README.md").write_bytes(destination.read_bytes())
    original_sha256 = artifact_sha256(original, "tree")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["items"].insert(
        0,
        {
            "id": "trial-tree",
            "kind": "trial_evidence",
            "source": {
                "state": "workspace",
                "observed_at": "2026-09-01T12:00:00Z",
                "path": "trial",
                "artifact_type": "tree",
                "sha256": original_sha256,
            },
            "snapshot": {
                "path": snapshot.relative_to(tmp_path).as_posix(),
                "artifact_type": "tree",
                "sha256": artifact_sha256(snapshot, "tree"),
            },
            "reconstruction": {
                "artifact_type": "tree",
                "sha256": original_sha256,
                "insertions": [
                    {
                        "source_item_id": "completed-readme",
                        "path": "assembled/README.md",
                        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                    }
                ],
            },
            "intake_mode": "snapshot",
            "status": "admitted",
            "authority": "evidence_only",
            "limitations": [],
        },
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_intake_manifest(manifest_path, repository_root=tmp_path)

    assert result["verified"] is True
    assert result["items"][0]["snapshot_verified"] is True
    assert result["items"][0]["reconstruction_verified"] is True


def test_git_fingerprint_and_source_verification_are_content_addressed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "--quiet", "--initial-branch=main")
    git(source, "config", "user.name", "readme-labs")
    git(source, "config", "user.email", "eval@readme-labs.invalid")
    (source / "notes").mkdir()
    (source / "notes/research.md").write_text("finding\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "source")
    revision = git(source, "rev-parse", "HEAD")
    fingerprint = fingerprint_git_path(
        source,
        revision=revision,
        source_path="notes",
        artifact_type="tree",
    )

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "research.md").write_text("finding\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "id": "test-intake",
        "title": "Test intake",
        "observed_at": "2026-08-30T00:00:00Z",
        "source_repository": {
            "repository_id": "local:test",
            "remote": None,
            "default_branch": "main",
            "availability": "local_only",
        },
        "items": [
            {
                "id": "research-tree",
                "kind": "research_content",
                "source": fingerprint,
                "snapshot": {
                    "path": "snapshot",
                    "artifact_type": "tree",
                    "sha256": fingerprint["sha256"],
                },
                "intake_mode": "snapshot",
                "status": "admitted",
                "authority": "evidence_only",
                "limitations": [],
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_intake_manifest(
        manifest_path, source_root=source, repository_root=tmp_path
    )

    assert result["verified"] is True
    assert json.loads(manifest_path.read_text(encoding="utf-8"))[
        "schema_version"
    ] == 1
    assert result["items"][0]["source_verified"] is True
    assert result["items"][0]["snapshot_verified"] is True

    (snapshot / "research.md").write_text("changed\n", encoding="utf-8")
    changed = verify_intake_manifest(
        manifest_path, source_root=source, repository_root=tmp_path
    )
    assert changed["verified"] is False
    assert hashlib.sha256(b"changed\n").hexdigest() != fingerprint["sha256"]
