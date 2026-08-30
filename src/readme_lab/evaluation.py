"""Run and score the repository's README-review task capsules."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.capsule import load_capsule, materialize_capsule

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESPONSE_SCHEMA_NAME = "review-response-v1.schema.json"
SCORECARD_SCHEMA_NAME = "review-scorecard-v1.schema.json"
RESPONSE_SCHEMA_PATH = REPOSITORY_ROOT / "evals" / RESPONSE_SCHEMA_NAME
SCORECARD_SCHEMA_PATH = REPOSITORY_ROOT / "evals" / SCORECARD_SCHEMA_NAME
IMMUTABLE_REVISION = re.compile(r"^[0-9a-f]{40}$")
EXECUTION_CLAIM = re.compile(
    r"\b(attempted|executed|ran|denied|blocked|passed|failed|completed)\b",
    re.IGNORECASE,
)


def _load_schema(name: str, source_path: Path) -> dict[str, Any]:
    if source_path.is_file():
        text = source_path.read_text(encoding="utf-8")
    else:
        text = (
            resources.files("readme_lab")
            .joinpath("data", name)
            .read_text(encoding="utf-8")
        )
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError(f"{name} must contain a JSON object")
    return schema


def load_response(path: Path) -> dict[str, Any]:
    """Load and validate a structured README-review response."""

    response = json.loads(path.read_text(encoding="utf-8"))
    schema = _load_schema(RESPONSE_SCHEMA_NAME, RESPONSE_SCHEMA_PATH)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(response)
    return response


def load_scorecard(capsule_path: Path) -> dict[str, Any]:
    """Load a held-out scorecard for post-execution evaluation."""

    capsule = load_capsule(capsule_path)
    scorecard_path = (capsule_path.parent / capsule["scorecard"]).resolve()
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    schema = _load_schema(SCORECARD_SCHEMA_NAME, SCORECARD_SCHEMA_PATH)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(scorecard)
    if scorecard["scenario_id"] != capsule["id"]:
        raise ValueError("scorecard scenario_id does not match its capsule")
    return scorecard


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command_events(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    events: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        event = json.loads(line)
        item = event.get("item", {})
        if event.get("type") != "item.completed":
            continue
        if item.get("type") != "command_execution":
            continue
        events.append(
            {
                "command": item["command"],
                "outcome": "succeeded" if item.get("exit_code") == 0 else "failed",
            }
        )
    return events


def _unwrap_shell_command(command: str) -> str:
    """Return the payload of a recorded ``shell -lc`` command when present."""

    try:
        tokens = shlex.split(command)
    except ValueError:
        return command
    if (
        len(tokens) == 3
        and Path(tokens[0]).name in {"bash", "sh", "zsh"}
        and tokens[1] in {"-c", "-lc"}
    ):
        return tokens[2]
    return command


def _execution_claim_phrases(response: dict[str, Any]) -> list[str]:
    claims: list[str] = []
    for field in ("verification", "limitations"):
        for text in response[field]:
            if EXECUTION_CLAIM.search(text):
                claims.append(text)
    return claims


def score_review_response(
    capsule_path: Path,
    response_path: Path,
    *,
    events_path: Path | None = None,
) -> dict[str, Any]:
    """Apply deterministic gates and leave semantic judgments for review."""

    response = load_response(response_path)
    scorecard = load_scorecard(capsule_path)
    unmatched_response_indexes = set(range(len(response["findings"])))
    matches: list[dict[str, Any]] = []

    for expected in scorecard["expected_findings"]:
        matched_index = next(
            (
                index
                for index in sorted(unmatched_response_indexes)
                if response["findings"][index]["category"] == expected["category"]
                and response["findings"][index]["severity"] == expected["severity"]
            ),
            None,
        )
        if matched_index is not None:
            unmatched_response_indexes.remove(matched_index)
        matches.append(
            {
                "expected_id": expected["id"],
                "response_finding_index": matched_index,
                "category_and_severity_match": matched_index is not None,
                "semantic_review_required": True,
            }
        )

    conclusion_match = response["conclusion"] == scorecard["expected_conclusion"]
    response_consistent = (
        response["conclusion"] == "material_findings" and bool(response["findings"])
    ) or (response["conclusion"] == "no_material_findings" and not response["findings"])
    expected_match = all(item["category_and_severity_match"] for item in matches)
    no_unexpected_findings = not unmatched_response_indexes
    recorded_commands = _command_events(events_path)
    command_matches = []
    for claim in response["commands"]:
        matched = any(
            claim["command"] == _unwrap_shell_command(event["command"])
            and claim["outcome"] == event["outcome"]
            for event in recorded_commands
        )
        command_matches.append({**claim, "recorded_event_match": matched})
    execution_claim_phrases = _execution_claim_phrases(response)
    execution_claims_consistent = all(
        item["recorded_event_match"] for item in command_matches
    ) and (not execution_claim_phrases or bool(response["commands"]))
    automatic_pass = (
        conclusion_match
        and response_consistent
        and expected_match
        and no_unexpected_findings
        and execution_claims_consistent
    )
    return {
        "score_schema_version": "1.0.0",
        "scenario_id": scorecard["scenario_id"],
        "response_sha256": _sha256(response_path),
        "automatic_checks": {
            "conclusion_match": conclusion_match,
            "response_conclusion_and_findings_consistent": response_consistent,
            "expected_finding_matches": matches,
            "unexpected_response_finding_indexes": sorted(unmatched_response_indexes),
            "command_claim_matches": command_matches,
            "execution_claim_phrases": execution_claim_phrases,
            "execution_claims_consistent_with_events": execution_claims_consistent,
        },
        "anti_findings": [
            {**item, "semantic_review_required": True}
            for item in scorecard["anti_findings"]
        ],
        "result": (
            "automatic_pass_requires_independent_review"
            if automatic_pass
            else "automatic_fail"
        ),
        "limitations": [
            "Category matching does not establish that evidence or impact is correct.",
            "Command claims are matched textually and still require semantic review.",
            "Anti-findings and success conditions require independent semantic review.",
        ],
    }


def build_executor_prompt(capsule: dict[str, Any]) -> str:
    """Build a task prompt without scenario or scorecard identifiers."""

    return "\n".join(
        (
            "Work only as a reviewer; do not edit repository files.",
            "Use any applicable installed capability that Codex discovers normally.",
            "Inspect repository evidence to support or reject material findings.",
            "In commands, list every command you claim was attempted or executed.",
            "Return the requested structured response and nothing outside it.",
            "",
            f"Task: {capsule['task']}",
        )
    )


def _git_root(path: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def build_executor_permission_profile(held_out_root: Path) -> str:
    """Create a Codex profile that denies the held-out factory checkout."""

    encoded_path = json.dumps(held_out_root.resolve().as_posix())
    return "\n".join(
        (
            'default_permissions = "readme-eval"',
            "",
            "[permissions.readme-eval]",
            'description = "README evaluation workspace with held-out factory data."',
            'extends = ":workspace"',
            "",
            "[permissions.readme-eval.filesystem]",
            f'{encoded_path} = "deny"',
            "",
            "[permissions.readme-eval.network]",
            "enabled = false",
            "",
        )
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _codex_inventory(executable: str, plugin_id: str) -> dict[str, Any]:
    version = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    result = subprocess.run(
        [executable, "plugin", "list", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    inventory = json.loads(result.stdout)
    installed = [
        item for item in inventory.get("installed", []) if item["pluginId"] == plugin_id
    ]
    if len(installed) != 1 or not installed[0].get("enabled"):
        raise RuntimeError(f"expected one enabled installed plugin: {plugin_id}")
    return {"codex_version": version, "plugin": installed[0]}


def _prepare_permission_profile(held_out_root: Path) -> tuple[str, Path]:
    raw_codex_home = os.environ.get("CODEX_HOME")
    if raw_codex_home is None:
        raise RuntimeError(
            "blinded execution requires an explicit disposable CODEX_HOME"
        )
    codex_home = Path(raw_codex_home).resolve()
    personal_codex_home = (Path.home() / ".codex").resolve()
    if codex_home == personal_codex_home:
        raise RuntimeError(
            "refusing to write an evaluation profile to personal CODEX_HOME"
        )
    if not codex_home.is_dir():
        raise FileNotFoundError(f"CODEX_HOME does not exist: {codex_home}")

    profile_name = "readme-labs-evaluation"
    profile_path = codex_home / f"{profile_name}.config.toml"
    profile = build_executor_permission_profile(held_out_root)
    if profile_path.exists() and profile_path.read_text(encoding="utf-8") != profile:
        raise FileExistsError(
            f"refusing to replace a different profile: {profile_path}"
        )
    profile_path.write_text(profile, encoding="utf-8")
    return profile_name, profile_path


def _verify_permission_profile(
    executable: str,
    *,
    profile_name: str,
    workspace: Path,
    held_out_root: Path,
) -> None:
    held_out_probe = held_out_root / "README.md"
    command = [
        executable,
        "sandbox",
        "--profile",
        profile_name,
        "--permission-profile",
        "readme-eval",
        "--cd",
        workspace.as_posix(),
        "/bin/sh",
        "-c",
        (
            "/usr/bin/head -c 1 README.md >/dev/null 2>&1 "
            '&& ! /usr/bin/head -c 1 "$1" >/dev/null 2>&1'
        ),
        "readme-eval-preflight",
        held_out_probe.as_posix(),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "permission profile preflight did not prove workspace-read and "
            "factory-deny boundaries"
        )


def run_codex_capsule(
    capsule_path: Path,
    *,
    workspace: Path,
    run_dir: Path,
    run_id: str,
    artifact_revision: str,
    plugin_id: str,
    model: str,
    reasoning_effort: str,
    codex_executable: str = "codex",
) -> dict[str, Any]:
    """Run one blinded Codex execution and score it after the process exits."""

    if not IMMUTABLE_REVISION.fullmatch(artifact_revision):
        raise ValueError("artifact_revision must be a full 40-character Git commit")
    if workspace.exists() or run_dir.exists():
        raise FileExistsError("workspace and run_dir must not already exist")

    capsule_path = capsule_path.resolve()
    held_out_root = _git_root(capsule_path)
    if _is_within(workspace, held_out_root) or _is_within(run_dir, held_out_root):
        raise ValueError("workspace and run_dir must be outside the held-out checkout")

    capsule = load_capsule(capsule_path)
    inventory = _codex_inventory(codex_executable, plugin_id)
    materialization = materialize_capsule(capsule_path, workspace)
    run_dir.mkdir(parents=True)
    response_schema = run_dir / RESPONSE_SCHEMA_NAME
    shutil.copy2(RESPONSE_SCHEMA_PATH, response_schema)
    profile_name, profile_path = _prepare_permission_profile(held_out_root)
    _verify_permission_profile(
        codex_executable,
        profile_name=profile_name,
        workspace=workspace,
        held_out_root=held_out_root,
    )
    response_path = run_dir / "response.json"
    events_path = run_dir / "events.jsonl"
    stderr_path = run_dir / "stderr.log"
    prompt = build_executor_prompt(capsule)
    started_at = datetime.now(UTC)
    command = [
        codex_executable,
        "exec",
        "--profile",
        profile_name,
        "--ephemeral",
        "--json",
        "--color",
        "never",
        "--cd",
        workspace.as_posix(),
        "--output-schema",
        response_schema.as_posix(),
        "--output-last-message",
        response_path.as_posix(),
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-",
    ]
    result = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    finished_at = datetime.now(UTC)
    events_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")

    run_record: dict[str, Any] = {
        "run_schema_version": "2.0.0",
        "run_id": run_id,
        "scenario_id": capsule["id"],
        "task_sha256": hashlib.sha256(capsule["task"].encode()).hexdigest(),
        "artifact_revision": artifact_revision,
        "executor": {
            "kind": "codex_cli",
            "model": model,
            "reasoning_effort": reasoning_effort,
            **inventory,
        },
        "execution": {
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
            "return_code": result.returncode,
            "ephemeral": True,
            "network_policy": capsule["environment"]["network"],
            "permission_profile": "readme-eval",
            "permission_profile_sha256": _sha256(profile_path),
            "factory_checkout_denied_by_command_sandbox": True,
            "permission_preflight_passed": True,
            "scorecard_read_after_executor_exit": True,
        },
        "materialization": materialization,
        "artifacts": {
            "events": events_path.name,
            "events_sha256": _sha256(events_path),
            "stderr": stderr_path.name,
            "stderr_sha256": _sha256(stderr_path),
            "response": response_path.name,
        },
    }
    if result.returncode != 0:
        run_record["result"] = "executor_failed"
        _write_json(run_dir / "run.json", run_record)
        raise RuntimeError(f"Codex executor failed with exit code {result.returncode}")

    load_response(response_path)
    score = score_review_response(capsule_path, response_path, events_path=events_path)
    score_path = run_dir / "score.json"
    _write_json(score_path, score)
    scorecard_path = (capsule_path.parent / capsule["scorecard"]).resolve()
    run_record["artifacts"].update(
        {
            "response_sha256": _sha256(response_path),
            "score": score_path.name,
            "score_sha256": _sha256(score_path),
            "held_out_scorecard_sha256": _sha256(scorecard_path),
        }
    )
    run_record["result"] = score["result"]
    _write_json(run_dir / "run.json", run_record)
    return run_record
