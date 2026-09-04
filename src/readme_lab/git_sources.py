"""Small Git and source-identity helpers for managed ingestion."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def run_git(
    repository: Path,
    *arguments: str,
    check: bool = True,
    binary: bool = False,
    input_data: bytes | str | None = None,
) -> bytes | str:
    """Run Git without a shell and return stdout."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=check,
        capture_output=True,
        text=not binary,
        input=input_data,
    )
    return result.stdout


def is_git_repository(path: Path) -> bool:
    """Return whether a path belongs to a Git working tree."""

    if not path.is_dir():
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_identity(repository: Path) -> tuple[str, str, str | None]:
    """Return immutable HEAD, tree, and optional branch identity."""

    head = run_git(repository, "rev-parse", "HEAD")
    tree = run_git(repository, "rev-parse", "HEAD^{tree}")
    branch = run_git(
        repository,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        check=False,
    )
    assert isinstance(head, str)
    assert isinstance(tree, str)
    assert isinstance(branch, str)
    return head.strip(), tree.strip(), branch.strip() or None


def sanitize_locator(locator: str) -> str:
    """Remove URL credentials, query parameters, and fragments."""

    value = locator.strip()
    if not value:
        raise ValueError("source locator must not be empty")
    if "://" in value:
        split = urlsplit(value)
        host = split.hostname or ""
        if split.port:
            host = f"{host}:{split.port}"
        return urlunsplit((split.scheme, host, split.path, "", ""))
    if re.match(r"^[^/@:]+@[^:]+:.+$", value):
        return value.split("@", 1)[1]
    return value


def repository_id_from_locator(locator: str) -> str:
    """Derive a display identity without claiming remote ownership."""

    sanitized = sanitize_locator(locator).rstrip("/")
    if "://" in sanitized:
        split = urlsplit(sanitized)
        path = split.path.removesuffix(".git").strip("/")
        return f"{split.hostname}:{path}" if split.hostname else path
    if ":" in sanitized and "/" in sanitized.split(":", 1)[1]:
        host, path = sanitized.split(":", 1)
        return f"{host}:{path.removesuffix('.git')}"
    path = Path(sanitized)
    return f"local:{path.name or 'repository'}"


def remote_records(
    repository: Path, *, repository_path: str = "."
) -> list[dict[str, str]]:
    """Capture sanitized fetch and push URLs for every configured remote."""

    output = run_git(repository, "remote")
    assert isinstance(output, str)
    records = []
    for name in sorted(line for line in output.splitlines() if line):
        fetch = run_git(repository, "remote", "get-url", name)
        push = run_git(repository, "remote", "get-url", "--push", name)
        assert isinstance(fetch, str)
        assert isinstance(push, str)
        records.append(
            {
                "repository_path": repository_path,
                "name": name,
                "fetch_url": sanitize_locator(fetch.strip()),
                "push_url": sanitize_locator(push.strip()),
            }
        )
    return records
