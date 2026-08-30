from __future__ import annotations

import json
import re
from pathlib import Path

SOURCE = Path("capabilities/readme-review")
PLUGIN_ROOT = Path("products/codex-plugin/readme-labs")
DESTINATION = PLUGIN_ROOT / "skills/readme-review"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"
MARKETPLACE = Path(".agents/plugins/marketplace.json")


def file_map(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_plugin_adapter_contains_exact_generated_capability() -> None:
    assert file_map(SOURCE) == file_map(DESTINATION)


def test_plugin_adapter_is_explicitly_experimental_and_pinned() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert re.fullmatch(r"\d+\.\d+\.\d+(?:-rc\.\d+)?", manifest["version"])
    assert "Experimental" in manifest["interface"]["displayName"]
    assert provenance["maturity"] == "experimental"
    assert len(provenance["source_revision"]) == 40
    assert len(provenance["source_sha256"]) == 64


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
