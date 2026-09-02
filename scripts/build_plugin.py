"""Build the experimental Codex plugin from canonical capabilities."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "products" / "codex-plugin" / "readme-labs"
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

# This ordered allowlist is the product's complete generated skill surface.
# Adding a capability is an explicit product decision rather than directory
# discovery, and the same order is preserved in UPSTREAM.json.
CAPABILITY_SOURCES = (
    ("readme-review", REPOSITORY_ROOT / "capabilities" / "readme-review"),
    ("readme-generate", REPOSITORY_ROOT / "capabilities" / "readme-generate"),
    ("readme-prune", REPOSITORY_ROOT / "capabilities" / "readme-prune"),
)


def tree_hash(root: Path) -> str:
    """Hash relative paths and contents for every file in a directory tree."""

    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_capability_sources(
    capability_sources: tuple[tuple[str, Path], ...],
) -> None:
    names = [name for name, _ in capability_sources]
    if not names or len(names) != len(set(names)):
        raise ValueError("capability allowlist names must be non-empty and unique")
    for name, source in capability_sources:
        if source.name != name:
            raise ValueError(f"capability name and source directory differ: {name}")
        if source.is_symlink() or not source.is_dir():
            raise FileNotFoundError(f"canonical capability is missing: {source}")


def source_revision(source: Path) -> str:
    relative = source.relative_to(REPOSITORY_ROOT)
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    revision = result.stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise RuntimeError(
            f"canonical capability needs a committed source revision: {relative}"
        )
    _assert_source_matches_revision(REPOSITORY_ROOT, source, revision)
    return revision


def _committed_file_map(
    repository_root: Path, source: Path, revision: str
) -> dict[str, bytes]:
    source_relative = source.relative_to(repository_root)
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", revision, "--", source_relative],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    committed: dict[str, bytes] = {}
    for entry in (item for item in result.stdout.split(b"\0") if item):
        metadata, raw_path = entry.split(b"\t", 1)
        object_type, object_id = metadata.split()[1:]
        if object_type != b"blob":
            raise RuntimeError("capability source contains a non-blob Git object")
        path = Path(os.fsdecode(raw_path))
        relative = path.relative_to(source_relative).as_posix()
        committed[relative] = subprocess.run(
            ["git", "cat-file", "blob", object_id.decode()],
            cwd=repository_root,
            check=True,
            capture_output=True,
        ).stdout
    return committed


def _assert_source_matches_revision(
    repository_root: Path, source: Path, revision: str
) -> None:
    if file_map(source) != _committed_file_map(repository_root, source, revision):
        relative = source.relative_to(repository_root)
        raise RuntimeError(
            "canonical capability has changes not present in its source revision: "
            f"{relative}"
        )


def expected_provenance() -> dict[str, object]:
    _validate_capability_sources(CAPABILITY_SOURCES)
    manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    product_version = manifest.get("version")
    if not isinstance(product_version, str) or not product_version:
        raise ValueError("plugin manifest requires a product version")
    sources = []
    for name, source in CAPABILITY_SOURCES:
        sources.append(
            {
                "destination": f"skills/{name}",
                "source": source.relative_to(REPOSITORY_ROOT).as_posix(),
                "source_revision": source_revision(source),
                "source_sha256": tree_hash(source),
            }
        )
    return {
        "artifact_kind": "codex_plugin_adapter",
        "maturity": "experimental",
        "product_version": product_version,
        "sources": sources,
        "generated_by": "scripts/build_plugin.py",
    }


def file_map(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _skill_entries(skills_root: Path) -> set[str]:
    if not skills_root.is_dir() or skills_root.is_symlink():
        return set()
    return {path.name for path in skills_root.iterdir()}


def sync_generated_skills(
    capability_sources: tuple[tuple[str, Path], ...],
    skills_root: Path,
) -> None:
    """Replace the generated skill surface with exactly the allowlisted sources."""

    _validate_capability_sources(capability_sources)
    if skills_root.is_symlink():
        raise ValueError(f"refusing to replace a symlinked skills root: {skills_root}")
    if skills_root.exists():
        if not skills_root.is_dir():
            raise ValueError(f"generated skills root is not a directory: {skills_root}")
        shutil.rmtree(skills_root)
    skills_root.mkdir(parents=True)
    for name, source in capability_sources:
        shutil.copytree(source, skills_root / name)


def check() -> int:
    failures: list[str] = []
    expected_names = {name for name, _ in CAPABILITY_SOURCES}
    actual_names = _skill_entries(SKILLS_ROOT)
    if actual_names != expected_names:
        failures.append(
            "generated skill set differs from explicit allowlist: "
            f"expected {sorted(expected_names)}, found {sorted(actual_names)}"
        )

    for name, source in CAPABILITY_SOURCES:
        destination = SKILLS_ROOT / name
        if not destination.is_dir() or destination.is_symlink():
            failures.append(f"missing generated capability: {destination}")
        elif file_map(source) != file_map(destination):
            failures.append(
                f"generated capability differs from canonical source: {name}"
            )

    if not PROVENANCE.is_file():
        failures.append(f"missing provenance record: {PROVENANCE}")
    else:
        actual = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        if actual != expected_provenance():
            failures.append("UPSTREAM.json does not match canonical sources")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Experimental plugin adapter is synchronized.")
    return 0


def build() -> None:
    # Compute and validate provenance before replacing any generated files.
    provenance = expected_provenance()
    sync_generated_skills(CAPABILITY_SOURCES, SKILLS_ROOT)
    serialized = json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    PROVENANCE.write_text(serialized, encoding="utf-8")
    print(f"Built experimental plugin adapter at {PLUGIN_ROOT}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
