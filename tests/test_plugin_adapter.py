from __future__ import annotations

import json
from pathlib import Path

SOURCE = Path("capabilities/readme-review")
PLUGIN_ROOT = Path("products/codex-plugin/readme-labs")
DESTINATION = PLUGIN_ROOT / "skills/readme-review"
PROVENANCE = PLUGIN_ROOT / "UPSTREAM.json"


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

    assert "dev" in manifest["version"]
    assert "Experimental" in manifest["interface"]["displayName"]
    assert provenance["maturity"] == "experimental"
    assert len(provenance["source_revision"]) == 40
    assert len(provenance["source_sha256"]) == 64


def test_repository_does_not_register_a_marketplace_product() -> None:
    assert not Path("marketplace.json").exists()
    assert not (PLUGIN_ROOT / "marketplace.json").exists()
