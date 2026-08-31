from __future__ import annotations

import json
import subprocess
from pathlib import Path

from readme_lab.artifacts import tree_sha256
from readme_lab.candidates import materialize_candidate, verify_candidate


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_imported_modular_readme_candidate_is_reproducible(tmp_path: Path) -> None:
    descriptor = Path(
        "candidates/reademe-temp-modular-readme-v1/candidate.json"
    )
    verification = verify_candidate(descriptor)

    assert verification["verified"] is True
    assert verification["entrypoints"] == [
        {
            "id": "modular-readme",
            "path": ".agents/skills/modular-readme",
            "exists": True,
        }
    ]

    destination = tmp_path / "candidate"
    materialization = materialize_candidate(descriptor, destination)
    assert materialization["tree_sha256"] == verification["tree_sha256"]
    assert (destination / ".agents/skills/modular-readme/SKILL.md").is_file()


def test_candidate_shape_is_not_constrained_to_current_skill_layout(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "--quiet", "--initial-branch=main")
    artifact = repository / "candidates/alternate/artifact"
    artifact.mkdir(parents=True)
    (artifact / "novel.prompt").write_text(
        "A deliberately different experimental form.\n", encoding="utf-8"
    )
    manifest_path = repository / "intake/manifests/source.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "alternate-source",
                "title": "Alternate source",
                "observed_at": "2026-08-30T00:00:00Z",
                "source_repository": {
                    "repository_id": "external:test",
                    "availability": "external",
                },
                "items": [
                    {
                        "id": "novel-shape",
                        "kind": "skill",
                        "source": {
                            "state": "external",
                            "locator": "https://example.invalid/novel",
                            "sha256": None,
                        },
                        "intake_mode": "reference",
                        "status": "admitted",
                        "authority": "evidence_only",
                        "limitations": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    descriptor = repository / "candidates/alternate/candidate.json"
    descriptor.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "alternate-shape",
                "title": "Alternate shape",
                "kind": "other",
                "authority": "experimental_candidate_only",
                "storage": {
                    "mode": "embedded",
                    "artifact_root": "artifact",
                    "tree_sha256": tree_sha256(artifact),
                },
                "source_bindings": [
                    {
                        "manifest": "intake/manifests/source.json",
                        "item_ids": ["novel-shape"],
                    }
                ],
                "entrypoints": [
                    {
                        "id": "novel",
                        "path": "novel.prompt",
                        "format": "experimental-promptware",
                    }
                ],
                "hypotheses": ["The alternate form may be useful."],
                "limitations": [],
            }
        ),
        encoding="utf-8",
    )
    git(repository, "config", "user.name", "readme-labs")
    git(repository, "config", "user.email", "eval@readme-labs.invalid")
    git(repository, "add", ".")
    git(repository, "commit", "--quiet", "-m", "fixture")

    result = verify_candidate(descriptor)

    assert result["verified"] is True
    assert result["entrypoints"][0]["path"] == "novel.prompt"
