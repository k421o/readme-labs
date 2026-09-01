"""Materialize one verified README artifact in a disposable Git context."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from readme_lab.git_sources import git_identity, git_root, is_git_repository

MATERIALIZATION_TIMESTAMP = "2000-01-01T00:00:00Z"
MATERIALIZATION_COMMIT_MESSAGE = "Materialize README artifact for evaluation"
MATERIALIZATION_AUTHOR_NAME = "README Labs context materializer"
MATERIALIZATION_AUTHOR_EMAIL = "context@readme-labs.invalid"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_git(
    repository: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
    binary: bool = False,
) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=not binary,
        env=environment,
    )
    return result.stdout


def _clone_without_hardlinks(source: Path, destination: Path) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "clone",
            "--no-hardlinks",
            "--no-checkout",
            "--quiet",
            "--",
            str(source),
            str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _remove_destination(destination: Path) -> None:
    if destination.is_symlink():
        destination.unlink()
    elif destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists():
        destination.unlink()


def _base_status(base: Path) -> str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    output = _run_git(
        base,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        environment=environment,
    )
    assert isinstance(output, str)
    return output


def _validate_base_repository(base_repository: Path) -> tuple[Path, str, str]:
    base = base_repository.resolve()
    if not is_git_repository(base):
        raise ValueError(f"base repository is not a Git working tree: {base}")
    if git_root(base) != base:
        raise ValueError(f"base repository must be the working-tree root: {base}")
    if _base_status(base):
        raise ValueError(f"base repository must be clean: {base}")
    revision, tree, _branch = git_identity(base)
    return base, revision, tree


def _validate_target(target_readme: str | Path) -> tuple[Path, str]:
    relative = Path(target_readme)
    if not str(target_readme) or relative == Path("."):
        raise ValueError("target README path must not be empty")
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(
            f"target README path must be relative and contained: {target_readme}"
        )
    if any(part.casefold() == ".git" for part in relative.parts):
        raise ValueError("target README path must not address Git metadata")
    return relative, relative.as_posix()


def _contained_target(destination: Path, relative: Path) -> Path:
    root = destination.resolve()
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"target README path traverses a symlink: {relative}")
    resolved = current.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"target README path escapes its context: {relative}"
        ) from error
    if resolved.exists() and not resolved.is_file():
        raise ValueError(f"target README path is not a file: {relative}")
    return resolved


def _nul_paths(output: bytes) -> set[str]:
    return {
        value.decode("utf-8", errors="surrogateescape")
        for value in output.split(b"\0")
        if value
    }


def _changed_paths(repository: Path) -> set[str]:
    tracked = _run_git(
        repository,
        "diff",
        "--name-only",
        "-z",
        binary=True,
    )
    untracked = _run_git(
        repository,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        binary=True,
    )
    assert isinstance(tracked, bytes)
    assert isinstance(untracked, bytes)
    return _nul_paths(tracked) | _nul_paths(untracked)


def _commit_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": MATERIALIZATION_AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": MATERIALIZATION_AUTHOR_EMAIL,
            "GIT_AUTHOR_DATE": MATERIALIZATION_TIMESTAMP,
            "GIT_COMMITTER_NAME": MATERIALIZATION_AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": MATERIALIZATION_AUTHOR_EMAIL,
            "GIT_COMMITTER_DATE": MATERIALIZATION_TIMESTAMP,
        }
    )
    return environment


def _context_id(binding: dict[str, Any]) -> str:
    encoded = json.dumps(
        binding,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"readme-context:{_sha256(encoded)}"


def _load_embedded_artifact(record_dir: Path) -> tuple[dict[str, Any], bytes]:
    # This import stays local so agent_evaluation can import the materializer later;
    # readme_artifacts currently imports evaluator loaders for evidence validation.
    from readme_lab.readme_artifacts import load_artifact_record

    record = load_artifact_record(record_dir)
    storage = record["artifact"]["storage"]
    if storage["mode"] != "embedded":
        raise ValueError("context materialization requires an embedded README artifact")
    stored_artifact = record_dir / storage["path"]
    if stored_artifact.is_symlink():
        raise ValueError("embedded README artifact must not be a symlink")
    artifact_path = stored_artifact.resolve()
    try:
        artifact_path.relative_to(record_dir)
    except ValueError as error:
        raise ValueError("embedded README artifact escapes its record") from error
    body = artifact_path.read_bytes()
    digest = record["artifact"]["content_sha256"]
    if _sha256(body) != digest:
        raise ValueError("embedded README artifact digest mismatch")
    return record, body


def materialize_readme_context(
    base_repository: Path,
    record_dir: Path,
    destination: Path,
    *,
    target_readme: str | Path = "README.md",
) -> dict[str, Any]:
    """Clone a clean base and bind one verified README in an ephemeral commit.

    The caller owns the returned destination and is expected to remove it after
    evaluation. Any failure during materialization removes the partial clone.
    """

    raw_destination = Path(destination)
    if raw_destination.is_symlink() or raw_destination.exists():
        raise FileExistsError(f"destination already exists: {raw_destination}")
    destination = raw_destination.resolve(strict=False)
    if destination.is_symlink() or destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    base, base_revision, base_tree = _validate_base_repository(base_repository)
    try:
        destination.relative_to(base)
    except ValueError:
        pass
    else:
        raise ValueError("destination must not be inside the base repository")

    record_dir = Path(record_dir).resolve()
    try:
        destination.relative_to(record_dir)
    except ValueError:
        pass
    else:
        raise ValueError("destination must not be inside the artifact record")
    record, body = _load_embedded_artifact(record_dir)
    relative_target, target_path_text = _validate_target(target_readme)
    digest = record["artifact"]["content_sha256"]
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        _clone_without_hardlinks(base, destination)
        remotes_output = _run_git(destination, "remote")
        assert isinstance(remotes_output, str)
        removed_remotes = sorted(remotes_output.splitlines())
        for remote in removed_remotes:
            _run_git(destination, "remote", "remove", remote)

        _run_git(destination, "config", "core.autocrlf", "false")
        _run_git(destination, "config", "commit.gpgsign", "false")
        _run_git(
            destination,
            "checkout",
            "--quiet",
            "--detach",
            base_revision,
        )
        cloned_revision, cloned_tree, _branch = git_identity(destination)
        if (cloned_revision, cloned_tree) != (base_revision, base_tree):
            raise RuntimeError("cloned base identity does not match the source")
        clone_status = _run_git(
            destination,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        assert isinstance(clone_status, str)
        if clone_status:
            raise RuntimeError("cloned base repository is not clean")

        target = _contained_target(destination, relative_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        if _sha256(target.read_bytes()) != digest:
            raise RuntimeError("materialized README digest mismatch")

        changed_paths = _changed_paths(destination)
        if changed_paths - {target_path_text}:
            raise RuntimeError("README materialization changed an unexpected path")
        _run_git(destination, "add", "--force", "--", target_path_text)

        staged = _run_git(
            destination,
            "show",
            f":{target_path_text}",
            binary=True,
        )
        assert isinstance(staged, bytes)
        if _sha256(staged) != digest:
            raise RuntimeError("staged README digest does not match its artifact")

        _run_git(
            destination,
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            MATERIALIZATION_COMMIT_MESSAGE,
            environment=_commit_environment(),
        )
        materialized_revision, materialized_tree, _branch = git_identity(destination)
        parent = _run_git(destination, "rev-parse", "HEAD^")
        assert isinstance(parent, str)
        if parent.strip() != base_revision:
            raise RuntimeError("materialized context has an unexpected parent")

        committed = _run_git(
            destination,
            "show",
            f"HEAD:{target_path_text}",
            binary=True,
        )
        assert isinstance(committed, bytes)
        if _sha256(committed) != digest:
            raise RuntimeError("committed README digest does not match its artifact")
        changed_in_commit = _run_git(
            destination,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            "HEAD^",
            "HEAD",
            binary=True,
        )
        assert isinstance(changed_in_commit, bytes)
        if _nul_paths(changed_in_commit) - {target_path_text}:
            raise RuntimeError("materialized commit changed an unexpected path")
        status = _run_git(
            destination,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        assert isinstance(status, str)
        if status:
            raise RuntimeError("materialized context is not clean")
        current_base_revision, current_base_tree, _branch = git_identity(base)
        if (current_base_revision, current_base_tree) != (base_revision, base_tree):
            raise RuntimeError("base repository changed during materialization")
        if _base_status(base):
            raise RuntimeError("base repository changed during materialization")

        artifact_binding = {
            "record_id": record["record_id"],
            "artifact_id": record["artifact"]["id"],
            "content_sha256": digest,
            "storage_path": record["artifact"]["storage"]["path"],
            "target_path": target_path_text,
        }
        identity_binding = {
            "base_revision": base_revision,
            "base_tree": base_tree,
            "materialized_revision": materialized_revision,
            "materialized_tree": materialized_tree,
            "artifact": artifact_binding,
        }
        return {
            "context_id": _context_id(identity_binding),
            "destination": destination.as_posix(),
            "base": {
                "repository": base.as_posix(),
                "revision": base_revision,
                "tree": base_tree,
            },
            "materialized": {
                "revision": materialized_revision,
                "tree": materialized_tree,
            },
            "artifact_binding": artifact_binding,
            "removed_remotes": removed_remotes,
        }
    except BaseException:
        _remove_destination(destination)
        raise
