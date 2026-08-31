from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from readme_lab.capsule import load_capsule, materialize_capsule
from readme_lab.evaluation import (
    RESPONSE_SCHEMA_PATH,
    SCORECARD_SCHEMA_PATH,
    _artifact_binding,
    build_executor_permission_profile,
    build_executor_prompt,
    load_scorecard,
    run_candidate_review_trial,
    score_review_response,
    stage_candidate_review_skill,
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


def _write_fake_codex(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import sys

arguments = sys.argv[1:]
if arguments == ["--version"]:
    print("codex-cli fake-candidate-review")
    raise SystemExit(0)
if arguments and arguments[0] == "sandbox":
    raise SystemExit(0)
if arguments and arguments[0] == "exec":
    output = Path(arguments[arguments.index("--output-last-message") + 1])
    shutil.copyfile(os.environ["README_LABS_FAKE_RESPONSE"], output)
    print(json.dumps({"type": "turn.completed"}))
    raise SystemExit(0)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


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


def test_executor_prompt_can_name_only_the_selected_candidate_skill() -> None:
    capsule = load_capsule(FINDING_CAPSULE)

    prompt = build_executor_prompt(
        capsule,
        skill_name="alternate-readme-review",
        invocation="explicit",
    )

    assert "$alternate-readme-review" in prompt
    assert "readme-labs" not in prompt
    assert capsule["id"] not in prompt
    assert capsule["scorecard"] not in prompt


def test_permission_profile_denies_factory_without_leaking_scenario_name() -> None:
    profile = build_executor_permission_profile(Path("/tmp/factory-checkout"))

    assert 'extends = ":workspace"' in profile
    assert '= "deny"' in profile
    assert "enabled = false" in profile
    assert Path("/tmp/factory-checkout").resolve().as_posix() in profile
    assert "missing-first-path" not in profile


def test_candidate_review_skill_stages_without_changing_subject_git_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    materialize_capsule(FINDING_CAPSULE, workspace)

    binding = stage_candidate_review_skill(
        Path("candidates/reademe-temp-modular-readme-v1/candidate.json"),
        workspace,
    )

    assert binding["candidate_id"] == "reademe-temp-modular-readme-v1"
    assert binding["entrypoint"]["id"] == "modular-readme"
    assert binding["entrypoint"]["skill_name"] == "modular-readme"
    assert binding["staging"]["surface"] == "repository_local_skill"
    assert (workspace / ".agents/skills/modular-readme/SKILL.md").is_file()
    assert (
        subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        == ""
    )


def test_candidate_review_trial_runs_as_evidence_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    response = tmp_path / "response.json"
    _write_response(response, finding=True)
    fake_codex = tmp_path / "fake-codex"
    _write_fake_codex(fake_codex)
    monkeypatch.setenv("CODEX_HOME", codex_home.as_posix())
    monkeypatch.setenv("README_LABS_FAKE_RESPONSE", response.as_posix())
    workspace = tmp_path / "workspace"
    run_dir = tmp_path / "run"

    run = run_candidate_review_trial(
        Path("candidates/reademe-temp-modular-readme-v1/candidate.json"),
        FINDING_CAPSULE,
        workspace=workspace,
        run_dir=run_dir,
        run_id="alternate-review-skill",
        model="fake-model",
        reasoning_effort="high",
        codex_executable=fake_codex.as_posix(),
    )

    assert run["candidate_id"] == "reademe-temp-modular-readme-v1"
    assert run["evaluation_role"] == "experimental_candidate_review"
    assert run["candidate_invocation"] == "explicit"
    assert run["automated_authority"] == "evidence_only"
    assert run["hypothesis_disposition"] == "not_decided"
    assert run["execution"]["subject_unchanged"] is True
    assert run["result"] == "completed"
    assert run["automated_score_result"] == (
        "automatic_pass_requires_independent_review"
    )
    assert (run_dir / "run.json").is_file()
    assert (run_dir / "score.json").is_file()


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
