from __future__ import annotations

from pathlib import Path

import yaml

SKILL_DIR = Path("capabilities/readme-review")


def test_readme_review_capability_has_no_scaffold_placeholders() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in skill
    assert "Establish its role before" in skill
    assert "Do not demand empty conventional sections" in skill
    assert "Do not use stars" in skill


def test_readme_review_references_are_local_and_present() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "roles-and-anatomy.md",
        "evidence-and-verification.md",
        "review-criteria.md",
    ):
        assert f"references/{name}" in skill
        assert (SKILL_DIR / "references" / name).is_file()


def test_openai_interface_invokes_canonical_skill_name() -> None:
    metadata = yaml.safe_load(
        (SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    assert "$readme-review" in metadata["interface"]["default_prompt"]
