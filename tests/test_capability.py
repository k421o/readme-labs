from __future__ import annotations

from pathlib import Path

import yaml

REVIEW_SKILL_DIR = Path("capabilities/readme-review")
GENERATION_SKILL_DIR = Path("capabilities/readme-generate")


def test_readme_review_capability_has_no_scaffold_placeholders() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in skill
    assert "Establish its role before" in skill
    assert "Do not demand empty conventional sections" in skill
    assert "Do not use stars" in skill
    assert "unless the requested scope includes migrating" in skill
    assert "current task's tool record contains that execution" in skill
    assert "Use readme-generate to create or explicitly replace" in skill


def test_readme_review_references_are_local_and_present() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "roles-and-anatomy.md",
        "evidence-and-verification.md",
        "review-criteria.md",
    ):
        assert f"references/{name}" in skill
        assert (REVIEW_SKILL_DIR / "references" / name).is_file()


def test_readme_review_interface_freezes_finding_and_no_finding_job() -> None:
    interface = (REVIEW_SKILL_DIR / "INTERFACE.md").read_text(encoding="utf-8")

    assert "Named user job" in interface
    assert "material findings" in interface
    assert "no-material-findings" in interface
    assert "does not promise" in interface


def test_review_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (REVIEW_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-review" in metadata["interface"]["default_prompt"]


def test_readme_generation_routes_authoring_without_overlapping_review() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "name: readme-generate" in skill
    assert "create, draft, bootstrap, or explicitly replace" in skill
    assert "Do not use for an audit, critique, or focused improvement" in skill
    assert "does not by itself authorize replacing" in skill
    assert "explicitly asks for a rewrite" in skill
    assert "replacement, or overwrite" in skill
    assert "preserve correct component-specific content" in skill
    assert "TODO" not in skill


def test_readme_generation_consumes_the_complete_review_source() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(skill.split())

    assert "../readme-review/SKILL.md" in skill
    assert "../readme-review/references/" in skill
    assert "read every local reference" in skill
    assert "single source" in skill
    assert "Apply the complete sibling `readme-review` workflow" in skill
    assert "exact written draft" in normalized
    assert (
        "run the complete review workflow again against the revised bytes"
        in normalized
    )
    assert (
        "latest complete pass reaches a no-material-findings conclusion" in normalized
    )
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


def test_readme_generation_interface_freezes_iteration_and_capture_boundaries() -> None:
    interface = (GENERATION_SKILL_DIR / "INTERFACE.md").read_text(encoding="utf-8")

    assert "Named user job" in interface
    assert "no material findings or an explicit residual limit" in interface
    assert "Explicit rewrite, replacement, or overwrite scope" in interface
    assert "all of its local" in interface
    assert "artifact capture during the authoring loop" in interface
    assert "Capture and lineage remain a" in interface
    assert "separate owner-selected operation" in interface


def test_generation_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (GENERATION_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-generate" in metadata["interface"]["default_prompt"]
