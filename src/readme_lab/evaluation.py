"""Run and score the repository's README-review task capsules."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.artifacts import (
    load_schema,
    resolve_contained,
    sha256,
    tree_sha256,
    write_json,
)
from readme_lab.candidates import load_candidate, verify_candidate
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
SANDBOX_VIOLATION = re.compile(r"recorded sandbox violation", re.IGNORECASE)
SKILL_NAME = re.compile(r"^name:\s*['\"]?([a-z0-9]+(?:-[a-z0-9]+)*)['\"]?\s*$")


def load_response(path: Path) -> dict[str, Any]:
    """Load and validate a structured README-review response."""

    response = json.loads(path.read_text(encoding="utf-8"))
    schema = load_schema(RESPONSE_SCHEMA_NAME, RESPONSE_SCHEMA_PATH)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(response)
    return response


def load_scorecard(capsule_path: Path) -> dict[str, Any]:
    """Load a held-out scorecard for post-execution evaluation."""

    capsule = load_capsule(capsule_path)
    scorecard_path = (capsule_path.parent / capsule["scorecard"]).resolve()
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    schema = load_schema(SCORECARD_SCHEMA_NAME, SCORECARD_SCHEMA_PATH)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(scorecard)
    if scorecard["scenario_id"] != capsule["id"]:
        raise ValueError("scorecard scenario_id does not match its capsule")
    return scorecard


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git_subtree_sha256(repository: Path, revision: str, subtree: Path) -> str:
    subtree_text = subtree.as_posix().rstrip("/")
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", revision, "--", subtree_text],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    if not entries:
        raise RuntimeError("declared artifact revision has no plugin product")
    digest = hashlib.sha256()
    for entry in entries:
        metadata, raw_path = entry.split(b"\t", 1)
        blob_hash = metadata.split()[-1].decode()
        path = Path(os.fsdecode(raw_path))
        relative = path.relative_to(subtree).as_posix().encode()
        blob = subprocess.run(
            ["git", "cat-file", "blob", blob_hash],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        digest.update(relative)
        digest.update(b"\0")
        digest.update(blob)
        digest.update(b"\0")
    return digest.hexdigest()


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


def _sandbox_violation_count(path: Path | None) -> int:
    if path is None:
        return 0
    return len(SANDBOX_VIOLATION.findall(path.read_text(encoding="utf-8")))


def score_review_response(
    capsule_path: Path,
    response_path: Path,
    *,
    events_path: Path | None = None,
    stderr_path: Path | None = None,
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
    remaining_sandbox_violations = _sandbox_violation_count(stderr_path)
    command_matches = []
    for claim in response["commands"]:
        event_match = any(
            claim["command"] == _unwrap_shell_command(event["command"])
            and claim["outcome"] == event["outcome"]
            for event in recorded_commands
        )
        sandbox_violation_match = (
            not event_match
            and claim["outcome"] == "failed"
            and remaining_sandbox_violations > 0
        )
        if sandbox_violation_match:
            remaining_sandbox_violations -= 1
        command_matches.append(
            {
                **claim,
                "recorded_event_match": event_match,
                "sandbox_violation_match": sandbox_violation_match,
                "evidence": (
                    "command_event"
                    if event_match
                    else "correlated_unattributed_sandbox_violation"
                    if sandbox_violation_match
                    else None
                ),
            }
        )
    execution_claim_phrases = _execution_claim_phrases(response)
    execution_claims_consistent = all(
        item["evidence"] is not None for item in command_matches
    ) and (not execution_claim_phrases or bool(response["commands"]))
    used_unattributed_sandbox_evidence = any(
        item["sandbox_violation_match"] for item in command_matches
    )
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
        "response_sha256": sha256(response_path),
        "automatic_checks": {
            "conclusion_match": conclusion_match,
            "response_conclusion_and_findings_consistent": response_consistent,
            "expected_finding_matches": matches,
            "unexpected_response_finding_indexes": sorted(unmatched_response_indexes),
            "command_claim_matches": command_matches,
            "execution_claim_phrases": execution_claim_phrases,
            "execution_claims_consistent_with_events": execution_claims_consistent,
            "sandbox_violation_count": _sandbox_violation_count(stderr_path),
            "used_unattributed_sandbox_evidence": (
                used_unattributed_sandbox_evidence
            ),
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
            *(
                [
                    "Codex stderr reported a sandbox denial without its command; the "
                    "failed command is correlated by count but not machine-attributed."
                ]
                if used_unattributed_sandbox_evidence
                else []
            ),
            "Anti-findings and success conditions require independent semantic review.",
        ],
    }


def build_executor_prompt(
    capsule: dict[str, Any],
    *,
    skill_name: str | None = None,
    invocation: str = "discovery",
) -> str:
    """Build a task prompt without scenario or scorecard identifiers."""

    if invocation not in {"discovery", "explicit"}:
        raise ValueError(f"unsupported candidate invocation mode: {invocation}")
    if invocation == "explicit" and skill_name is None:
        raise ValueError("explicit candidate invocation requires a skill name")
    capability_instruction = (
        f"Use ${skill_name} as the review treatment for this trial."
        if invocation == "explicit"
        else "Use any applicable installed capability that Codex discovers normally."
    )
    return "\n".join(
        (
            "Work only as a reviewer; do not edit repository files.",
            capability_instruction,
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


def _explicit_codex_home() -> Path:
    raw_codex_home = os.environ.get("CODEX_HOME")
    if raw_codex_home is None:
        raise RuntimeError(
            "blinded execution requires an explicit disposable CODEX_HOME"
        )
    codex_home = Path(raw_codex_home).resolve()
    personal_codex_home = (Path.home() / ".codex").resolve()
    if codex_home == personal_codex_home:
        raise RuntimeError("refusing to use personal CODEX_HOME for blinded execution")
    if not codex_home.is_dir():
        raise FileNotFoundError(f"CODEX_HOME does not exist: {codex_home}")
    return codex_home


def _assert_candidate_codex_home_isolated(codex_home: Path) -> None:
    """Reject ambient skills or plugins that would confound a candidate trial."""

    for relative in ("skills", "plugins/cache", ".tmp/marketplaces"):
        path = codex_home / relative
        if path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise RuntimeError(
                f"candidate review CODEX_HOME contains another treatment: {relative}"
            )
    config_path = codex_home / "config.toml"
    if config_path.is_file():
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        if config.get("marketplaces"):
            raise RuntimeError(
                "candidate review CODEX_HOME contains configured marketplaces"
            )


def _codex_skill_name(skill_file: Path) -> str:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Codex skill candidate requires YAML frontmatter")
    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line == "---"
        )
    except StopIteration as error:
        raise ValueError(
            "Codex skill candidate has unclosed YAML frontmatter"
        ) from error
    names = [
        match.group(1)
        for line in lines[1:closing]
        if (match := SKILL_NAME.fullmatch(line)) is not None
    ]
    if len(names) != 1:
        raise ValueError("Codex skill candidate requires one simple frontmatter name")
    return names[0]


def _candidate_codex_skill_entrypoint(
    candidate_path: Path,
    entrypoint_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    candidate_path = candidate_path.resolve()
    verification = verify_candidate(candidate_path)
    if not verification["verified"]:
        raise ValueError("candidate failed verification")
    candidate = load_candidate(candidate_path)
    if candidate["storage"]["mode"] != "embedded":
        raise ValueError("candidate review trials require embedded candidate bytes")

    compatible = [
        entrypoint
        for entrypoint in candidate["entrypoints"]
        if entrypoint["format"] == "codex_skill"
        and entrypoint.get("host") in {None, "codex"}
    ]
    if entrypoint_id is not None:
        compatible = [
            entrypoint
            for entrypoint in compatible
            if entrypoint["id"] == entrypoint_id
        ]
        if not compatible:
            raise ValueError(
                f"candidate has no Codex skill entrypoint named {entrypoint_id}"
            )
    if len(compatible) != 1:
        raise ValueError(
            "candidate review requires one Codex skill entrypoint or an explicit "
            "entrypoint id"
        )
    entrypoint = compatible[0]
    artifact_root = resolve_contained(
        candidate_path.parent, candidate["storage"]["artifact_root"]
    )
    source = resolve_contained(artifact_root, entrypoint["path"])
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise ValueError("Codex skill candidate entrypoint must contain SKILL.md")
    _codex_skill_name(source / "SKILL.md")
    return candidate, verification, entrypoint, source


def stage_candidate_review_skill(
    candidate_path: Path,
    workspace: Path,
    *,
    entrypoint_id: str | None = None,
) -> dict[str, Any]:
    """Stage one verified candidate as the sole repository-local review skill."""

    candidate, verification, entrypoint, source = _candidate_codex_skill_entrypoint(
        candidate_path, entrypoint_id
    )
    workspace = workspace.resolve()
    if not (workspace / ".git").is_dir():
        raise ValueError(
            "candidate review workspace must be an isolated Git repository"
        )
    skills_root = workspace / ".agents/skills"
    if skills_root.exists() and any(skills_root.iterdir()):
        raise ValueError(
            "candidate review workspace already contains repository skills"
        )
    destination = skills_root / entrypoint["id"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)

    exclude_path = workspace / ".git/info/exclude"
    exclude_line = f"/.agents/skills/{entrypoint['id']}/"
    existing_excludes = exclude_path.read_text(encoding="utf-8")
    if exclude_line not in existing_excludes.splitlines():
        with exclude_path.open("a", encoding="utf-8") as stream:
            if existing_excludes and not existing_excludes.endswith("\n"):
                stream.write("\n")
            stream.write(exclude_line + "\n")

    visible_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if visible_status:
        raise RuntimeError("candidate staging changed the visible subject Git state")
    return {
        "candidate_id": candidate["id"],
        "candidate_kind": candidate["kind"],
        "authority": candidate["authority"],
        "descriptor_sha256": sha256(candidate_path.resolve()),
        "candidate_tree_sha256": verification["tree_sha256"],
        "entrypoint": {
            "id": entrypoint["id"],
            "path": entrypoint["path"],
            "format": entrypoint["format"],
            "host": entrypoint.get("host"),
            "skill_name": _codex_skill_name(source / "SKILL.md"),
            "tree_sha256": tree_sha256(source),
        },
        "staging": {
            "surface": "repository_local_skill",
            "path": destination.relative_to(workspace).as_posix(),
            "tree_sha256": tree_sha256(destination),
            "excluded_from_subject_git_status": True,
        },
    }


def _artifact_binding(
    codex_home: Path,
    plugin: dict[str, Any],
    artifact_revision: str,
) -> dict[str, Any]:
    marketplace_name = plugin["marketplaceName"]
    marketplace_root = (
        codex_home / ".tmp" / "marketplaces" / marketplace_name
    ).resolve()
    config_path = codex_home.resolve() / "config.toml"
    if not config_path.is_file():
        raise FileNotFoundError(f"missing Codex config: {config_path}")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    marketplace_config = config.get("marketplaces", {}).get(marketplace_name)
    if not isinstance(marketplace_config, dict):
        raise RuntimeError("plugin marketplace is missing from Codex config")
    if marketplace_config.get("source_type") != "git":
        raise RuntimeError("evaluation plugin must come from a Git marketplace")
    if marketplace_config.get("ref") != artifact_revision:
        raise RuntimeError(
            "configured marketplace ref does not match artifact revision"
        )

    install_record_path = marketplace_root / ".codex-marketplace-install.json"
    install_record_sha256 = None
    if install_record_path.is_file():
        install_record = json.loads(
            install_record_path.read_text(encoding="utf-8")
        )
        if install_record.get("source_type") != "git":
            raise RuntimeError("marketplace install record is not a Git source")
        if install_record.get("revision") != artifact_revision:
            raise RuntimeError(
                "marketplace install record does not match artifact revision"
            )
        install_record_sha256 = sha256(install_record_path)

    clone_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=marketplace_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if clone_revision != artifact_revision:
        raise RuntimeError("marketplace clone does not match artifact revision")
    tracked_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=marketplace_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if tracked_status:
        raise RuntimeError("marketplace clone has tracked modifications")

    marketplace_product = Path(plugin["source"]["path"]).resolve()
    if not _is_within(marketplace_product, marketplace_root):
        raise RuntimeError("plugin source is outside its marketplace snapshot")
    installed_product = (
        codex_home
        / "plugins"
        / "cache"
        / marketplace_name
        / plugin["name"]
        / plugin["version"]
    ).resolve()
    if not marketplace_product.is_dir() or not installed_product.is_dir():
        raise FileNotFoundError("marketplace or installed plugin product is missing")
    marketplace_sha256 = _tree_sha256(marketplace_product)
    product_relative = marketplace_product.relative_to(marketplace_root)
    committed_sha256 = _git_subtree_sha256(
        marketplace_root,
        artifact_revision,
        product_relative,
    )
    if marketplace_sha256 != committed_sha256:
        raise RuntimeError("marketplace product differs from declared Git revision")
    installed_sha256 = _tree_sha256(installed_product)
    if marketplace_sha256 != installed_sha256:
        raise RuntimeError("installed plugin differs from the marketplace product")

    return {
        "artifact_revision_verified": True,
        "marketplace_revision": clone_revision,
        "marketplace_ref": marketplace_config["ref"],
        "marketplace_config_sha256": sha256(config_path),
        "marketplace_install_record_sha256": install_record_sha256,
        "committed_product_sha256": committed_sha256,
        "marketplace_product_sha256": marketplace_sha256,
        "installed_product_sha256": installed_sha256,
        "installed_product_matches_marketplace": True,
    }


def _codex_version(executable: str) -> str:
    return subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _codex_inventory(
    executable: str,
    plugin_id: str,
    artifact_revision: str,
) -> dict[str, Any]:
    version = _codex_version(executable)
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
    return {
        "codex_version": version,
        "plugin": installed[0],
        "artifact_binding": _artifact_binding(
            _explicit_codex_home(), installed[0], artifact_revision
        ),
    }


def _prepare_permission_profile(held_out_root: Path) -> tuple[str, Path]:
    codex_home = _explicit_codex_home()

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
    artifact_revision: str | None,
    plugin_id: str,
    model: str,
    reasoning_effort: str,
    candidate_path: Path | None = None,
    candidate_entrypoint_id: str | None = None,
    candidate_invocation: str = "explicit",
    codex_executable: str = "codex",
) -> dict[str, Any]:
    """Run one blinded Codex execution and score it after the process exits."""

    if (artifact_revision is None) == (candidate_path is None):
        raise ValueError(
            "review execution requires exactly one installed plugin revision or "
            "candidate"
        )
    candidate_mode = candidate_path is not None
    if artifact_revision is not None and not IMMUTABLE_REVISION.fullmatch(
        artifact_revision
    ):
        raise ValueError("artifact_revision must be a full 40-character Git commit")
    if workspace.exists() or run_dir.exists():
        raise FileExistsError("workspace and run_dir must not already exist")

    capsule_path = capsule_path.resolve()
    held_out_root = _git_root(capsule_path)
    if _is_within(workspace, held_out_root) or _is_within(run_dir, held_out_root):
        raise ValueError("workspace and run_dir must be outside the held-out checkout")
    if candidate_path is not None:
        candidate_path = candidate_path.resolve()
        if not _is_within(candidate_path, held_out_root):
            raise ValueError(
                "candidate descriptor must be inside the held-out domain checkout"
            )
        _candidate_codex_skill_entrypoint(
            candidate_path,
            candidate_entrypoint_id,
        )
        candidate_codex_home = _explicit_codex_home()
        _assert_candidate_codex_home_isolated(candidate_codex_home)
    elif candidate_invocation != "explicit":
        raise ValueError("candidate invocation applies only to candidate trials")

    capsule = load_capsule(capsule_path)
    if candidate_mode:
        inventory: dict[str, Any] = {"codex_version": _codex_version(codex_executable)}
    else:
        assert artifact_revision is not None
        inventory = _codex_inventory(
            codex_executable,
            plugin_id,
            artifact_revision,
        )
    materialization = materialize_capsule(capsule_path, workspace)
    candidate_binding = None
    if candidate_path is not None:
        candidate_binding = stage_candidate_review_skill(
            candidate_path,
            workspace,
            entrypoint_id=candidate_entrypoint_id,
        )
        inventory["candidate_treatment"] = candidate_binding
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
    prompt = build_executor_prompt(
        capsule,
        skill_name=(
            candidate_binding["entrypoint"]["skill_name"]
            if candidate_binding is not None
            else None
        ),
        invocation=(
            candidate_invocation if candidate_binding is not None else "discovery"
        ),
    )
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
    subject_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    subject_diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        cwd=workspace,
        check=True,
        capture_output=True,
    ).stdout
    treatment_state = None
    if candidate_binding is not None:
        staged_treatment = workspace / candidate_binding["staging"]["path"]
        treatment_digest = (
            tree_sha256(staged_treatment) if staged_treatment.is_dir() else None
        )
        treatment_state = {
            "candidate_codex_home_isolated": True,
            "candidate_treatment_present_after_run": staged_treatment.is_dir(),
            "candidate_treatment_sha256_after_run": treatment_digest,
            "candidate_treatment_unchanged": (
                treatment_digest == candidate_binding["staging"]["tree_sha256"]
            ),
        }

    run_record: dict[str, Any] = {
        "run_schema_version": "2.0.0",
        "run_id": run_id,
        "scenario_id": capsule["id"],
        "task_sha256": hashlib.sha256(capsule["task"].encode()).hexdigest(),
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
            "permission_profile_sha256": sha256(profile_path),
            "factory_checkout_denied_by_command_sandbox": True,
            "permission_preflight_passed": True,
            "scorecard_read_after_executor_exit": True,
            "subject_unchanged": not subject_status,
            "subject_status": subject_status,
            "subject_diff_sha256": hashlib.sha256(subject_diff).hexdigest(),
        },
        "materialization": materialization,
        "artifacts": {
            "events": events_path.name,
            "events_sha256": sha256(events_path),
            "stderr": stderr_path.name,
            "stderr_sha256": sha256(stderr_path),
            "response": response_path.name,
        },
    }
    if candidate_binding is None:
        run_record["artifact_revision"] = artifact_revision
    else:
        assert treatment_state is not None
        run_record["execution"].update(treatment_state)
        run_record.update(
            {
                "candidate_id": candidate_binding["candidate_id"],
                "candidate": candidate_binding,
                "candidate_invocation": candidate_invocation,
                "evaluation_role": "experimental_candidate_review",
                "automated_authority": "evidence_only",
                "hypothesis_disposition": "not_decided",
            }
        )
    if result.returncode != 0:
        run_record["result"] = "executor_failed"
        write_json(run_dir / "run.json", run_record)
        raise RuntimeError(f"Codex executor failed with exit code {result.returncode}")

    load_response(response_path)
    score = score_review_response(
        capsule_path,
        response_path,
        events_path=events_path,
        stderr_path=stderr_path,
    )
    score_path = run_dir / "score.json"
    write_json(score_path, score)
    scorecard_path = (capsule_path.parent / capsule["scorecard"]).resolve()
    run_record["artifacts"].update(
        {
            "response_sha256": sha256(response_path),
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "held_out_scorecard_sha256": sha256(scorecard_path),
        }
    )
    if candidate_binding is None:
        run_record["result"] = score["result"]
    else:
        run_record["automated_score_result"] = score["result"]
        run_record["result"] = (
            "completed"
            if run_record["execution"]["subject_unchanged"]
            and run_record["execution"]["candidate_treatment_unchanged"]
            else "completed_with_boundary_violation"
        )
    write_json(run_dir / "run.json", run_record)
    return run_record


def run_candidate_review_trial(
    candidate_path: Path,
    capsule_path: Path,
    *,
    workspace: Path,
    run_dir: Path,
    run_id: str,
    model: str,
    reasoning_effort: str,
    entrypoint_id: str | None = None,
    invocation: str = "explicit",
    codex_executable: str = "codex",
) -> dict[str, Any]:
    """Run one experimental Codex skill candidate against a held-out capsule."""

    return run_codex_capsule(
        capsule_path,
        workspace=workspace,
        run_dir=run_dir,
        run_id=run_id,
        artifact_revision=None,
        plugin_id="",
        model=model,
        reasoning_effort=reasoning_effort,
        candidate_path=candidate_path,
        candidate_entrypoint_id=entrypoint_id,
        candidate_invocation=invocation,
        codex_executable=codex_executable,
    )
