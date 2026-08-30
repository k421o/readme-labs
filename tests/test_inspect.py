from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from readme_lab.inspect import inspect_readme

FIXTURE = Path("tests/fixtures/readme-with-conventional-sections.md")


def test_inspect_readme_emits_valid_deterministic_structure() -> None:
    observation = inspect_readme(
        FIXTURE,
        repository="example/project",
        revision="0123456789abcdef",
        role="repository_root",
        observed_at=datetime(2026, 8, 29, 12, tzinfo=UTC),
    )

    assert observation["schema_version"] == "1.0.0"
    assert observation["source"]["path"] == FIXTURE.as_posix()
    assert observation["role"] == {
        "primary": "repository_root",
        "secondary": [],
        "assignment": "declared",
    }
    assert observation["structure"] == {
        "line_count": 23,
        "word_count": 32,
        "heading_count": 5,
        "link_count": 1,
        "code_block_count": 1,
        "headings": [
            {"level": 1, "text": "Example project", "line": 1},
            {"level": 2, "text": "Getting started", "line": 5},
            {"level": 2, "text": "Usage", "line": 13},
            {"level": 2, "text": "Compatibility", "line": 17},
            {"level": 2, "text": "License", "line": 21},
        ],
    }
    assert {signal["category_id"] for signal in observation["category_signals"]} == {
        "boundaries",
        "first_successful_path",
        "identity",
        "legal_provenance",
        "minimal_use",
        "status_metadata",
    }


def test_nested_readme_role_remains_unspecified_without_context(tmp_path: Path) -> None:
    nested = tmp_path / "packages" / "thing" / "README.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("# Thing\n", encoding="utf-8")

    observation = inspect_readme(
        nested,
        repository="example/project",
        revision="main",
        observed_at=datetime(2026, 8, 29, 12, tzinfo=UTC),
    )

    assert observation["role"]["primary"] == "unspecified"
    assert "could not be inferred" in observation["limitations"][0]
