"""Enforce one durable repository path for each README body at HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

README_NAME = re.compile(r"^readme(?:\..+)?$", re.IGNORECASE)
REVISION = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
RAW_OUTPUT_FIELDS = frozenset({"aggregated_output", "output", "stderr", "stdout"})


def _git_root(repository: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def _tracked_paths(repository: Path) -> set[PurePosixPath]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return {
        PurePosixPath(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw
    }


def _worktree_file(repository: Path, relative: PurePosixPath) -> Path | None:
    path = repository.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file():
        return None
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _source_sha256(path: Path) -> str:
    return _sha256(path) if path.is_file() else _tree_sha256(path)


def _git_source_sha256(
    repository: Path,
    source: PurePosixPath,
    revision: str,
    *,
    source_is_file: bool,
) -> str:
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != revision:
        raise ValueError("source_revision does not name its full commit object")

    object_spec = f"{revision}:{source.as_posix()}"
    object_type = subprocess.run(
        ["git", "cat-file", "-t", object_spec],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    expected_type = "blob" if source_is_file else "tree"
    if object_type != expected_type:
        raise ValueError(
            f"source changed kind between the worktree and revision ({object_type})"
        )
    if source_is_file:
        content = subprocess.run(
            ["git", "cat-file", "blob", object_spec],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        return hashlib.sha256(content).hexdigest()

    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-z", revision, "--", source.as_posix()],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    digest = hashlib.sha256()
    for entry in (item for item in listing.split(b"\0") if item):
        metadata, raw_path = entry.split(b"\t", 1)
        object_kind, object_id = metadata.split()[1:]
        if object_kind != b"blob":
            raise ValueError("source revision contains a non-blob Git object")
        committed_path = PurePosixPath(raw_path.decode("utf-8"))
        relative = committed_path.relative_to(source).as_posix().encode()
        content = subprocess.run(
            ["git", "cat-file", "blob", object_id.decode("ascii")],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        digest.update(relative)
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _safe_relative(value: object, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise ValueError(f"{label} must stay inside its declared root: {value!r}")
    return path


def _record_body_paths(
    repository: Path,
    tracked: set[PurePosixPath],
) -> tuple[set[PurePosixPath], list[str]]:
    bodies: set[PurePosixPath] = set()
    violations: list[str] = []
    for record_path in sorted(tracked):
        if not record_path.match("readmes/records/*/record.json"):
            continue
        worktree_record = _worktree_file(repository, record_path)
        if worktree_record is None:
            continue
        try:
            record = json.loads(worktree_record.read_text(encoding="utf-8"))
            artifact = record["artifact"]
            storage = artifact["storage"]
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as error:
            violations.append(f"cannot inspect README record {record_path}: {error}")
            continue
        if artifact.get("media_type") != "text/markdown":
            continue
        if storage.get("mode") != "embedded":
            continue
        try:
            stored = _safe_relative(
                storage.get("path"), label=f"{record_path} embedded path"
            )
        except ValueError as error:
            violations.append(str(error))
            continue
        body_path = record_path.parent / stored
        if body_path.parent != record_path.parent:
            violations.append(
                f"embedded README body escapes its record directory: {body_path}"
            )
            continue
        if body_path not in tracked or _worktree_file(repository, body_path) is None:
            violations.append(
                f"embedded README body is not a tracked file: {body_path}"
            )
            continue
        bodies.add(body_path)
    return bodies, violations


def _generated_pairs(
    repository: Path,
    tracked: set[PurePosixPath],
) -> tuple[set[tuple[PurePosixPath, PurePosixPath]], list[str]]:
    """Expand explicit generated-product source/destination tree mappings."""

    pairs: set[tuple[PurePosixPath, PurePosixPath]] = set()
    violations: list[str] = []
    for upstream_path in sorted(tracked):
        if upstream_path.name != "UPSTREAM.json" or not upstream_path.is_relative_to(
            PurePosixPath("products")
        ):
            continue
        worktree_upstream = _worktree_file(repository, upstream_path)
        if worktree_upstream is None:
            continue
        try:
            upstream = json.loads(worktree_upstream.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            violations.append(
                f"cannot inspect generated provenance {upstream_path}: {error}"
            )
            continue
        if not isinstance(upstream, dict) or not isinstance(
            upstream.get("generated_by"), str
        ):
            violations.append(
                f"generated provenance lacks generated_by: {upstream_path}"
            )
            continue
        sources = upstream.get("sources")
        if not isinstance(sources, list):
            violations.append(f"generated provenance lacks sources: {upstream_path}")
            continue
        product_root = upstream_path.parent
        for index, item in enumerate(sources):
            label = f"{upstream_path} sources[{index}]"
            if not isinstance(item, dict):
                violations.append(f"{label} must be an object")
                continue
            source_revision = str(item.get("source_revision", ""))
            if REVISION.fullmatch(source_revision) is None:
                violations.append(f"{label} lacks a full source revision")
                continue
            source_digest = str(item.get("source_sha256", ""))
            if DIGEST.fullmatch(source_digest) is None:
                violations.append(f"{label} lacks a source digest")
                continue
            try:
                source = _safe_relative(item.get("source"), label=f"{label} source")
                destination = _safe_relative(
                    item.get("destination"), label=f"{label} destination"
                )
            except ValueError as error:
                violations.append(str(error))
                continue
            destination_root = product_root / destination
            if source.is_relative_to(PurePosixPath("products")):
                violations.append(
                    f"generated source must be outside products/: {source}"
                )
                continue

            source_worktree = repository.joinpath(*source.parts)
            if source_worktree.is_symlink() or not source_worktree.exists():
                violations.append(f"generated source is missing: {source}")
                continue
            current_digest = _source_sha256(source_worktree)
            if current_digest != source_digest:
                violations.append(
                    f"generated source digest does not match current source: {source}"
                )
                continue
            try:
                revision_digest = _git_source_sha256(
                    repository,
                    source,
                    source_revision,
                    source_is_file=source_worktree.is_file(),
                )
            except (
                subprocess.CalledProcessError,
                UnicodeDecodeError,
                ValueError,
            ) as error:
                violations.append(
                    f"cannot inspect generated source revision for {source}: {error}"
                )
                continue
            if revision_digest != source_digest:
                violations.append(
                    "generated source revision does not match declared digest: "
                    f"{source} at {source_revision}"
                )
                continue
            if source_worktree.is_file():
                source_files = [source]
            else:
                prefix = source.parts
                source_files = sorted(
                    path
                    for path in tracked
                    if path.parts[: len(prefix)] == prefix
                    and _worktree_file(repository, path) is not None
                )
            for source_file in source_files:
                suffix = (
                    PurePosixPath()
                    if source_worktree.is_file()
                    else source_file.relative_to(source)
                )
                generated_file = destination_root / suffix
                source_path = _worktree_file(repository, source_file)
                generated_path = _worktree_file(repository, generated_file)
                if (
                    source_path is not None
                    and generated_file in tracked
                    and generated_path is not None
                    and source_path.read_bytes() == generated_path.read_bytes()
                ):
                    pairs.add((source_file, generated_file))
    return pairs, violations


def _json_strings(value: Any, location: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                yield f"{location}.<key>", key
            yield from _json_strings(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _json_strings(child, f"{location}[{index}]")


def _is_output_digest(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"sha256", "byte_length"}:
        return False
    sha256 = value["sha256"]
    byte_length = value["byte_length"]
    return (
        isinstance(sha256, str)
        and DIGEST.fullmatch(sha256) is not None
        and isinstance(byte_length, int)
        and not isinstance(byte_length, bool)
        and byte_length >= 0
    )


def _raw_output_locations(value: Any, location: str = "$") -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in RAW_OUTPUT_FIELDS and not _is_output_digest(child):
                yield child_location
            yield from _raw_output_locations(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _raw_output_locations(child, f"{location}[{index}]")


def _is_event_log(relative: PurePosixPath) -> bool:
    name = relative.name.casefold()
    return name in {"events.json", "events.jsonl"} or any(
        name.endswith(suffix) for suffix in ("-events.json", "-events.jsonl")
    )


def _durable_output_violations(
    repository: Path,
    tracked: set[PurePosixPath],
) -> list[str]:
    violations: list[str] = []
    for relative in sorted(tracked):
        path = _worktree_file(repository, relative)
        if path is None:
            continue
        if _is_event_log(relative):
            try:
                text = path.read_text(encoding="utf-8")
                if relative.suffix.casefold() == ".json":
                    documents = [(None, json.loads(text))]
                else:
                    documents = [
                        (line_number, json.loads(line))
                        for line_number, line in enumerate(text.splitlines(), start=1)
                        if line.strip()
                    ]
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                violations.append(
                    f"cannot inspect durable event log {relative}: {error}"
                )
                continue
            for line_number, document in documents:
                for location in _raw_output_locations(document):
                    line = f":{line_number}" if line_number is not None else ""
                    violations.append(
                        "durable event output must be a digest object: "
                        f"{relative}{line} {location}"
                    )
        if (
            relative.name.casefold() == "stderr.log"
            or relative.name.casefold().endswith("-stderr.log")
        ):
            try:
                stderr_digest = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                violations.append(
                    f"durable stderr must be a digest object: {relative} ({error})"
                )
                continue
            if not _is_output_digest(stderr_digest):
                violations.append(f"durable stderr must be a digest object: {relative}")
    return violations


def _embedded_body_violations(
    repository: Path,
    tracked: set[PurePosixPath],
    bodies: dict[str, bytes],
) -> list[str]:
    violations: list[str] = []
    decoded: dict[str, str] = {}
    for digest, body in bodies.items():
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            violations.append(f"README body {digest} is not valid UTF-8")
            continue
        if text:
            decoded[digest] = text

    for relative in sorted(tracked):
        if relative.suffix.casefold() not in {".json", ".jsonl"}:
            continue
        path = _worktree_file(repository, relative)
        if path is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            if relative.suffix.casefold() == ".json":
                documents = [(None, json.loads(text))]
            else:
                documents = [
                    (line_number, json.loads(line))
                    for line_number, line in enumerate(text.splitlines(), start=1)
                    if line.strip()
                ]
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            violations.append(f"cannot inspect JSON strings in {relative}: {error}")
            continue
        for line_number, document in documents:
            for location, value in _json_strings(document):
                for digest, body in decoded.items():
                    if body in value:
                        line = f":{line_number}" if line_number is not None else ""
                        violations.append(
                            "complete README body embedded in JSON string: "
                            f"{relative}{line} {location} ({digest})"
                        )
    return violations


def audit_repository(repository: Path) -> list[str]:
    """Return single-body invariant violations for one Git working tree."""

    repository = _git_root(repository.resolve())
    tracked = _tracked_paths(repository)
    record_bodies, violations = _record_body_paths(repository, tracked)
    named_bodies = {path for path in tracked if README_NAME.fullmatch(path.name)}
    body_paths = named_bodies | record_bodies

    hashes: dict[str, list[PurePosixPath]] = defaultdict(list)
    file_bytes: dict[PurePosixPath, bytes] = {}
    for relative in sorted(tracked):
        path = _worktree_file(repository, relative)
        if path is None:
            continue
        content = path.read_bytes()
        file_bytes[relative] = content
        hashes[hashlib.sha256(content).hexdigest()].append(relative)

    generated_pairs, generated_violations = _generated_pairs(repository, tracked)
    violations.extend(generated_violations)
    generated_destinations = {
        destination: source for source, destination in generated_pairs
    }
    body_digests = {
        _sha256(path): relative
        for relative in body_paths
        if (path := _worktree_file(repository, relative)) is not None
    }
    for digest in sorted(body_digests):
        matching = set(hashes[digest])
        generated = {
            path
            for path in matching
            if path in generated_destinations
            and generated_destinations[path] in matching
        }
        owners = matching - generated
        if len(owners) != 1:
            rendered = ", ".join(str(path) for path in sorted(matching))
            violations.append(
                f"README body {digest} has {len(owners)} durable owners: {rendered}"
            )

    unique_bodies = {
        digest: file_bytes[relative]
        for digest, relative in body_digests.items()
        if relative in file_bytes
    }
    violations.extend(_embedded_body_violations(repository, tracked, unique_bodies))
    violations.extend(_durable_output_violations(repository, tracked))
    return sorted(set(violations))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject duplicate or JSON-embedded durable README bodies."
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path.cwd(),
        help="path inside the Git repository to inspect (default: current directory)",
    )
    args = parser.parse_args(argv)
    violations = audit_repository(args.repository)
    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1
    print("Single durable README body invariant holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
