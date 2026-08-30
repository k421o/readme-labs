"""Validate open-ended experiment plans and user-response envelopes."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "experiments" / "schemas"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / name
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = resources.files("readme_lab").joinpath("data", name).read_text()
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError(f"{name} must be a JSON object")
    return schema


def load_experiment_plan(path: Path) -> dict[str, Any]:
    """Load a plan whose automated measurements remain evidence only."""

    plan = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(_load_schema("experiment-plan-v1.schema.json")).validate(
        plan
    )
    trial_ids = [trial["id"] for trial in plan["planned_trials"]]
    if len(trial_ids) != len(set(trial_ids)):
        raise ValueError("experiment trial ids must be unique")
    return plan


def load_user_response_observation(path: Path) -> dict[str, Any]:
    """Load a privacy-bounded, method-defined user-response observation."""

    observation = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(
        _load_schema("user-response-observation-v1.schema.json"),
        format_checker=FormatChecker(),
    ).validate(observation)
    return observation
