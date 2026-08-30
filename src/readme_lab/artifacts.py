"""Content-addressed artifact helpers shared by intake and candidates."""

from __future__ import annotations

import hashlib
from pathlib import Path


def tree_sha256(root: Path) -> str:
    """Hash every regular file by relative path and content."""

    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        if ".git" in relative_path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"artifact trees must not contain symlinks: {path}")
        if not path.is_file():
            continue
        relative = relative_path.as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def artifact_sha256(path: Path, artifact_type: str) -> str:
    """Hash one file or one complete directory tree."""

    if artifact_type == "file":
        if path.is_symlink():
            raise ValueError(f"artifact files must not be symlinks: {path}")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if artifact_type == "tree":
        return tree_sha256(path)
    raise ValueError(f"unsupported artifact type: {artifact_type}")


def resolve_contained(root: Path, relative: str) -> Path:
    """Resolve a repository-relative path and reject traversal."""

    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes its declared root: {relative}") from error
    return path
