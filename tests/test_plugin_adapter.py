from __future__ import annotations

import json
import re
import runpy
import subprocess
from pathlib import Path

import pytest

CAPABILITY_NAMES = ("readme-review", "readme-generate", "readme-prune")
CAPABILITIES_ROOT = Path("capabilities")
PLUGIN_ROOT = Path("products/codex-plugin/readme-labs")
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"
MARKETPLACE = Path(".agents/plugins/marketplace.json")
SYNC_GENERATED_SKILLS = runpy.run_path("scripts/build_plugin.py")[
    "sync_generated_skills"
]
ASSERT_SOURCE_MATCHES_REVISION = runpy.run_path("scripts/build_plugin.py")[
    "_assert_source_matches_revision"
]


def file_map(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_plugin_adapter_contains_exact_generated_capabilities() -> None:
    assert {path.name for path in SKILLS_ROOT.iterdir()} == set(CAPABILITY_NAMES)
    for name in CAPABILITY_NAMES:
        assert file_map(CAPABILITIES_ROOT / name) == file_map(SKILLS_ROOT / name)


def test_skill_sync_replaces_stale_and_partial_generated_directories(
    tmp_path: Path,
) -> None:
    sources_root = tmp_path / "sources"
    sources = []
    for name in CAPABILITY_NAMES:
        source = sources_root / name
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        sources.append((name, source))

    generated = tmp_path / "plugin" / "skills"
    (generated / "readme-review").mkdir(parents=True)
    (generated / "readme-review" / "stale.txt").write_text(
        "stale\n", encoding="utf-8"
    )
    (generated / "removed-capability").mkdir()

    SYNC_GENERATED_SKILLS(tuple(sources), generated)

    assert {path.name for path in generated.iterdir()} == set(CAPABILITY_NAMES)
    assert not (generated / "readme-review" / "stale.txt").exists()
    for name, source in sources:
        assert file_map(source) == file_map(generated / name)


@pytest.mark.parametrize("change_kind", ["tracked", "untracked"])
def test_source_revision_rejects_uncommitted_capability_bytes(
    tmp_path: Path, change_kind: str
) -> None:
    repository = tmp_path / "repository"
    source = repository / "capabilities/readme-review"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("committed\n", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "readme-labs"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "eval@readme-labs.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "fixture"],
        cwd=repository,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if change_kind == "tracked":
        (source / "SKILL.md").write_text("modified\n", encoding="utf-8")
    else:
        (source / "new-reference.md").write_text("untracked\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="not present in its source revision"):
        ASSERT_SOURCE_MATCHES_REVISION(repository, source, revision)


def test_plugin_adapter_is_experimental_and_pins_every_ordered_source() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert manifest["version"] == "0.3.0-dev.2"
    assert re.fullmatch(r"\d+\.\d+\.\d+-(?:dev|rc)\.\d+", manifest["version"])
    assert "Experimental" in manifest["interface"]["displayName"]
    assert manifest["interface"]["defaultPrompt"] == [
        "Use $readme-labs:readme-review to review an existing README.",
        (
            "Use $readme-labs:readme-generate to create a README from repository "
            "evidence."
        ),
        "Use $readme-labs:readme-prune to remove content from an existing README.",
    ]
    assert provenance["maturity"] == "experimental"
    assert provenance["product_version"] == manifest["version"]
    assert [item["source"] for item in provenance["sources"]] == [
        f"capabilities/{name}" for name in CAPABILITY_NAMES
    ]
    assert [item["destination"] for item in provenance["sources"]] == [
        f"skills/{name}" for name in CAPABILITY_NAMES
    ]
    for item in provenance["sources"]:
        assert re.fullmatch(r"[0-9a-f]{40}", item["source_revision"])
        assert re.fullmatch(r"[0-9a-f]{64}", item["source_sha256"])


def test_repository_registers_its_own_mechanical_marketplace_adapter() -> None:
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))

    assert marketplace["name"] == "readme-labs"
    assert marketplace["plugins"] == [
        {
            "name": "readme-labs",
            "source": {
                "source": "local",
                "path": "./products/codex-plugin/readme-labs",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
    ]
    assert "agent-skills" not in MARKETPLACE.read_text(encoding="utf-8").casefold()
