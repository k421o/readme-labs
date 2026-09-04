from __future__ import annotations

from pathlib import Path

import yaml

REVIEW_SKILL_DIR = Path("capabilities/readme-review")
GENERATION_SKILL_DIR = Path("capabilities/readme-generate")
PRUNE_SKILL_DIR = Path("capabilities/readme-prune")


def test_readme_review_skill_has_no_scaffold_placeholders() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in skill


def test_readme_review_references_are_local_and_present() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "roles-and-anatomy.md",
        "evidence-and-verification.md",
        "review-criteria.md",
    ):
        assert f"references/{name}" in skill
        assert (REVIEW_SKILL_DIR / "references" / name).is_file()


def test_review_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (REVIEW_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-review" in metadata["interface"]["default_prompt"]


def test_readme_generation_skill_has_no_scaffold_placeholders() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: readme-generate" in skill
    assert "TODO" not in skill


def test_readme_generation_keeps_its_review_source_available() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "../readme-review/SKILL.md" in skill
    assert "../readme-review/references/" in skill
    assert (GENERATION_SKILL_DIR.parent / "readme-review/SKILL.md").is_file()
    assert (GENERATION_SKILL_DIR.parent / "readme-review/references").is_dir()


def test_packaged_generation_keeps_its_review_dependency_as_a_sibling() -> None:
    packaged_skills = Path("products/codex-plugin/readme-labs/skills")
    generation = packaged_skills / "readme-generate"
    review = generation.parent / "readme-review"

    assert (generation / "SKILL.md").is_file()
    assert (review / "SKILL.md").is_file()
    assert (review / "references/roles-and-anatomy.md").is_file()
    assert (review / "references/evidence-and-verification.md").is_file()
    assert (review / "references/review-criteria.md").is_file()


def test_generation_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (GENERATION_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-generate" in metadata["interface"]["default_prompt"]


def test_readme_prune_skill_has_no_scaffold_placeholders() -> None:
    skill = (PRUNE_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: readme-prune" in skill
    assert "TODO" not in skill


def test_readme_prune_keeps_its_review_source_available() -> None:
    skill = (PRUNE_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "../readme-review/SKILL.md" in skill
    assert "../readme-review/references/" in skill
    assert (PRUNE_SKILL_DIR.parent / "readme-review/SKILL.md").is_file()
    assert (PRUNE_SKILL_DIR.parent / "readme-review/references").is_dir()


def test_prune_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (PRUNE_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-prune" in metadata["interface"]["default_prompt"]
