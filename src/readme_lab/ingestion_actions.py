"""Guarded executors for ingestion actions that change source or GitHub state."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from readme_lab.artifacts import artifact_sha256, resolve_contained
from readme_lab.git_sources import git_identity, run_git
from readme_lab.ingestion import (
    _job_directory,
    _load_job_from_directory,
    _log,
    _store_job,
    _target,
    _verify_target,
    _write_json,
    load_external_action_plan,
)
from readme_lab.intake import fingerprint_git_path
from readme_lab.migration import (
    build_git_migration_receipt,
    write_git_migration_receipt,
)


def _run(
    arguments: list[str], *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _write_action_result(
    job_dir: Path, plan: dict[str, Any], result: dict[str, Any]
) -> None:
    path = job_dir / "control/actions" / f"{plan['id']}.result.json"
    _write_json(path, result)
    job = _load_job_from_directory(job_dir)
    _log(job, "external_action_executed", action=plan["action"], action_id=plan["id"])
    _store_job(job_dir, job)


def _repository_view(gh: str, repository: str) -> dict[str, Any] | None:
    result = _run(
        [
            gh,
            "repo",
            "view",
            repository,
            "--json",
            "name,owner,isPrivate,isArchived,viewerPermission,url",
        ],
        check=False,
    )
    if result.returncode != 0:
        return None
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise TypeError("GitHub repository view must return an object")
    return value


def _verify_owned(view: dict[str, Any], owner: str) -> None:
    actual_owner = view.get("owner")
    if isinstance(actual_owner, dict):
        actual_owner = actual_owner.get("login")
    if actual_owner != owner or view.get("viewerPermission") != "ADMIN":
        raise PermissionError(
            "authenticated GitHub identity does not administer target"
        )


def _snapshot_repository(checkout: Path, destination: Path) -> None:
    shutil.copytree(
        checkout,
        destination,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git"),
    )
    run_git(destination, "init", "--quiet", "--initial-branch=main")
    run_git(destination, "config", "user.name", "README Labs ingestion")
    run_git(destination, "config", "user.email", "ingestion@readme-labs.invalid")
    run_git(destination, "add", ".")
    run_git(destination, "commit", "--quiet", "-m", "Import managed snapshot")


def execute_github_action(
    *,
    yard: Path,
    plan_path: Path,
    execute: bool = False,
    gh_executable: str = "gh",
) -> dict[str, Any]:
    """Dry-run or explicitly execute private publication or owned archival."""

    plan = load_external_action_plan(plan_path)
    if plan["action"] not in {"publish_private", "archive_owned"}:
        raise ValueError("this executor only handles GitHub publication and archival")
    job_dir = _job_directory(yard, plan["job_id"], require_active=True)
    expected_plan = job_dir / "control/actions" / f"{plan['id']}.json"
    if plan_path.resolve() != expected_plan.resolve():
        raise PermissionError("action plan is not the registered job plan")
    job = _load_job_from_directory(job_dir)
    if job["status"] != "verified":
        raise ValueError("GitHub execution requires a still-verified job")
    if not execute:
        return {
            "action_id": plan["id"],
            "action": plan["action"],
            "dry_run": True,
            "parameters": plan["parameters"],
        }

    parameters = plan["parameters"]
    owner = parameters["owner"]
    repository_name = parameters["repository"]
    repository = f"{owner}/{repository_name}"
    before = _repository_view(gh_executable, repository)

    if plan["action"] == "publish_private":
        if before is not None:
            raise FileExistsError(f"GitHub target already exists: {repository}")
        checkout = job_dir / "checkout"
        history = parameters["history"]
        if history == "full":
            status = run_git(checkout, "status", "--porcelain")
            assert isinstance(status, str)
            if status.strip():
                raise ValueError("full-history publication requires a clean checkout")
            source = checkout
            temporary = None
        else:
            temporary = tempfile.TemporaryDirectory(prefix="readme-labs-publish-")
            source = Path(temporary.name) / "snapshot"
            _snapshot_repository(checkout, source)
        try:
            _run(
                [
                    gh_executable,
                    "repo",
                    "create",
                    repository,
                    "--private",
                    "--source",
                    source.as_posix(),
                    "--remote",
                    "origin",
                    "--push",
                ]
            )
        finally:
            if temporary is not None:
                temporary.cleanup()
        after = _repository_view(gh_executable, repository)
        if after is None or after.get("isPrivate") is not True:
            raise RuntimeError("new GitHub repository was not verified private")
        _verify_owned(after, owner)
        result = {
            "schema_version": 1,
            "action_id": plan["id"],
            "action": plan["action"],
            "status": "completed",
            "repository": repository,
            "private": True,
            "url": after.get("url"),
        }
    else:
        if before is None:
            raise FileNotFoundError(f"GitHub repository not found: {repository}")
        _verify_owned(before, owner)
        _run(
            [
                gh_executable,
                "api",
                "--method",
                "PATCH",
                f"repos/{repository}",
                "-F",
                "archived=true",
            ]
        )
        after = _repository_view(gh_executable, repository)
        if after is None or after.get("isArchived") is not True:
            raise RuntimeError("GitHub repository archival did not verify")
        _verify_owned(after, owner)
        result = {
            "schema_version": 1,
            "action_id": plan["id"],
            "action": plan["action"],
            "status": "completed",
            "repository": repository,
            "archived": True,
            "url": after.get("url"),
        }
    _write_action_result(job_dir, plan, result)
    return result


def _matching_selections(
    job_dir: Path, paths: list[dict[str, str]]
) -> list[dict[str, Any]]:
    selections = json.loads(
        (job_dir / "control/selections.json").read_text(encoding="utf-8")
    )["selections"]
    matched = []
    normalized_paths = [Path(item["path"]) for item in paths]
    for index, path in enumerate(normalized_paths):
        for other in normalized_paths[index + 1 :]:
            if path == other or path in other.parents or other in path.parents:
                raise ValueError("source cleanup paths must not overlap")
    for declared in paths:
        match = next(
            (
                item
                for item in selections
                if item["path"] == declared["path"]
                and item["sha256"] == declared["sha256"]
                and item["artifact_type"] == declared["artifact_type"]
            ),
            None,
        )
        if match is None:
            raise ValueError(
                f"cleanup path is not an exact ingestion selection: {declared}"
            )
        matched.append(match)
    return matched


def _verify_github_source_ownership(
    gh_executable: str, repository: str, expected_owner: str
) -> None:
    view = _repository_view(gh_executable, repository)
    if view is None:
        raise FileNotFoundError(f"GitHub source repository not found: {repository}")
    _verify_owned(view, expected_owner)


def _durable_selection_landed(
    *,
    job: dict[str, Any],
    selection: dict[str, Any],
    domain_repository: Path,
    parameters: dict[str, Any],
) -> bool:
    if job["admission"] is not None and job["admission"]["mode"] == "generated":
        for target in job["admission"]["targets"]:
            if target["kind"] != "intake_manifest":
                continue
            manifest_path = resolve_contained(domain_repository, target["path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            item = next(
                (
                    candidate
                    for candidate in manifest["items"]
                    if candidate["id"] == selection["id"]
                ),
                None,
            )
            if item is None:
                continue
            landing = item.get("landing")
            if landing is not None:
                landing_path = resolve_contained(
                    domain_repository, landing["path"]
                )
                actual = artifact_sha256(
                    landing_path, landing["artifact_type"]
                )
                if actual == selection["sha256"] == landing["sha256"]:
                    return True
            if "snapshot" not in item:
                continue
            snapshot = item["snapshot"]
            snapshot_path = resolve_contained(domain_repository, snapshot["path"])
            actual = artifact_sha256(snapshot_path, snapshot["artifact_type"])
            if actual == selection["sha256"] == snapshot["sha256"]:
                return True
    proofs = parameters.get("landing_proofs", [])
    proof = next(
        (item for item in proofs if item.get("selection_id") == selection["id"]),
        None,
    )
    if proof is None or proof.get("sha256") != selection["sha256"]:
        return False
    path = resolve_contained(domain_repository, proof["path"])
    return artifact_sha256(path, proof["artifact_type"]) == proof["sha256"]


def execute_source_cleanup(
    *,
    yard: Path,
    plan_path: Path,
    authorized_source: Path,
    domain_repository: Path,
    execute: bool = False,
    gh_executable: str = "gh",
) -> dict[str, Any]:
    """Physically delete exact owned source paths and settle their Git state."""

    plan = load_external_action_plan(plan_path)
    if plan["action"] != "source_cleanup":
        raise ValueError("source cleanup requires a source_cleanup plan")
    job_dir = _job_directory(yard, plan["job_id"], require_active=True)
    expected_plan = job_dir / "control/actions" / f"{plan['id']}.json"
    if plan_path.resolve() != expected_plan.resolve():
        raise PermissionError("cleanup plan is not the registered job plan")
    job = _load_job_from_directory(job_dir)
    if job["status"] != "verified" or job["source"]["ownership"] != "owned":
        raise PermissionError(
            "source cleanup requires a verified, explicitly owned job"
        )
    parameters = plan["parameters"]
    source = Path(parameters["source_repository"]).expanduser().resolve()
    if source != authorized_source.expanduser().resolve():
        raise PermissionError("authorized source path does not exactly match the plan")
    if (
        job["source"]["kind"] != "local_git"
        or source.as_posix() != job["source"]["locator"]
    ):
        raise PermissionError(
            "cleanup may act only on this job's original local Git source"
        )
    paths = parameters["paths"]
    matched = _matching_selections(job_dir, paths)
    if not execute:
        return {
            "action_id": plan["id"],
            "action": "source_cleanup",
            "dry_run": True,
            "source_repository": source.as_posix(),
            "paths": paths,
            "settlement": parameters["settlement"],
        }

    head, _, branch = git_identity(source)
    if head != parameters["expected_head"]:
        raise ValueError("source HEAD changed after cleanup planning")
    status = run_git(source, "status", "--porcelain")
    assert isinstance(status, str)
    if status.strip():
        raise ValueError("source cleanup requires a clean working tree")
    for declared, selection in zip(paths, matched, strict=True):
        artifact = resolve_contained(source, declared["path"])
        digest = artifact_sha256(artifact, declared["artifact_type"])
        if digest != declared["sha256"] or selection["source_state"] != "committed":
            raise ValueError("source cleanup content is not the committed selection")
        untracked = run_git(
            source,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            declared["path"],
        )
        assert isinstance(untracked, str)
        if untracked.strip():
            raise ValueError("source selection contains untracked files")

    migration_selections = [
        item for item in matched if item["preservation"] == "git_migration"
    ]
    destination_fingerprint = None
    destination = parameters.get("destination")
    migration_receipt_path = None
    if migration_selections:
        if len(migration_selections) != 1 or destination is None:
            raise ValueError(
                "v1 Git migration cleanup requires one destination contract"
            )
        if destination.get("ownership") != "owned":
            raise PermissionError(
                "snapshot-free Git migration requires an explicitly owned destination"
            )
        destination_repository = Path(destination["repository"]).resolve()
        destination_fingerprint = fingerprint_git_path(
            destination_repository,
            revision=destination["revision"],
            source_path=destination["path"],
            artifact_type=migration_selections[0]["artifact_type"],
        )
        if destination_fingerprint["sha256"] != migration_selections[0]["sha256"]:
            raise ValueError("destination does not contain the selected source content")
        migration_receipt_path = resolve_contained(
            domain_repository, parameters["migration_receipt"]
        )
        if migration_receipt_path.exists():
            raise FileExistsError(migration_receipt_path)
    for selection in matched:
        if selection["preservation"] == "git_migration":
            continue
        if selection["preservation"] not in {"selected", "replayable"}:
            raise ValueError(
                "source cleanup requires preserved bytes or an owned Git migration"
            )
        if not _durable_selection_landed(
            job=job,
            selection=selection,
            domain_repository=domain_repository,
            parameters=parameters,
        ):
            raise ValueError(
                f"selection has no verified durable landing: {selection['id']}"
            )

    checkout = job_dir / "checkout"
    if job["admission"] is None or not all(
        _verify_target(
            target,
            domain_repository=domain_repository,
            checkout=checkout,
        )
        for target in job["admission"]["targets"]
    ):
        raise ValueError("durable admission changed after ingestion verification")

    selected_paths = [item["path"] for item in paths]
    run_git(source, "rm", "-r", "--", *selected_paths)
    try:
        for item in paths:
            physical = source / item["path"]
            if physical.exists() or physical.is_symlink():
                raise RuntimeError(
                    "git rm did not physically remove the selected source path"
                )
        run_git(source, "commit", "-m", parameters["commit_message"])
    except Exception:
        run_git(
            source,
            "restore",
            "--source=HEAD",
            "--staged",
            "--worktree",
            "--",
            *selected_paths,
            check=False,
        )
        raise
    deletion_revision, _, _ = git_identity(source)
    settlement = parameters["settlement"]
    references: list[str] = []
    if settlement != "local_commit":
        try:
            github_repository = parameters["github_repository"]
            github_owner = parameters["github_owner"]
            _verify_github_source_ownership(
                gh_executable, github_repository, github_owner
            )
            remote = parameters.get("remote", "origin")
            push_branch = parameters.get("branch") or branch
            if not push_branch:
                raise ValueError("pushed cleanup requires a named branch")
            run_git(source, "push", remote, f"HEAD:{push_branch}")
            references.append(f"git:{github_repository}@{deletion_revision}")
            if settlement in {"pr_open", "merged"}:
                result = _run(
                    [
                        gh_executable,
                        "pr",
                        "create",
                        "--repo",
                        github_repository,
                        "--head",
                        push_branch,
                        "--base",
                        parameters["base"],
                        "--title",
                        parameters["title"],
                        "--body",
                        parameters["body"],
                    ]
                )
                pull_request = result.stdout.strip()
                references.append(pull_request)
                if settlement == "merged":
                    _run(
                        [
                            gh_executable,
                            "pr",
                            "merge",
                            pull_request,
                            "--merge",
                        ]
                    )
        except Exception as error:
            _write_action_result(
                job_dir,
                plan,
                {
                    "schema_version": 1,
                    "action_id": plan["id"],
                    "action": "source_cleanup",
                    "status": "incomplete",
                    "deletion_revision": deletion_revision,
                    "paths_absent": True,
                    "failed_step": "remote_settlement",
                    "error_type": type(error).__name__,
                },
            )
            raise

    migration_target = None
    if migration_selections:
        assert destination is not None and migration_receipt_path is not None
        receipt_relative = parameters["migration_receipt"]
        receipt = build_git_migration_receipt(
            receipt_id=parameters["migration_receipt_id"],
            source_repository=source,
            source_repository_id=job["source"]["repository_id"],
            source_revision=parameters["expected_head"],
            source_path=migration_selections[0]["path"],
            source_deletion_revision=deletion_revision,
            destination_repository=Path(destination["repository"]),
            destination_repository_id=destination["repository_id"],
            destination_revision=destination["revision"],
            destination_path=destination["path"],
            artifact_type=migration_selections[0]["artifact_type"],
            source_settlement=settlement,
            destination_settlement=destination["settlement"],
            source_ownership_basis=parameters.get(
                "source_ownership_basis", "explicit_owner_assertion"
            ),
            destination_ownership_basis=destination.get(
                "ownership_basis", "explicit_owner_assertion"
            ),
            references=references + destination.get("references", []),
            limitations=destination.get("limitations", []),
        )
        write_git_migration_receipt(migration_receipt_path, receipt)
        migration_target = _target(
            "migration_receipt", migration_receipt_path, domain_repository
        )
        job = _load_job_from_directory(job_dir)
        assert job["admission"] is not None and job["verification"] is not None
        job["admission"]["targets"].append(migration_target)
        job["verification"]["targets"].append(migration_target)
        _log(job, "git_migration_settled", receipt=receipt_relative)
        _store_job(job_dir, job)

    result = {
        "schema_version": 1,
        "action_id": plan["id"],
        "action": "source_cleanup",
        "status": "completed",
        "source_repository": job["source"]["repository_id"],
        "deletion_revision": deletion_revision,
        "paths_absent": True,
        "settlement": settlement,
        "references": references,
        "migration_target": migration_target,
    }
    _write_action_result(job_dir, plan, result)
    return result
