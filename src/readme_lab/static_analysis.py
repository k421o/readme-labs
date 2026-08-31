"""Load versioned static analyzers and their evidence-only run envelopes."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.artifacts import resolve_contained

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "experiments" / "schemas"
ANALYZER_SCHEMA = "static-analyzer-v1.schema.json"
RUN_SCHEMA = "static-analysis-run-v1.schema.json"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / name
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", name).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError(f"{name} must contain a JSON object")
    return schema


def load_static_analyzer(path: Path) -> dict[str, Any]:
    """Load one adapter without treating its native output as universal."""

    path = path.resolve()
    analyzer = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(_load_schema(ANALYZER_SCHEMA)).validate(analyzer)
    rule_ids = [rule["id"] for rule in analyzer["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("static analyzer rule ids must be unique")
    documentation = resolve_contained(path.parent, analyzer["documentation"])
    if not documentation.is_file():
        raise FileNotFoundError(documentation)
    return {
        **analyzer,
        "_spec_path": path,
        "_documentation_path": documentation,
    }


def load_static_analysis_run(path: Path) -> dict[str, Any]:
    """Load and validate one common static-analysis evidence envelope."""

    run = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(
        _load_schema(RUN_SCHEMA), format_checker=FormatChecker()
    ).validate(run)
    return run
