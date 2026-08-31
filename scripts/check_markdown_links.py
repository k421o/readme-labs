"""Check repository-local links in Markdown files."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "dist", "build", ".pytest_cache", ".ruff_cache"}
HISTORICAL_FIXTURE_ROOT = REPOSITORY_ROOT / "research" / "readme-contract-exercises"
NON_AUTHORITATIVE_ARTIFACT_ROOTS = (
    REPOSITORY_ROOT / "intake" / "snapshots",
    REPOSITORY_ROOT / "candidates",
    REPOSITORY_ROOT / "readmes" / "records",
)


def is_non_authoritative_artifact(path: Path) -> bool:
    if path.is_relative_to(NON_AUTHORITATIVE_ARTIFACT_ROOTS[0]):
        return True
    if path.is_relative_to(NON_AUTHORITATIVE_ARTIFACT_ROOTS[1]):
        relative = path.relative_to(NON_AUTHORITATIVE_ARTIFACT_ROOTS[1])
        return "artifact" in relative.parts
    if path.is_relative_to(NON_AUTHORITATIVE_ARTIFACT_ROOTS[2]):
        return path.name == "artifact.md"
    return False


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.relative_to(REPOSITORY_ROOT).parts)
    )


def destinations(path: Path) -> list[str]:
    tokens = MarkdownIt("commonmark").parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for token in tokens:
        if token.type != "inline" or not token.children:
            continue
        for child in token.children:
            if child.type == "link_open":
                href = child.attrGet("href")
                if href:
                    found.append(href)
            if child.type == "image":
                source = child.attrGet("src")
                if source:
                    found.append(source)
    return found


def main() -> int:
    failures: list[str] = []
    for markdown in markdown_files():
        if markdown.is_relative_to(HISTORICAL_FIXTURE_ROOT) or (
            is_non_authoritative_artifact(markdown)
        ):
            continue
        for destination in destinations(markdown):
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (markdown.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                relative = markdown.relative_to(REPOSITORY_ROOT)
                failures.append(f"{relative}: missing local target {destination}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"Checked local links in {len(markdown_files())} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
