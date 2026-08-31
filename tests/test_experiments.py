from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from readme_lab.experiments import (
    load_experiment_plan,
    load_user_response_observation,
)


def test_initial_plan_makes_automated_results_evidence_only() -> None:
    plan = load_experiment_plan(
        Path("experiments/plans/reademe-temp-modular-readme-v1.json")
    )

    assert plan["completion_policy"] == {
        "mode": "complete_planned_run",
        "automated_results_authority": "evidence_only",
        "candidate_admission_gate": "none",
        "allowed_early_stops": ["safety", "authorization", "infrastructure"],
        "early_stop_disposition": "incomplete_not_rejected",
    }
    assert plan["decision"]["timing"] == "after_planned_trials_complete"


def test_static_diagnostic_plan_preserves_owner_decision_authority() -> None:
    plan = load_experiment_plan(
        Path("experiments/plans/reademe-temp-static-diagnostics-v1.json")
    )

    assert plan["planned_trials"][0]["kind"] == "static_analysis"
    assert plan["completion_policy"]["automated_results_authority"] == (
        "evidence_only"
    )
    assert plan["completion_policy"]["candidate_admission_gate"] == "none"
    assert plan["decision"]["authority"] == "owner_or_designated_review"


def test_plan_rejects_an_automated_hypothesis_veto(tmp_path: Path) -> None:
    source = Path(
        "experiments/plans/reademe-temp-modular-readme-v1.json"
    )
    plan = json.loads(source.read_text(encoding="utf-8"))
    plan["completion_policy"]["automated_results_authority"] = "reject"
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_experiment_plan(path)


def test_user_response_payload_can_evolve_with_its_method(tmp_path: Path) -> None:
    observation = {
        "schema_version": 1,
        "study_id": "navigation-interview-v2",
        "artifact_id": "candidate-a",
        "observed_at": "2026-08-30T00:00:00Z",
        "method": {
            "id": "think-aloud-navigation",
            "version": "2",
            "new_method_property": {"allowed": True},
        },
        "participant_scope": {
            "kind": "cohort",
            "count": 3,
            "experience_bands": ["new", "maintainer"],
        },
        "privacy": {
            "classification": "pseudonymous",
            "direct_identifiers_committed": False,
            "consent_basis": "recorded externally",
            "protected_raw_data_reference": "vault:study-2",
        },
        "payload": {
            "path_choices": ["install", "contribute"],
            "unexpected_future_measure": {"seconds_to_first_action": [12, 19, 8]},
        },
        "limitations": ["Small purposive sample."],
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")

    loaded = load_user_response_observation(path)

    assert loaded["payload"]["unexpected_future_measure"] == {
        "seconds_to_first_action": [12, 19, 8]
    }
