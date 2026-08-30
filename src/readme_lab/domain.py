"""Load and validate versioned readme-labs domain contracts."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "domain"
TAXONOMY_PATH = DOMAIN_DIR / "taxonomy-v1.json"
OBSERVATION_SCHEMA_PATHS = {
    "1.0.0": DOMAIN_DIR / "readme-observation-v1.schema.json",
    "2.0.0": DOMAIN_DIR / "readme-observation-v2.schema.json",
}


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from a domain file."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return value


def _load_domain_file(name: str, source_path: Path) -> dict[str, Any]:
    if source_path.is_file():
        return load_json(source_path)
    packaged = resources.files("readme_lab").joinpath("data", name)
    value = json.loads(packaged.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in packaged domain file {name}")
    return value


def load_taxonomy(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical taxonomy or an explicitly supplied compatible file."""

    if path is not None:
        return load_json(path)
    return _load_domain_file("taxonomy-v1.json", TAXONOMY_PATH)


def validate_observation(observation: dict[str, Any]) -> None:
    """Raise a validation error when an observation violates its contract."""

    version = observation.get("schema_version")
    if version not in OBSERVATION_SCHEMA_PATHS:
        expected = ", ".join(sorted(OBSERVATION_SCHEMA_PATHS))
        raise ValueError(
            f"unknown READMEObservation schema version {version!r}; "
            f"expected one of: {expected}"
        )
    schema_name = f"readme-observation-v{version.split('.')[0]}.schema.json"
    schema = _load_domain_file(schema_name, OBSERVATION_SCHEMA_PATHS[version])
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(observation)
