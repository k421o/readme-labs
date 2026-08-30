from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from readme_lab.capsule import load_capsule
from readme_lab.evaluation import (
    RESPONSE_SCHEMA_PATH,
    SCORECARD_SCHEMA_PATH,
    _artifact_binding,
    build_executor_permission_profile,
    build_executor_prompt,
    load_scorecard,
    score_review_response,
)

FINDING_CAPSULE = Path("evals/scenarios/missing-first-path/capsule.toml")
NO_FINDING_CAPSULE = Path("evals/scenarios/adequate-first-path/capsule.toml")


def _write_response(path: Path, *, finding: bool) -> None:
    findings = []
    if finding:
        findings.append(
            {
                "title": "Consumer path is missing",
                "category": "first_successful_path",
                "severity": "material",
                "path": "README.md",
                "line_start": 1,
                "line_end": 9,
                "problem": "Only contributor setup is documented.",
                "evidence": ["pyproject.toml declares the pebble-count script."],
                "impact": "A user cannot reach the first supported result.",
                "correction": "Restore a consumer install-and-run example.",
            }
        )
    value = {
        "schema_version": "1.0.0",
        "conclusion": "material_findings" if finding else "no_material_findings",
        "findings": findings,
        "commands": [],
        "verification": ["Inspected README.md and pyproject.toml."],
        "limitations": ["Did not build a wheel."],
    }
    path.write_text(json.dumps(value), encoding="utf-8")


def test_evaluation_json_schemas_and_scorecards_are_valid() -> None:
    for path in (RESPONSE_SCHEMA_PATH, SCORECARD_SCHEMA_PATH):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    assert load_scorecard(FINDING_CAPSULE)["expected_conclusion"] == (
        "material_findings"
    )
    assert load_scorecard(NO_FINDING_CAPSULE)["expected_conclusion"] == (
        "no_material_findings"
    )


def test_executor_prompt_withholds_scenario_and_scorecard_names() -> None:
    capsule = load_capsule(FINDING_CAPSULE)
    prompt = build_executor_prompt(capsule)

    assert capsule["task"] in prompt
    assert capsule["id"] not in prompt
    assert capsule["scorecard"] not in prompt
    assert "readme-review" not in prompt


def test_permission_profile_denies_factory_without_leaking_scenario_name() -> None:
    profile = build_executor_permission_profile(Path("/tmp/factory-checkout"))

    assert 'extends = ":workspace"' in profile
    assert '= "deny"' in profile
    assert "enabled = false" in profile
    assert Path("/tmp/factory-checkout").resolve().as_posix() in profile
    assert "missing-first-path" not in profile


