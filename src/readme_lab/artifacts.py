"""Shared deterministic hashing, JSON, timestamp, and schema helpers."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any


def tree_sha256(root: Path) -> str:
    """Hash every regular file by relative path and content."""

    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    digest = hashlib.sha256()
    files = []
    for current_root, directories, names in os.walk(root, followlinks=False):
        current = Path(current_root)
        directories[:] = [name for name in directories if name != ".git"]
        files.extend(current / name for name in names)
        files.extend(
            current / name for name in directories if (current / name).is_symlink()
        )
    for path in sorted(files):
        relative_path = path.relative_to(root)
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


def sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of one file's bytes."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    """Write a JSON document deterministically, creating parent directories."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 timestamp ending in ``Z``."""

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def timestamp(value: datetime | None = None) -> str:
    """Normalize an optional aware datetime to a ``Z``-suffixed UTC timestamp."""

    resolved = value or datetime.now(UTC)
    if resolved.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return resolved.astimezone(UTC).isoformat().replace("+00:00", "Z")


def load_schema(
    name: str,
    source_path: Path | None = None,
    *,
    schema_root: Path | None = None,
) -> dict[str, Any]:
    """Load a JSON Schema from the repository or the packaged data fallback.

    ``source_path`` names the on-disk schema file directly; otherwise
    ``schema_root / name`` is used. When the on-disk copy is absent the schema
    packaged into the wheel under ``readme_lab/data/<name>`` is loaded.
    """

    if source_path is not None:
        path = source_path
    elif schema_root is not None:
        path = schema_root / name
    else:
        raise TypeError("load_schema requires source_path or schema_root")
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", name).read_text(
            encoding="utf-8"
        )
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError(f"{name} must contain a JSON object")
    return schema
