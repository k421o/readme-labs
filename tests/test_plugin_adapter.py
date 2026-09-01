from __future__ import annotations

import json
import re
import runpy
from pathlib import Path

CAPABILITY_NAMES = ("readme-review", "readme-generate")
CAPABILITIES_ROOT = Path("capabilities")
PLUGIN_ROOT = Path("products/codex-plugin/readme-labs")
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"
MARKETPLACE = Path(".agents/plugins/marketplace.json")
SYNC_GENERATED_SKILLS = runpy.run_path("scripts/build_plugin.py")[
    "sync_generated_skills"
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


def test_plugin_adapter_is_experimental_and_pins_every_ordered_source() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert manifest["version"] == "0.3.0-dev.1"
    assert re.fullmatch(r"\d+\.\d+\.\d+-(?:dev|rc)\.\d+", manifest["version"])
    assert "Experimental" in manifest["interface"]["displayName"]
    assert provenance["maturity"] == "experimental"
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