def test_artifact_binding_verifies_marketplace_and_installed_bytes(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    marketplace = codex_home / ".tmp" / "marketplaces" / "readme-labs"
    product = marketplace / "products" / "readme-labs"
    installed = (
        codex_home
        / "plugins"
        / "cache"
        / "readme-labs"
        / "readme-labs"
        / "0.2.0-rc.1"
    )
    product.mkdir(parents=True)
    (product / "plugin.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "readme-labs"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "eval@readme-labs.invalid"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=marketplace, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "fixture"],
        cwd=marketplace,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=marketplace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    codex_home.joinpath("config.toml").write_text(
        "[marketplaces.readme-labs]\n"
        'source_type = "git"\n'
        f'ref = "{revision}"\n',
        encoding="utf-8",
    )
    (marketplace / ".codex-marketplace-install.json").write_text(
        json.dumps(
            {
                "source_type": "git",
                "ref_name": revision,
                "revision": revision,
            }
        ),
        encoding="utf-8",
    )
    shutil.copytree(product, installed)
    plugin = {
        "marketplaceName": "readme-labs",
        "name": "readme-labs",
        "version": "0.2.0-rc.1",
        "source": {"path": product.as_posix()},
    }

    binding = _artifact_binding(codex_home, plugin, revision)

    assert binding["artifact_revision_verified"] is True
    assert binding["marketplace_revision"] == revision
    assert binding["marketplace_product_sha256"] == (
        binding["installed_product_sha256"]
    )


def test_artifact_binding_rejects_configured_revision_mismatch(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    marketplace = codex_home / ".tmp" / "marketplaces" / "readme-labs"
    marketplace.mkdir(parents=True)
    codex_home.joinpath("config.toml").write_text(
        "[marketplaces.readme-labs]\n"
        'source_type = "git"\n'
        f'ref = "{"0" * 40}"\n',
        encoding="utf-8",
    )
    plugin = {
        "marketplaceName": "readme-labs",
        "name": "readme-labs",
        "version": "0.2.0-rc.1",
        "source": {"path": (marketplace / "product").as_posix()},
    }

    with pytest.raises(RuntimeError, match="configured marketplace ref"):
        _artifact_binding(codex_home, plugin, "f" * 40)


def test_artifact_binding_rejects_tracked_marketplace_tampering(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    marketplace = codex_home / ".tmp" / "marketplaces" / "readme-labs"
    product = marketplace / "product"
    installed = (
        codex_home
        / "plugins"
        / "cache"
        / "readme-labs"
        / "readme-labs"
        / "0.2.0-rc.1"
    )
    product.mkdir(parents=True)
    (product / "plugin.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "readme-labs"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "eval@readme-labs.invalid"],
        cwd=marketplace,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=marketplace, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "fixture"],
        cwd=marketplace,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=marketplace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    codex_home.joinpath("config.toml").write_text(
        "[marketplaces.readme-labs]\n"
        'source_type = "git"\n'
        f'ref = "{revision}"\n',
        encoding="utf-8",
    )
    (marketplace / ".codex-marketplace-install.json").write_text(
        json.dumps(
            {
                "source_type": "git",
                "revision": revision,
            }
        ),
        encoding="utf-8",
    )
    shutil.copytree(product, installed)
    (product / "plugin.json").write_text('{"tampered": true}\n', encoding="utf-8")
    plugin = {
        "marketplaceName": "readme-labs",
        "name": "readme-labs",
        "version": "0.2.0-rc.1",
        "source": {"path": product.as_posix()},
    }

    with pytest.raises(RuntimeError, match="tracked modifications"):
        _artifact_binding(codex_home, plugin, revision)


def test_deterministic_scoring_accepts_finding_and_no_finding_runs(
    tmp_path: Path,
) -> None:
    finding_response = tmp_path / "finding.json"
    no_finding_response = tmp_path / "no-finding.json"
    _write_response(finding_response, finding=True)
    _write_response(no_finding_response, finding=False)

    finding_score = score_review_response(FINDING_CAPSULE, finding_response)
    no_finding_score = score_review_response(NO_FINDING_CAPSULE, no_finding_response)

    assert finding_score["result"] == "automatic_pass_requires_independent_review"
    assert no_finding_score["result"] == ("automatic_pass_requires_independent_review")


def test_deterministic_scoring_rejects_wrong_conclusion(tmp_path: Path) -> None:
    response = tmp_path / "response.json"
    _write_response(response, finding=False)

    score = score_review_response(FINDING_CAPSULE, response)

    assert score["result"] == "automatic_fail"
    assert score["automatic_checks"]["conclusion_match"] is False


def test_deterministic_scoring_rejects_unrecorded_execution_claim(
    tmp_path: Path,
) -> None:
    response = tmp_path / "response.json"
    _write_response(response, finding=True)
    value = json.loads(response.read_text(encoding="utf-8"))
    value["verification"].append("Attempted pytest, but the command failed.")
    response.write_text(json.dumps(value), encoding="utf-8")

    score = score_review_response(FINDING_CAPSULE, response)

    assert score["result"] == "automatic_fail"
    assert score["automatic_checks"]["execution_claims_consistent_with_events"] is False


def test_deterministic_scoring_matches_recorded_command_claim(tmp_path: Path) -> None:
    response = tmp_path / "response.json"
    events = tmp_path / "events.jsonl"
    _write_response(response, finding=True)
    value = json.loads(response.read_text(encoding="utf-8"))
    value["commands"] = [{"command": "pytest -q", "outcome": "succeeded"}]
    value["verification"].append("Executed pytest -q successfully.")
    response.write_text(json.dumps(value), encoding="utf-8")
    event = {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": '/bin/zsh -lc "pytest -q"',
            "exit_code": 0,
        },
    }
    events.write_text(json.dumps(event) + "\n", encoding="utf-8")

    score = score_review_response(FINDING_CAPSULE, response, events_path=events)

    assert score["result"] == "automatic_pass_requires_independent_review"


def test_deterministic_scoring_unwraps_codex_shell_quoting(tmp_path: Path) -> None:
    response = tmp_path / "response.json"
    events = tmp_path / "events.jsonl"
    _write_response(response, finding=True)
    command = "rg --files -g 'README*' -g '!vendor'"
    value = json.loads(response.read_text(encoding="utf-8"))
    value["commands"] = [{"command": command, "outcome": "succeeded"}]
    response.write_text(json.dumps(value), encoding="utf-8")
    event = {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": (
                "/bin/zsh -lc \"rg --files -g 'README*' "
                "-g '\"'!vendor'\"'\""
            ),
            "exit_code": 0,
        },
    }
    events.write_text(json.dumps(event) + "\n", encoding="utf-8")

    score = score_review_response(FINDING_CAPSULE, response, events_path=events)

    assert score["result"] == "automatic_pass_requires_independent_review"


def test_deterministic_scoring_marks_unattributed_sandbox_denial(
    tmp_path: Path,
) -> None:
    response = tmp_path / "response.json"
    events = tmp_path / "events.jsonl"
    stderr = tmp_path / "stderr.log"
    _write_response(response, finding=True)
    value = json.loads(response.read_text(encoding="utf-8"))
    value["commands"] = [{"command": "python -m pytest", "outcome": "failed"}]
    value["limitations"].append("Attempted python -m pytest; it was denied.")
    response.write_text(json.dumps(value), encoding="utf-8")
    events.write_text("", encoding="utf-8")
    stderr.write_text(
        "WARN sandbox: recorded sandbox violation: operation_not_permitted\n",
        encoding="utf-8",
    )

    score = score_review_response(
        FINDING_CAPSULE,
        response,
        events_path=events,
        stderr_path=stderr,
    )

    assert score["result"] == "automatic_pass_requires_independent_review"
    command_match = score["automatic_checks"]["command_claim_matches"][0]
    assert command_match["recorded_event_match"] is False
    assert command_match["sandbox_violation_match"] is True
    assert command_match["evidence"] == (
        "correlated_unattributed_sandbox_violation"
    )
    assert score["automatic_checks"]["used_unattributed_sandbox_evidence"] is True


def test_deterministic_scoring_does_not_overassign_sandbox_denial(
    tmp_path: Path,
) -> None:
    response = tmp_path / "response.json"
    events = tmp_path / "events.jsonl"
    stderr = tmp_path / "stderr.log"
    _write_response(response, finding=True)
    value = json.loads(response.read_text(encoding="utf-8"))
    value["commands"] = [
        {"command": "python -m pytest", "outcome": "failed"},
        {"command": "python -m build", "outcome": "failed"},
    ]
    response.write_text(json.dumps(value), encoding="utf-8")
    events.write_text("", encoding="utf-8")
    stderr.write_text(
        "WARN sandbox: recorded sandbox violation: operation_not_permitted\n",
        encoding="utf-8",
    )

    score = score_review_response(
        FINDING_CAPSULE,
        response,
        events_path=events,
        stderr_path=stderr,
    )

    assert score["result"] == "automatic_fail"
    matches = score["automatic_checks"]["command_claim_matches"]
    assert sum(item["sandbox_violation_match"] for item in matches) == 1
