#!/usr/bin/env python3
"""Validate path-independent README Labs release structure."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NAME = "readme-labs"
EXPECTED_VERSION = "0.1.0"
SKILL_PATH = ROOT / "skills/readme-contract-review/SKILL.md"
HISTORICAL_FIXTURE_ROOT = ROOT / "research/readme-contract-exercises"


def load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifests() -> None:
    manifests = [
        load_manifest(ROOT / ".codex-plugin/plugin.json"),
        load_manifest(ROOT / ".claude-plugin/plugin.json"),
    ]
    for manifest in manifests:
        assert manifest["name"] == EXPECTED_NAME
        assert manifest["version"] == EXPECTED_VERSION
        assert manifest["repository"] == "https://github.com/k421o/readme-labs"


def validate_skill() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert re.search(r"^name: readme-contract-review$", text, re.MULTILINE)
    assert (SKILL_PATH.parent / "references/readme-review.md").is_file()
    assert (SKILL_PATH.parent / "agents/openai.yaml").is_file()


def markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.md") if ".git" not in path.parts)


def validate_markdown_links() -> None:
    for source in markdown_files():
        # Blind reconstruction exercises preserve the source repository's
        # links as evaluated data; their targets are intentionally not copied.
        if source.is_relative_to(HISTORICAL_FIXTURE_ROOT):
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
            target = raw_target.strip().split(" ", 1)[0].strip("<>")
            if not target or target.startswith(("#", "https://", "http://", "mailto:")):
                continue
            path_part = unquote(target.split("#", 1)[0])
            resolved = (source.parent / path_part).resolve()
            assert resolved.is_relative_to(ROOT), f"{source}: path escapes repository: {target}"
            assert resolved.exists(), f"{source}: missing local target: {target}"


def validate_path_independence() -> None:
    forbidden = ("/Users/", "~/dev/")
    for source in markdown_files():
        text = source.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"{source}: active checkout-specific path: {marker}"


def main() -> None:
    validate_manifests()
    validate_skill()
    validate_markdown_links()
    validate_path_independence()
    print("README Labs deterministic validation passed")


if __name__ == "__main__":
    main()
