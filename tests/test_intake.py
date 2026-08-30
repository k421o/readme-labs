from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from readme_lab.intake import fingerprint_git_path, verify_intake_manifest


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_checked_in_reademe_temp_snapshots_verify_without_source_checkout() -> None:
    result = verify_intake_manifest(
        Path("intake/manifests/reademe-temp-v1.json")
    )

    assert result["verified"] is True
    assert all(item["snapshot_verified"] is True for item in result["items"])
    assert all(item["source_verified"] is None for item in result["items"])


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
    assert result["items"][0]["source_verified"] is True
    assert result["items"][0]["snapshot_verified"] is True

    (snapshot / "research.md").write_text("changed\n", encoding="utf-8")
    changed = verify_intake_manifest(
        manifest_path, source_root=source, repository_root=tmp_path
    )
    assert changed["verified"] is False
    assert hashlib.sha256(b"changed\n").hexdigest() != fingerprint["sha256"]
