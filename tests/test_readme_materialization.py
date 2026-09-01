from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

import readme_lab.readme_materialization as materialization
from readme_lab.readme_artifacts import (
    capture_readme_artifact,
    load_artifact_record,
    register_reference_artifact,
)
from readme_lab.readme_materialization import materialize_readme_context


def git(repository: Path, *arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return result.stdout


def create_base_repository(
    root: Path,
    *,
    files: dict[str, bytes] | None = None,
) -> Path:
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    for relative, body in (files or {"README.md": b"# Base README\n"}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    git(root, "add", ".")
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "Base Author",
            "GIT_AUTHOR_EMAIL": "base@example.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_NAME": "Base Author",
            "GIT_COMMITTER_EMAIL": "base@example.invalid",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
    )
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Base fixture"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return root


def create_embedded_record(root: Path, body: bytes) -> Path:
    source = root / "artifact-source.md"
    source.write_bytes(body)
    return capture_readme_artifact(
        source,
        registry=root / "records",
        provenance_kind="generated",
        boundary="completed_generation",
        pre_capture_editability="mutable",
        ownership="owned",
        visibility="local_only",
        repository="local:test-artifact",
        revision="generated-output",
        recorded_path="README.md",
        role="repository_root",
        producer={
            "kind": "skill",
            "id": "test-readme-generator",
            "version": "1.0.0",
            "run_id": "test-generation-run",
        },
        captured_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )


def snapshot_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def test_materializes_verified_artifact_with_deterministic_identity(
    tmp_path: Path,
) -> None:
    base = create_base_repository(
        tmp_path / "base",
        files={
            "README.md": b"# Old contextual README\n",
            "src/example.py": b"VALUE = 1\n",
        },
    )
    git(base, "remote", "add", "upstream", "https://example.invalid/base.git")
    body = b"# Canonical README\n\nMaterialized temporarily.\n"
    record_dir = create_embedded_record(tmp_path, body)
    record = load_artifact_record(record_dir)
    base_revision = str(git(base, "rev-parse", "HEAD")).strip()
    base_tree = str(git(base, "rev-parse", "HEAD^{tree}")).strip()
    base_files = snapshot_files(base)
    record_files = snapshot_files(record_dir)

    first = materialize_readme_context(base, record_dir, tmp_path / "context-one")
    second = materialize_readme_context(base, record_dir, tmp_path / "context-two")

    assert first["context_id"] == second["context_id"]
    assert first["materialized"] == second["materialized"]
    assert first["base"] == {
        "repository": base.as_posix(),
        "revision": base_revision,
        "tree": base_tree,
    }
    assert first["artifact_binding"] == {
        "record_id": record["record_id"],
        "artifact_id": record["artifact"]["id"],
        "content_sha256": hashlib.sha256(body).hexdigest(),
        "storage_path": "artifact.md",
        "target_path": "README.md",
    }
    assert first["removed_remotes"] == ["origin"]

    for destination_name in ("context-one", "context-two"):
        destination = tmp_path / destination_name
        assert (destination / "README.md").read_bytes() == body
        assert (destination / "src/example.py").read_bytes() == b"VALUE = 1\n"
        assert str(git(destination, "remote")).strip() == ""
        assert str(git(destination, "status", "--porcelain=v1")).strip() == ""
        assert str(git(destination, "rev-parse", "HEAD^")).strip() == base_revision
        assert (
            str(
                git(
                    destination,
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "HEAD^",
                    "HEAD",
                )
            ).strip()
            == "README.md"
        )
        identity = str(
            git(
                destination,
                "show",
                "--quiet",
                "--format=%an%n%ae%n%at%n%cn%n%ce%n%ct%n%s",
                "HEAD",
            )
        ).splitlines()
        assert identity == [
            "README Labs context materializer",
            "context@readme-labs.invalid",
            "946684800",
            "README Labs context materializer",
            "context@readme-labs.invalid",
            "946684800",
            "Materialize README artifact for evaluation",
        ]

    base_object = base / ".git/objects" / base_revision[:2] / base_revision[2:]
    cloned_object = (
        tmp_path
        / "context-one/.git/objects"
        / base_revision[:2]
        / base_revision[2:]
    )
    assert base_object.is_file()
    assert cloned_object.is_file()
    assert base_object.stat().st_ino != cloned_object.stat().st_ino
    assert not (tmp_path / "context-one/.git/objects/info/alternates").exists()

    assert str(git(base, "rev-parse", "HEAD")).strip() == base_revision
    assert str(git(base, "rev-parse", "HEAD^{tree}")).strip() == base_tree
    assert str(git(base, "status", "--porcelain=v1")).strip() == ""
    assert str(git(base, "remote")).strip() == "upstream"
    assert snapshot_files(base) == base_files
    assert snapshot_files(record_dir) == record_files


def test_materializes_at_a_contained_nested_target(tmp_path: Path) -> None:
    base = create_base_repository(
        tmp_path / "base",
        files={"README.md": b"# Root stays unchanged\n", "src/app.py": b"pass\n"},
    )
    body = b"# Nested contextual README\n"
    record_dir = create_embedded_record(tmp_path, body)
    destination = tmp_path / "context"

    result = materialize_readme_context(
        base,
        record_dir,
        destination,
        target_readme="docs/README.md",
    )

    assert (destination / "docs/README.md").read_bytes() == body
    assert (destination / "README.md").read_bytes() == b"# Root stays unchanged\n"
    assert result["artifact_binding"]["target_path"] == "docs/README.md"
    assert (
        str(
            git(
                destination,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD^",
                "HEAD",
            )
        ).strip()
        == "docs/README.md"
    )


def test_identical_base_readme_still_gets_an_ephemeral_commit(tmp_path: Path) -> None:
    body = b"# Already canonical\n"
    base = create_base_repository(tmp_path / "base", files={"README.md": body})
    record_dir = create_embedded_record(tmp_path, body)

    result = materialize_readme_context(base, record_dir, tmp_path / "context")

    assert result["materialized"]["revision"] != result["base"]["revision"]
    assert result["materialized"]["tree"] == result["base"]["tree"]
    assert str(git(tmp_path / "context", "rev-parse", "HEAD^")).strip() == result[
        "base"
    ]["revision"]


@pytest.mark.parametrize(
    "target",
    ["../README.md", "/outside/README.md", ".git/config", "nested/.GIT/config", ""],
)
def test_rejects_uncontained_or_git_metadata_targets(
    tmp_path: Path,
    target: str,
) -> None:
    base = create_base_repository(tmp_path / "base")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    destination = tmp_path / "context"

    with pytest.raises(ValueError):
        materialize_readme_context(
            base,
            record_dir,
            destination,
            target_readme=target,
        )

    assert not destination.exists()


def test_rejects_dirty_base_without_creating_destination(tmp_path: Path) -> None:
    base = create_base_repository(tmp_path / "base")
    (base / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    record_files = snapshot_files(record_dir)
    destination = tmp_path / "context"

    with pytest.raises(ValueError, match="must be clean"):
        materialize_readme_context(base, record_dir, destination)

    assert not destination.exists()
    assert (base / "untracked.txt").read_text(encoding="utf-8") == "dirty\n"
    assert snapshot_files(record_dir) == record_files


def test_rejects_external_reference_artifact(tmp_path: Path) -> None:
    base = create_base_repository(tmp_path / "base")
    body_digest = hashlib.sha256(b"# External\n").hexdigest()
    record_dir = register_reference_artifact(
        registry=tmp_path / "records",
        content_sha256=body_digest,
        locator="https://example.invalid/repository/README.md",
        repository="example/repository",
        revision="a" * 40,
        recorded_path="README.md",
        role="repository_root",
        captured_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )
    destination = tmp_path / "context"

    with pytest.raises(ValueError, match="requires an embedded README artifact"):
        materialize_readme_context(base, record_dir, destination)

    assert not destination.exists()


def test_existing_destination_is_never_replaced(tmp_path: Path) -> None:
    base = create_base_repository(tmp_path / "base")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    destination = tmp_path / "context"
    destination.mkdir()
    sentinel = destination / "sentinel.txt"
    sentinel.write_text("keep\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        materialize_readme_context(base, record_dir, destination)

    assert sentinel.read_text(encoding="utf-8") == "keep\n"


def test_failure_after_clone_removes_partial_destination(tmp_path: Path) -> None:
    base = create_base_repository(
        tmp_path / "base",
        files={"README.md": b"# Base\n", "docs": b"not a directory\n"},
    )
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    base_revision = str(git(base, "rev-parse", "HEAD")).strip()
    base_files = snapshot_files(base)
    record_files = snapshot_files(record_dir)
    destination = tmp_path / "context"

    with pytest.raises(FileExistsError):
        materialize_readme_context(
            base,
            record_dir,
            destination,
            target_readme="docs/README.md",
        )

    assert not destination.exists()
    assert str(git(base, "rev-parse", "HEAD")).strip() == base_revision
    assert str(git(base, "status", "--porcelain=v1")).strip() == ""
    assert snapshot_files(base) == base_files
    assert snapshot_files(record_dir) == record_files


def test_partial_clone_failure_is_rolled_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = create_base_repository(tmp_path / "base")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    destination = tmp_path / "context"

    def fail_after_creating_destination(source: Path, clone: Path) -> None:
        del source
        clone.mkdir()
        (clone / "partial").write_text("partial\n", encoding="utf-8")
        raise subprocess.CalledProcessError(1, ["git", "clone"])

    monkeypatch.setattr(
        materialization,
        "_clone_without_hardlinks",
        fail_after_creating_destination,
    )

    with pytest.raises(subprocess.CalledProcessError):
        materialize_readme_context(base, record_dir, destination)

    assert not destination.exists()


def test_destination_must_not_be_inside_base_repository(tmp_path: Path) -> None:
    base = create_base_repository(tmp_path / "base")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    destination = base / "context"

    with pytest.raises(ValueError, match="must not be inside"):
        materialize_readme_context(base, record_dir, destination)

    assert not destination.exists()
    assert str(git(base, "status", "--porcelain=v1")).strip() == ""


def test_destination_must_not_be_inside_artifact_record(tmp_path: Path) -> None:
    base = create_base_repository(tmp_path / "base")
    record_dir = create_embedded_record(tmp_path, b"# Artifact\n")
    record_files = snapshot_files(record_dir)
    destination = record_dir / "context"

    with pytest.raises(ValueError, match="must not be inside the artifact record"):
        materialize_readme_context(base, record_dir, destination)

    assert not destination.exists()
    assert snapshot_files(record_dir) == record_files
