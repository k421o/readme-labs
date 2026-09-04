from __future__ import annotations

from pathlib import Path

import yaml

REVIEW_SKILL_DIR = Path("capabilities/readme-review")
GENERATION_SKILL_DIR = Path("capabilities/readme-generate")
PRUNE_SKILL_DIR = Path("capabilities/readme-prune")

# Prose snapshots below pin the current reviewed wording of each SKILL.md
# deliberately. They are not behavior contracts: a copyedit must update them
# in the same change. Structural and linkage checks stay in their own tests.


def test_readme_review_skill_has_no_scaffold_placeholders() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in skill


def test_readme_review_skill_prose_snapshot() -> None:
    skill = (REVIEW_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "Establish its role before" in skill
    assert "Do not demand empty conventional sections" in skill
    assert "Do not use stars" in skill
    assert "unless the requested scope includes migrating" in skill
    assert "current task's tool record contains that execution" in skill
    assert "readme-generate to create or explicitly replace" in skill
    assert "Use readme-prune when the requested outcome is removal" in skill
    assert "route a primarily subtractive request through `readme-prune`" in skill
    assert "remove unsupported, stale, duplicative, or noisy content" in skill
    assert "relocate still-needed content only" in skill


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


def test_readme_generation_skill_has_no_scaffold_placeholders() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: readme-generate" in skill
    assert "TODO" not in skill


def test_readme_generation_skill_prose_snapshot() -> None:
    skill = (GENERATION_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(skill.split())

    assert "create, draft, bootstrap, or explicitly replace" in skill
    assert "Use readme-review for an audit or critique without edits" in skill
    assert "readme-prune to remove, trim, declutter, or shorten" in skill
    assert "Do not use for a focused edit" in skill
    assert "does not by itself authorize replacing" in skill
    assert "explicitly asks for a rewrite" in skill
    assert "replacement, or overwrite" in skill
    assert "preserve correct component-specific content" in skill
    assert "read every local reference" in skill
    assert "single source" in skill
    assert "Apply the complete sibling `readme-review` workflow" in skill
    assert "exact written draft" in normalized
    assert (
        "run the complete review workflow again against the revised bytes"
        in normalized
    )
    assert (
        "latest complete pass reaches a no-material-findings conclusion"
        in normalized
    )


def test_readme_generation_consumes_the_complete_review_source() -> None:
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


def test_readme_prune_skill_has_no_scaffold_placeholders() -> None:
    skill = (PRUNE_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: readme-prune" in skill
    assert "TODO" not in skill


def test_readme_prune_skill_prose_snapshot() -> None:
    skill = (PRUNE_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "trim, declutter, shorten by subtraction, or remove" in skill
    assert "Use `readme-review` for findings without edits" in skill
    assert "Use `readme-generate` for a" in skill
    assert "missing README, an explicit replacement, or a broad rewrite" in skill
    assert "Do not delete or move the README" in skill
    assert "Make no new substantive claims, sections, commands, or links" in skill
    assert "read every local reference" in skill
    assert "single source" in skill
    assert "Apply the complete sibling `readme-review` workflow" in skill


def test_readme_prune_consumes_the_complete_review_source() -> None:
    skill = (PRUNE_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "../readme-review/SKILL.md" in skill
    assert "../readme-review/references/" in skill
    assert (PRUNE_SKILL_DIR.parent / "readme-review/SKILL.md").is_file()
    assert (PRUNE_SKILL_DIR.parent / "readme-review/references").is_dir()


def test_readme_prune_interface_freezes_safety_and_completion() -> None:
    interface = (PRUNE_SKILL_DIR / "INTERFACE.md").read_text(encoding="utf-8")

    assert "Named user job" in interface
    assert "`user_directed` removals from `review_evidenced`" in interface
    assert "Make no new substantive claims, sections, commands, or links" in interface
    assert "Restore an agent-selected deletion" in interface
    assert "Do not silently reverse an exact user-directed removal" in interface
    assert "no material regression attributable to agent-selected pruning" in interface
    assert "whole-file deletion or movement" in interface
    assert "artifact capture during pruning" in interface


def test_prune_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (PRUNE_SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-prune" in metadata["interface"]["default_prompt"]
