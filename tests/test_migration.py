from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from readme_lab.migration import (
    build_git_migration_receipt,
    load_git_migration_receipt,
)

CHECKED_IN_RECEIPT = Path(
    "intake/migrations/reademe-temp-forward-test-readme-v1.json"
)


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repository(path: Path, content: str) -> tuple[Path, str]:
    path.mkdir()
    git(path, "init", "--quiet", "--initial-branch=main")
    git(path, "config", "user.name", "README Labs test")
    git(path, "config", "user.email", "test@readme-labs.invalid")
    (path / "artifact.md").write_text(content, encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "--quiet", "-m", "artifact")
    return path, git(path, "rev-parse", "HEAD")


def test_migration_receipt_refuses_to_replace_provenance_with_a_false_link(
    tmp_path: Path,
) -> None:
    source, source_revision = repository(tmp_path / "source", "source\n")
    destination, destination_revision = repository(
        tmp_path / "destination", "different\n"
    )
    git(source, "rm", "artifact.md")
    git(source, "commit", "--quiet", "-m", "remove")
    deletion_revision = git(source, "rev-parse", "HEAD")

    with pytest.raises(ValueError, match="content digests differ"):
        build_git_migration_receipt(
            receipt_id="false-migration",
            source_repository=source,
            source_repository_id="owned:source",
            source_revision=source_revision,
            source_path="artifact.md",
            source_deletion_revision=deletion_revision,
            destination_repository=destination,
            destination_repository_id="owned:destination",
            destination_revision=destination_revision,
            destination_path="artifact.md",
            artifact_type="file",
            source_settlement="local_commit",
            destination_settlement="local_commit",
        )


def test_migration_receipt_requires_physical_absence_in_source_history(
    tmp_path: Path,
) -> None:
    source, source_revision = repository(tmp_path / "source", "same\n")
    destination, destination_revision = repository(tmp_path / "destination", "same\n")

    with pytest.raises(ValueError, match="still exists"):
        build_git_migration_receipt(
            receipt_id="not-cleaned",
            source_repository=source,
            source_repository_id="owned:source",
            source_revision=source_revision,
            source_path="artifact.md",
            source_deletion_revision=source_revision,
            destination_repository=destination,
            destination_repository_id="owned:destination",
            destination_revision=destination_revision,
            destination_path="artifact.md",
            artifact_type="file",
            source_settlement="local_commit",
            destination_settlement="local_commit",
        )


def test_checked_in_readme_move_receipt_matches_the_single_live_body() -> None:
    receipt = load_git_migration_receipt(CHECKED_IN_RECEIPT)
    source = Path(receipt["source"]["path"])
    destination = Path(receipt["destination"]["path"])

    assert receipt["content_equivalent"] is True
    assert receipt["duplicate_snapshot_retained"] is False
    assert receipt["source"]["path_absent"] is True
    assert not source.exists()
    assert destination.is_file()
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    assert (
        digest
        == receipt["source"]["sha256"]
        == receipt["destination"]["sha256"]
    )
