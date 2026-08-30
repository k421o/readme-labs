"""Build the experimental Codex plugin from the canonical capability."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "capabilities" / "readme-review"
PLUGIN_ROOT = REPOSITORY_ROOT / "products" / "codex-plugin" / "readme-labs"
DESTINATION = PLUGIN_ROOT / "skills" / "readme-review"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"


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


def source_revision() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", SOURCE.relative_to(REPOSITORY_ROOT)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def expected_provenance() -> dict[str, str]:
    return {
        "artifact_kind": "codex_plugin_adapter",
        "maturity": "experimental",
        "source": "capabilities/readme-review",
        "source_revision": source_revision(),
        "source_sha256": tree_hash(SOURCE),
        "generated_by": "scripts/build_plugin.py",
    }


def file_map(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def check() -> int:
    failures: list[str] = []
    if not DESTINATION.is_dir():
        failures.append(f"missing generated capability: {DESTINATION}")
    elif file_map(SOURCE) != file_map(DESTINATION):
        failures.append("generated capability differs from canonical source")

    if not PROVENANCE.is_file():
        failures.append(f"missing provenance record: {PROVENANCE}")
    else:
        actual = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        if actual != expected_provenance():
            failures.append("UPSTREAM.json does not match canonical source")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Experimental plugin adapter is synchronized.")
    return 0


def build() -> None:
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, DESTINATION)
    serialized = json.dumps(expected_provenance(), indent=2, sort_keys=True) + "\n"
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
