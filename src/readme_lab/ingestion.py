"""Managed source acquisition, admission, verification, and disposition."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.artifacts import artifact_sha256, resolve_contained, tree_sha256
from readme_lab.candidates import verify_candidate
from readme_lab.experiments import load_experiment_plan
from readme_lab.git_sources import (
    git_identity,
    is_git_repository,
    remote_records,
    repository_id_from_locator,
    run_git,
    sanitize_locator,
)
from readme_lab.intake import fingerprint_git_path, verify_intake_manifest
from readme_lab.migration import load_git_migration_receipt

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "intake"
YARD_MARKER = ".readme-labs-ingestion-yard"
JOB_MARKER = ".readme-labs-ingestion-job"
JOB_SCHEMA = "ingestion-job-v1.schema.json"
SELECTION_SCHEMA = "ingestion-selection-v1.schema.json"
INVENTORY_SCHEMA = "ingestion-inventory-v1.schema.json"
RECEIPT_SCHEMA = "finalization-receipt-v1.schema.json"
ACTION_SCHEMA = "external-action-plan-v1.schema.json"
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def _validate(value: dict[str, Any], schema_name: str) -> None:
    Draft202012Validator(
        _load_schema(schema_name), format_checker=FormatChecker()
    ).validate(value)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_id(value: str) -> None:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError(f"invalid ingestion id: {value}")


def initialize_ingestion_yard(domain_root: Path) -> Path:
    """Create a non-Git operational yard beside domain repositories."""

    domain_root = domain_root.expanduser().resolve()
    domain_root.mkdir(parents=True, exist_ok=True)
    if is_git_repository(domain_root):
        raise ValueError("the README domain container must not be a Git working tree")
    yard = domain_root / "ingestion"
    yard.mkdir(exist_ok=True)
    marker = yard / YARD_MARKER
    if marker.exists() and marker.read_text(encoding="utf-8").strip() != "1":
        raise ValueError("ingestion yard marker is invalid")
    marker.write_text("1\n", encoding="utf-8")
    for name in (
        "active",
        "completed",
        "quarantine",
        "archive/owned",
        "archive/external",
    ):
        (yard / name).mkdir(parents=True, exist_ok=True)
    return yard


def _validate_yard(yard: Path) -> Path:
    yard = yard.expanduser().resolve()
    if (yard / YARD_MARKER).read_text(encoding="utf-8").strip() != "1":
        raise ValueError("not a managed README Labs ingestion yard")
    return yard


def _job_directory(yard: Path, job_id: str, *, require_active: bool = False) -> Path:
    yard = _validate_yard(yard)
    _assert_id(job_id)
    roots = (
        [yard / "active"]
        if require_active
        else [
            yard / "active",
            yard / "completed",
            yard / "quarantine",
            yard / "archive/owned",
            yard / "archive/external",
        ]
    )
    matches = [root / job_id for root in roots if (root / job_id).is_dir()]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one managed job named {job_id}")
    job_dir = matches[0].resolve()
    if (job_dir / JOB_MARKER).read_text(encoding="utf-8").strip() != job_id:
        raise ValueError("ingestion job marker does not match job id")
    return job_dir


def _load_job_from_directory(job_dir: Path) -> dict[str, Any]:
    path = job_dir / "control/job.json"
    job = json.loads(path.read_text(encoding="utf-8"))
    _validate(job, JOB_SCHEMA)
    return job


def load_ingestion_job(yard: Path, job_id: str) -> dict[str, Any]:
    """Load a managed job from any lifecycle directory."""

    return _load_job_from_directory(_job_directory(yard, job_id))


def _store_job(job_dir: Path, job: dict[str, Any]) -> None:
    job["updated_at"] = _now()
    _validate(job, JOB_SCHEMA)
    _write_json(job_dir / "control/job.json", job)


def _log(job: dict[str, Any], event: str, **details: Any) -> None:
    job["action_log"].append({"at": _now(), "event": event, "details": details})


def _source_kind(source: str) -> tuple[str, Path | None]:
    candidate = Path(source).expanduser()
    if candidate.exists():
        candidate = candidate.resolve()
        if is_git_repository(candidate):
            return "local_git", candidate
        if candidate.is_dir():
            return "local_directory", candidate
        raise ValueError("local ingestion sources must be directories")
    return "git_url", None


def _git_repositories(root: Path) -> list[Path]:
    repositories = [root] if is_git_repository(root) else []
    for marker in root.rglob(".git"):
        repository = marker.parent
        if repository == root or not is_git_repository(repository):
            continue
        if not any(repository == existing for existing in repositories):
            repositories.append(repository)
    return sorted(repositories, key=lambda item: item.as_posix())


def _all_remote_records(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for repository in _git_repositories(root):
        relative = repository.relative_to(root).as_posix() or "."
        records.extend(remote_records(repository, repository_path=relative))
    return records


def _apply_remote_policy(root: Path, policy: str, job_id: str) -> None:
    for repository in _git_repositories(root):
        output = run_git(repository, "remote")
        assert isinstance(output, str)
        for name in [line for line in output.splitlines() if line]:
            fetch = run_git(repository, "remote", "get-url", name)
            push = run_git(repository, "remote", "get-url", "--push", name)
            assert isinstance(fetch, str)
            assert isinstance(push, str)
            safe_fetch = sanitize_locator(fetch.strip())
            safe_push = sanitize_locator(push.strip())
            run_git(repository, "remote", "set-url", name, safe_fetch)
            run_git(repository, "remote", "set-url", "--push", name, safe_push)
            if policy == "sever":
                run_git(repository, "remote", "remove", name)
            elif policy == "fetch_only":
                relative = repository.relative_to(root).as_posix() or "root"
                disabled = f"disabled://readme-labs/{job_id}/{relative}/{name}"
                run_git(repository, "remote", "set-url", "--push", name, disabled)
            elif policy != "preserve":
                raise ValueError(f"unsupported remote policy: {policy}")


def _copy_path(source: Path, destination: Path) -> None:
    if source.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)


def _copy_untracked(source: Path, checkout: Path, *, include_ignored: bool) -> None:
    arguments = ["ls-files", "-z", "--others", "--exclude-standard"]
    if include_ignored:
        arguments = ["ls-files", "-z", "--others", "--ignored", "--exclude-standard"]
    output = run_git(source, *arguments, binary=True)
    assert isinstance(output, bytes)
    for raw_path in [item for item in output.split(b"\0") if item]:
        relative = Path(os.fsdecode(raw_path))
        source_path = source / relative
        destination = checkout / relative
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        _copy_path(source_path, destination)


def _apply_local_workspace(
    source: Path, checkout: Path, *, include_ignored: bool
) -> None:
    staged = run_git(source, "diff", "--binary", "--cached", "HEAD", binary=True)
    assert isinstance(staged, bytes)
    if staged:
        run_git(
            checkout,
            "apply",
            "--index",
            "--binary",
            "-",
            binary=True,
            input_data=staged,
        )
    unstaged = run_git(source, "diff", "--binary", binary=True)
    assert isinstance(unstaged, bytes)
    if unstaged:
        run_git(
            checkout,
            "apply",
            "--binary",
            "-",
            binary=True,
            input_data=unstaged,
        )
    _copy_untracked(source, checkout, include_ignored=False)
    if include_ignored:
        _copy_untracked(source, checkout, include_ignored=True)


def _clone(
    source: str,
    checkout: Path,
    *,
    local: bool,
    lfs_policy: str,
    submodule_policy: str,
) -> None:
    command = ["git", "clone", "--no-hardlinks"]
    if local:
        command.append("--no-local")
    if submodule_policy == "fetch":
        command.append("--recurse-submodules")
    command.extend([source, checkout.as_posix()])
    environment = os.environ.copy()
    if lfs_policy == "pointers":
        environment["GIT_LFS_SKIP_SMUDGE"] = "1"
    subprocess.run(command, check=True, capture_output=True, text=True, env=environment)
    if lfs_policy == "fetch":
        subprocess.run(
            ["git", "lfs", "pull"],
            cwd=checkout,
            check=True,
            capture_output=True,
            text=True,
        )


def _git_status_paths(repository: Path, *arguments: str) -> list[str]:
    output = run_git(repository, *arguments, "-z", binary=True)
    assert isinstance(output, bytes)
    return sorted(os.fsdecode(item) for item in output.split(b"\0") if item)


def _inventory(job_id: str, checkout: Path, *, include_ignored: bool) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    symlinks: list[str] = []
    for current_root, directories, files in os.walk(checkout, followlinks=False):
        current = Path(current_root)
        directories[:] = [name for name in directories if name != ".git"]
        for name in list(directories) + files:
            path = current / name
            relative = path.relative_to(checkout).as_posix()
            if path.is_symlink():
                symlinks.append(relative)
            elif path.is_file():
                file_count += 1
                total_bytes += path.stat().st_size

    git_record = None
    if is_git_repository(checkout):
        head, tree, branch = git_identity(checkout)
        submodules: list[str] = []
        gitmodules = checkout / ".gitmodules"
        if gitmodules.is_file():
            output = subprocess.run(
                [
                    "git",
                    "config",
                    "-f",
                    gitmodules.as_posix(),
                    "--get-regexp",
                    r"^submodule\..*\.path$",
                ],
                cwd=checkout,
                check=False,
                capture_output=True,
                text=True,
            ).stdout
            submodules = sorted(
                line.split(maxsplit=1)[1]
                for line in output.splitlines()
                if len(line.split(maxsplit=1)) == 2
            )
        lfs_version = subprocess.run(
            ["git", "lfs", "version"],
            cwd=checkout,
            check=False,
            capture_output=True,
            text=True,
        )
        lfs_paths: list[str] = []
        if lfs_version.returncode == 0:
            lfs_output = subprocess.run(
                ["git", "lfs", "ls-files", "-n"],
                cwd=checkout,
                check=False,
                capture_output=True,
                text=True,
            ).stdout
            lfs_paths = sorted(line for line in lfs_output.splitlines() if line)
        git_record = {
            "head": head,
            "tree": tree,
            "branch": branch,
            "staged": _git_status_paths(checkout, "diff", "--name-only", "--cached"),
            "modified": _git_status_paths(checkout, "diff", "--name-only"),
            "untracked": _git_status_paths(
                checkout, "ls-files", "--others", "--exclude-standard"
            ),
            "ignored": _git_status_paths(
                checkout, "ls-files", "--others", "--ignored", "--exclude-standard"
            ),
            "submodules": submodules,
            "lfs": {
                "available": lfs_version.returncode == 0,
                "tracked_paths": lfs_paths,
            },
            "remotes": _all_remote_records(checkout),
        }
    inventory = {
        "schema_version": 1,
        "job_id": job_id,
        "observed_at": _now(),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "symlinks": sorted(symlinks),
        "ignored_files_policy": "included" if include_ignored else "excluded",
        "git": git_record,
    }
    _validate(inventory, INVENTORY_SCHEMA)
    return inventory


def begin_ingestion(
    *,
    domain_root: Path,
    job_id: str,
    source: str,
    remote_policy: str = "sever",
    ownership: str = "unknown",
    include_ignored: bool = False,
    lfs_policy: str = "pointers",
    submodule_policy: str = "record",
) -> dict[str, Any]:
    """Acquire one source into an isolated managed checkout and inventory it."""

    _assert_id(job_id)
    yard = initialize_ingestion_yard(domain_root)
    job_dir = yard / "active" / job_id
    if job_dir.exists():
        raise FileExistsError(job_dir)
    job_dir.mkdir()
    (job_dir / "control").mkdir()
    (job_dir / JOB_MARKER).write_text(f"{job_id}\n", encoding="utf-8")
    checkout = job_dir / "checkout"
    kind, local_path = _source_kind(source)

    try:
        if kind == "local_git":
            assert local_path is not None
            head, tree, branch = git_identity(local_path)
            original_remotes = _all_remote_records(local_path)
            dirty = bool(
                str(
                    run_git(local_path, "status", "--porcelain", "--untracked-files=no")
                ).strip()
            )
            untracked = bool(
                str(
                    run_git(
                        local_path,
                        "ls-files",
                        "--others",
                        "--exclude-standard",
                    )
                ).strip()
            )
            _clone(
                local_path.as_posix(),
                checkout,
                local=True,
                lfs_policy=lfs_policy,
                submodule_policy=submodule_policy,
            )
            _apply_local_workspace(
                local_path, checkout, include_ignored=include_ignored
            )
            locator = local_path.as_posix()
            mode = "clone"
        elif kind == "git_url":
            _clone(
                source,
                checkout,
                local=False,
                lfs_policy=lfs_policy,
                submodule_policy=submodule_policy,
            )
            head, tree, branch = git_identity(checkout)
            original_remotes = _all_remote_records(checkout)
            dirty = False
            untracked = False
            locator = sanitize_locator(source)
            mode = "clone"
        else:
            assert local_path is not None
            shutil.copytree(local_path, checkout, symlinks=True)
            head = tree = branch = None
            original_remotes = []
            dirty = untracked = False
            locator = local_path.as_posix()
            mode = "copy"

        if is_git_repository(checkout):
            _apply_remote_policy(checkout, remote_policy, job_id)
        inventory = _inventory(job_id, checkout, include_ignored=include_ignored)
        _write_json(job_dir / "control/inventory.json", inventory)
        selections = {"schema_version": 1, "job_id": job_id, "selections": []}
        _validate(selections, SELECTION_SCHEMA)
        _write_json(job_dir / "control/selections.json", selections)
        now = _now()
        repository_locator = (
            original_remotes[0]["fetch_url"] if original_remotes else locator
        )
        job = {
            "schema_version": 1,
            "id": job_id,
            "status": "acquired",
            "created_at": now,
            "updated_at": now,
            "source": {
                "kind": kind,
                "locator": locator,
                "repository_id": repository_id_from_locator(repository_locator),
                "ownership": ownership,
                "git_head": head,
                "git_tree": tree,
                "branch": branch,
                "dirty": dirty,
                "untracked": untracked,
            },
            "acquisition": {
                "mode": mode,
                "checkout": "checkout",
                "remote_policy": remote_policy,
                "include_ignored": include_ignored,
                "lfs_policy": lfs_policy,
                "submodule_policy": submodule_policy,
                "original_remotes": original_remotes,
            },
            "inventory": "control/inventory.json",
            "selections": "control/selections.json",
            "admission": None,
            "verification": None,
            "finalization": None,
            "action_log": [],
        }
        _log(job, "source_acquired", kind=kind, remote_policy=remote_policy)
        _store_job(job_dir, job)
        return job
    except Exception:
        failure = yard / "quarantine" / job_id
        if job_dir.exists() and not failure.exists():
            shutil.move(job_dir, failure)
        raise


def refresh_ingestion_inventory(*, yard: Path, job_id: str) -> dict[str, Any]:
    """Refresh inventory without changing the selected or admitted artifacts."""

    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] in {"verified", "finalized", "quarantined"}:
        raise ValueError("final lifecycle states have immutable inventories")
    inventory = _inventory(
        job_id,
        job_dir / "checkout",
        include_ignored=job["acquisition"]["include_ignored"],
    )
    _write_json(job_dir / job["inventory"], inventory)
    _log(job, "inventory_refreshed")
    _store_job(job_dir, job)
    return inventory


def _git_path_is_committed_and_clean(checkout: Path, relative: str) -> bool:
    object_path = "." if relative == "." else relative
    exists = (
        subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{object_path}"],
            cwd=checkout,
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )
    status = run_git(
        checkout,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        relative,
    )
    assert isinstance(status, str)
    return exists and not status.strip()


def _resolve_artifact(checkout: Path, relative: str) -> Path:
    if relative == ".":
        path = checkout.resolve()
    else:
        lexical = Path(os.path.abspath(checkout / relative))
        try:
            lexical.relative_to(checkout.resolve())
        except ValueError as error:
            raise ValueError(f"artifact path escapes checkout: {relative}") from error
        if lexical.is_symlink():
            raise ValueError("a symlink cannot be a selection root")
        path = resolve_contained(checkout, relative)
    if not path.exists() and not path.is_symlink():
        raise FileNotFoundError(path)
    if path.is_symlink():
        raise ValueError("a symlink cannot be a selection root")
    return path


def add_ingestion_selection(
    *,
    yard: Path,
    job_id: str,
    selection_id: str,
    source_path: str,
    role: str,
    preservation: str,
    context_paths: Iterable[str] = (),
    candidate_id: str | None = None,
    candidate_kind: str | None = None,
    candidate_format: str | None = None,
    candidate_entrypoint: str | None = None,
) -> dict[str, Any]:
    """Record an exact, content-addressed artifact selection."""

    _assert_id(selection_id)
    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] not in {"acquired", "selected"}:
        raise ValueError("selections are immutable after admission")
    checkout = job_dir / "checkout"
    artifact = _resolve_artifact(checkout, source_path)
    artifact_type = "tree" if artifact.is_dir() else "file"
    digest = artifact_sha256(artifact, artifact_type)
    normalized_context = []
    for context in context_paths:
        _resolve_artifact(checkout, context)
        normalized_context.append(context)
    if preservation == "replayable" and not normalized_context:
        raise ValueError("replayable selections require at least one context path")
    if preservation != "replayable" and normalized_context:
        raise ValueError("context paths are only valid for replayable selections")
    if preservation == "git_migration":
        if job["source"]["kind"] not in {"local_git", "git_url"}:
            raise ValueError("Git migration requires a Git source")
        if job["source"]["ownership"] != "owned":
            raise ValueError("Git migration requires an explicitly owned source")
        if not _git_path_is_committed_and_clean(checkout, source_path):
            raise ValueError("Git migration requires committed, clean source content")

    candidate_values = [
        candidate_id,
        candidate_kind,
        candidate_format,
        candidate_entrypoint,
    ]
    if any(value is not None for value in candidate_values) and not all(
        value is not None for value in candidate_values
    ):
        raise ValueError("candidate id, kind, format, and entrypoint are one contract")
    candidate = None
    if candidate_id is not None:
        _assert_id(candidate_id)
        candidate = {
            "id": candidate_id,
            "kind": candidate_kind,
            "format": candidate_format,
            "entrypoint": candidate_entrypoint,
        }

    source_state = "directory"
    if is_git_repository(checkout):
        source_state = (
            "committed"
            if _git_path_is_committed_and_clean(checkout, source_path)
            else "workspace"
        )
    path = job_dir / job["selections"]
    selections = json.loads(path.read_text(encoding="utf-8"))
    if any(item["id"] == selection_id for item in selections["selections"]):
        raise ValueError(f"duplicate selection id: {selection_id}")
    selection = {
        "id": selection_id,
        "path": source_path,
        "artifact_type": artifact_type,
        "role": role,
        "preservation": preservation,
        "sha256": digest,
        "source_state": source_state,
        "context_paths": normalized_context,
        "candidate": candidate,
    }
    selections["selections"].append(selection)
    _validate(selections, SELECTION_SCHEMA)
    _write_json(path, selections)
    job["status"] = "selected"
    _log(
        job,
        "selection_added",
        selection_id=selection_id,
        source_path=source_path,
        preservation=preservation,
    )
    _store_job(job_dir, job)
    return selection


def _copy_artifact(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git"),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)


def _source_record(
    job: dict[str, Any],
    checkout: Path,
    *,
    source_path: str,
    artifact_type: str,
    source_state: str,
) -> dict[str, Any]:
    if source_state == "committed":
        revision = job["source"]["git_head"]
        if revision is None:
            raise ValueError("committed selection has no Git revision")
        return fingerprint_git_path(
            checkout,
            revision=revision,
            source_path=source_path,
            artifact_type=artifact_type,
        )
    artifact = _resolve_artifact(checkout, source_path)
    return {
        "state": "workspace",
        "observed_at": _now(),
        "path": source_path,
        "artifact_type": artifact_type,
        "sha256": artifact_sha256(artifact, artifact_type),
    }


def _intake_kind(role: str) -> str:
    return {
        "readme_artifact": "readme_artifact",
        "skill": "skill",
        "skill_bundle": "skill_bundle",
        "research_content": "research_content",
        "research_method": "research_method",
        "research_protocol": "research_method",
        "research_data": "dataset",
        "evaluation_method": "evaluation_method",
        "trial_evidence": "trial_evidence",
        "whole_solution": "repository",
    }[role]


def _target(kind: str, path: Path, domain_repository: Path) -> dict[str, str]:
    relative = path.resolve().relative_to(domain_repository.resolve()).as_posix()
    return {"kind": kind, "path": relative, "sha256": _file_sha256(path)}


def _manifest_repository(job: dict[str, Any]) -> dict[str, Any]:
    remotes = job["acquisition"]["original_remotes"]
    remote = remotes[0]["fetch_url"] if remotes else None
    return {
        "repository_id": job["source"]["repository_id"],
        "remote": remote,
        "default_branch": job["source"]["branch"],
        "availability": "remote" if remote else "local_only",
    }


def _write_candidate(
    *,
    domain_repository: Path,
    manifest_path: Path,
    selection: dict[str, Any],
    source_artifact: Path,
    snapshot: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    candidate = selection["candidate"]
    assert candidate is not None
    candidate_root = domain_repository / "candidates" / candidate["id"]
    if candidate_root.exists():
        raise FileExistsError(candidate_root)
    artifact_root = candidate_root / "artifact"
    if source_artifact.is_dir():
        _copy_artifact(source_artifact, artifact_root)
        snapshot_path = artifact_root
        snapshot_type = "tree"
    else:
        artifact_root.mkdir(parents=True)
        snapshot_path = artifact_root / source_artifact.name
        _copy_artifact(source_artifact, snapshot_path)
        snapshot_type = "file"
    snapshot.update(
        {
            "path": snapshot_path.relative_to(domain_repository).as_posix(),
            "artifact_type": snapshot_type,
            "sha256": artifact_sha256(snapshot_path, snapshot_type),
        }
    )
    descriptor = {
        "schema_version": 1,
        "id": candidate["id"],
        "title": f"Ingested {selection['role']} candidate {candidate['id']}",
        "kind": candidate["kind"],
        "authority": "experimental_candidate_only",
        "storage": {
            "mode": "embedded",
            "artifact_root": "artifact",
            "tree_sha256": tree_sha256(artifact_root),
        },
        "source_bindings": [
            {
                "manifest": manifest_path.relative_to(domain_repository).as_posix(),
                "item_ids": [selection["id"]],
            }
        ],
        "entrypoints": [
            {
                "id": selection["id"],
                "path": candidate["entrypoint"],
                "format": candidate["format"],
            }
        ],
        "hypotheses": [
            f"The ingested {selection['role']} candidate may improve "
            "README-domain outcomes."
        ],
        "limitations": [
            "Ingestion makes this artifact testable; it does not promote it "
            "to a canonical capability."
        ],
    }
    descriptor_path = candidate_root / "candidate.json"
    _write_json(descriptor_path, descriptor)
    return snapshot, _target("candidate", descriptor_path, domain_repository)


def admit_ingestion(
    *,
    yard: Path,
    job_id: str,
    domain_repository: Path,
    manifest_id: str,
    title: str,
) -> dict[str, Any]:
    """Admit selected artifacts into intake and optional candidate records."""

    _assert_id(manifest_id)
    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] != "selected":
        raise ValueError("a generated admission requires selected artifacts")
    domain_repository = domain_repository.resolve()
    if not is_git_repository(domain_repository):
        raise ValueError("durable admission requires a Git domain repository")
    selections = json.loads((job_dir / job["selections"]).read_text(encoding="utf-8"))
    if any(
        selection["preservation"] == "git_migration"
        for selection in selections["selections"]
    ):
        raise ValueError(
            "Git migrations are admitted through settled migration receipts"
        )
    manifest_path = domain_repository / "intake/manifests" / f"{manifest_id}.json"
    if manifest_path.exists():
        raise FileExistsError(manifest_path)
    checkout = job_dir / "checkout"
    items: list[dict[str, Any]] = []
    relationships: list[dict[str, str]] = []
    candidate_targets: list[dict[str, str]] = []

    for selection in selections["selections"]:
        source_artifact = _resolve_artifact(checkout, selection["path"])
        source = _source_record(
            job,
            checkout,
            source_path=selection["path"],
            artifact_type=selection["artifact_type"],
            source_state=selection["source_state"],
        )
        item: dict[str, Any] = {
            "id": selection["id"],
            "kind": _intake_kind(selection["role"]),
            "source": source,
            "intake_mode": "reference",
            "status": "admitted",
            "authority": "evidence_only",
            "description": f"Managed ingestion selection for {selection['role']}.",
            "limitations": [
                f"Preservation policy: {selection['preservation']}.",
                "Admission does not establish correctness or canonical authority.",
            ],
        }
        if selection["preservation"] in {"selected", "replayable"}:
            snapshot: dict[str, Any] = {}
            if selection["candidate"] is not None:
                snapshot, candidate_target = _write_candidate(
                    domain_repository=domain_repository,
                    manifest_path=manifest_path,
                    selection=selection,
                    source_artifact=source_artifact,
                    snapshot=snapshot,
                )
                candidate_targets.append(candidate_target)
            else:
                snapshot_root = (
                    domain_repository
                    / "intake/snapshots"
                    / manifest_id
                    / selection["id"]
                )
                if source_artifact.is_file():
                    snapshot_path = snapshot_root / source_artifact.name
                else:
                    snapshot_path = snapshot_root
                _copy_artifact(source_artifact, snapshot_path)
                snapshot = {
                    "path": snapshot_path.relative_to(domain_repository).as_posix(),
                    "artifact_type": selection["artifact_type"],
                    "sha256": artifact_sha256(
                        snapshot_path, selection["artifact_type"]
                    ),
                }
            item["snapshot"] = snapshot
            item["intake_mode"] = "snapshot"
        elif selection["preservation"] == "archive":
            item["limitations"].append(
                "Full bytes remain in the managed operational archive rather "
                "than domain Git."
            )
        items.append(item)

        for index, context_path in enumerate(selection["context_paths"], start=1):
            context_artifact = _resolve_artifact(checkout, context_path)
            artifact_type = "tree" if context_artifact.is_dir() else "file"
            context_id = f"{selection['id']}-context-{index}"
            context_source = _source_record(
                job,
                checkout,
                source_path=context_path,
                artifact_type=artifact_type,
                source_state=(
                    "committed"
                    if is_git_repository(checkout)
                    and _git_path_is_committed_and_clean(checkout, context_path)
                    else "workspace"
                ),
            )
            context_root = (
                domain_repository / "intake/snapshots" / manifest_id / context_id
            )
            context_snapshot = (
                context_root / context_artifact.name
                if context_artifact.is_file()
                else context_root
            )
            _copy_artifact(context_artifact, context_snapshot)
            items.append(
                {
                    "id": context_id,
                    "kind": "repository",
                    "source": context_source,
                    "snapshot": {
                        "path": context_snapshot.relative_to(
                            domain_repository
                        ).as_posix(),
                        "artifact_type": artifact_type,
                        "sha256": artifact_sha256(context_snapshot, artifact_type),
                    },
                    "intake_mode": "snapshot",
                    "status": "admitted",
                    "authority": "evidence_only",
                    "description": f"Replay context for {selection['id']}.",
                    "limitations": ["Context is evidence, not candidate authority."],
                }
            )
            relationships.append(
                {
                    "from": context_id,
                    "relationship": "provides_replay_context_for",
                    "to": selection["id"],
                }
            )

    manifest = {
        "schema_version": 1,
        "id": manifest_id,
        "title": title,
        "observed_at": _now(),
        "source_repository": _manifest_repository(job),
        "items": items,
        "relationships": relationships,
        "limitations": [
            "The managed ingestion log remains local; this manifest records "
            "only landed domain material."
        ],
    }
    _write_json(manifest_path, manifest)
    verification = verify_intake_manifest(
        manifest_path, source_root=checkout, repository_root=domain_repository
    )
    if not verification["verified"]:
        raise ValueError("generated intake manifest did not verify")
    targets = [_target("intake_manifest", manifest_path, domain_repository)]
    targets.extend(candidate_targets)
    job["admission"] = {"mode": "generated", "targets": targets}
    job["status"] = "admitted"
    _log(job, "domain_admission_generated", manifest=targets[0]["path"])
    _store_job(job_dir, job)
    return job["admission"]


def link_existing_admission(
    *,
    yard: Path,
    job_id: str,
    domain_repository: Path,
    targets: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    """Link a job to already-landed durable records without duplicating bytes."""

    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] != "selected":
        raise ValueError("existing records may be linked only after selection")
    domain_repository = domain_repository.resolve()
    linked = []
    for kind, relative in targets:
        path = resolve_contained(domain_repository, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        linked.append({"kind": kind, "path": relative, "sha256": _file_sha256(path)})
    if not linked:
        raise ValueError("at least one landed target is required")
    job["admission"] = {"mode": "linked_existing", "targets": linked}
    job["status"] = "admitted"
    _log(job, "existing_admission_linked", targets=len(linked))
    _store_job(job_dir, job)
    return job["admission"]


def _verify_target(
    target: dict[str, str], *, domain_repository: Path, checkout: Path
) -> bool:
    path = resolve_contained(domain_repository, target["path"])
    if not path.is_file() or _file_sha256(path) != target["sha256"]:
        return False
    kind = target["kind"]
    if kind == "intake_manifest":
        return bool(
            verify_intake_manifest(
                path,
                source_root=checkout,
                repository_root=domain_repository,
            )["verified"]
        )
    if kind == "candidate":
        return bool(verify_candidate(path)["verified"])
    if kind == "experiment_plan":
        load_experiment_plan(path)
        return True
    if kind == "migration_receipt":
        load_git_migration_receipt(path)
        return True
    if kind in {"experiment_run", "other"}:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    return False


def verify_ingestion(
    *, yard: Path, job_id: str, domain_repository: Path
) -> dict[str, Any]:
    """Verify selected source bytes and every declared durable target."""

    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] != "admitted" or job["admission"] is None:
        raise ValueError("verification requires a completed admission")
    checkout = job_dir / "checkout"
    selections = json.loads((job_dir / job["selections"]).read_text(encoding="utf-8"))
    selection_results = []
    for selection in selections["selections"]:
        artifact = _resolve_artifact(checkout, selection["path"])
        digest = artifact_sha256(artifact, selection["artifact_type"])
        selection_results.append(
            {"id": selection["id"], "verified": digest == selection["sha256"]}
        )
    domain_repository = domain_repository.resolve()
    target_results = []
    for target in job["admission"]["targets"]:
        verified = _verify_target(
            target, domain_repository=domain_repository, checkout=checkout
        )
        target_results.append({**target, "verified": verified})
    if not all(item["verified"] for item in selection_results + target_results):
        raise ValueError("ingestion verification failed")
    verified_targets = [
        {key: value for key, value in item.items() if key != "verified"}
        for item in target_results
    ]
    job["verification"] = {
        "verified_at": _now(),
        "verified": True,
        "targets": verified_targets,
    }
    job["status"] = "verified"
    _log(
        job,
        "ingestion_verified",
        selections=len(selection_results),
        targets=len(target_results),
    )
    _store_job(job_dir, job)
    return {
        "job_id": job_id,
        "verified": True,
        "selections": selection_results,
        "targets": target_results,
    }


def quarantine_ingestion(*, yard: Path, job_id: str, reason: str) -> Path:
    """Move an unfinished job aside without interpreting it as rejection."""

    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    job["status"] = "quarantined"
    _log(job, "job_quarantined", reason=reason)
    _store_job(job_dir, job)
    destination = _validate_yard(yard) / "quarantine" / job_id
    if destination.exists():
        raise FileExistsError(destination)
    shutil.move(job_dir, destination)
    return destination


def _receipt_source(job: dict[str, Any]) -> dict[str, Any]:
    remotes = job["acquisition"]["original_remotes"]
    return {
        "kind": job["source"]["kind"],
        "repository_id": job["source"]["repository_id"],
        "git_head": job["source"]["git_head"],
        "git_tree": job["source"]["git_tree"],
        "remote": remotes[0]["fetch_url"] if remotes else None,
    }


def finalize_ingestion(
    *,
    yard: Path,
    job_id: str,
    domain_repository: Path,
    workspace_disposition: str,
    remote_disposition: str = "none",
    export_receipt: bool = True,
    migration_receipts: Iterable[str] = (),
    limitations: Iterable[str] = (),
) -> dict[str, Any]:
    """Settle a verified job and optionally export its durable receipt."""

    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] != "verified" or job["verification"] is None:
        raise ValueError("only a verified job may be finalized")
    selections = json.loads((job_dir / job["selections"]).read_text(encoding="utf-8"))
    if (
        any(item["preservation"] == "archive" for item in selections["selections"])
        and workspace_disposition != "archive_local"
    ):
        raise ValueError("archive preservation requires local archive disposition")
    migration_paths = list(migration_receipts)
    if remote_disposition == "owned_git_migration" and not migration_paths:
        raise ValueError("owned Git migration requires a settled migration receipt")
    if remote_disposition in {"publish_private", "archive_owned"}:
        actions = list((job_dir / "control/actions").glob("*.result.json"))
        if not actions:
            raise ValueError(
                "external remote disposition has no executed action result"
            )

    checkout = job_dir / "checkout"
    checkout_present = True
    destination: Path | None = None
    if workspace_disposition == "delete":
        if not checkout.resolve().is_relative_to(job_dir.resolve()):
            raise ValueError("managed checkout escaped its job directory")
        shutil.rmtree(checkout)
        checkout_present = False
        destination = _validate_yard(yard) / "completed" / job_id
    elif workspace_disposition == "archive_local":
        if is_git_repository(checkout):
            bundle = job_dir / "control/source.bundle"
            subprocess.run(
                ["git", "bundle", "create", bundle.as_posix(), "--all"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            )
        ownership = "owned" if job["source"]["ownership"] == "owned" else "external"
        destination = _validate_yard(yard) / "archive" / ownership / job_id
    elif workspace_disposition == "retain":
        destination = None
    else:
        raise ValueError(f"unsupported verified disposition: {workspace_disposition}")

    receipt = {
        "schema_version": 1,
        "id": f"{job_id}-finalization",
        "job_id": job_id,
        "completed_at": _now(),
        "source": _receipt_source(job),
        "remote_policy": job["acquisition"]["remote_policy"],
        "selections": [
            {
                "id": item["id"],
                "path": item["path"],
                "role": item["role"],
                "preservation": item["preservation"],
                "sha256": item["sha256"],
            }
            for item in selections["selections"]
        ],
        "admission_targets": job["verification"]["targets"],
        "workspace_disposition": workspace_disposition,
        "remote_disposition": remote_disposition,
        "checkout_present": checkout_present,
        "status": "completed",
        "migration_receipts": migration_paths,
        "limitations": list(limitations),
    }
    _validate(receipt, RECEIPT_SCHEMA)
    receipt_path = job_dir / "control/finalization-receipt.json"
    _write_json(receipt_path, receipt)
    job["finalization"] = "control/finalization-receipt.json"
    job["status"] = "finalized"
    _log(
        job,
        "job_finalized",
        workspace_disposition=workspace_disposition,
        remote_disposition=remote_disposition,
    )
    _store_job(job_dir, job)

    if export_receipt:
        domain_repository = domain_repository.resolve()
        exported = domain_repository / "intake/receipts" / f"{job_id}.json"
        if exported.exists():
            raise FileExistsError(exported)
        _write_json(exported, receipt)
    else:
        exported = None
    if destination is not None:
        if destination.exists():
            raise FileExistsError(destination)
        shutil.move(job_dir, destination)
    return {
        "job_id": job_id,
        "receipt": receipt,
        "exported_receipt": exported.as_posix() if exported else None,
        "job_directory": (destination or job_dir).as_posix(),
    }


def create_external_action_plan(
    *,
    yard: Path,
    job_id: str,
    action_id: str,
    action: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Persist a dry-run-first plan for external or destructive state changes."""

    _assert_id(action_id)
    job_dir = _job_directory(yard, job_id, require_active=True)
    job = _load_job_from_directory(job_dir)
    if job["status"] != "verified":
        raise ValueError("external actions require a verified ingestion job")
    required = {
        "publish_private": {"owner", "repository", "history"},
        "archive_owned": {"owner", "repository"},
        "source_cleanup": {
            "source_repository",
            "expected_head",
            "paths",
            "commit_message",
            "settlement",
        },
    }
    if action not in required:
        raise ValueError(f"unsupported external action: {action}")
    missing = required[action] - parameters.keys()
    if missing:
        raise ValueError(f"missing action parameters: {sorted(missing)}")
    if action == "publish_private" and parameters["history"] not in {
        "snapshot",
        "full",
    }:
        raise ValueError("private publication history must be snapshot or full")
    plan = {
        "schema_version": 1,
        "id": action_id,
        "job_id": job_id,
        "created_at": _now(),
        "action": action,
        "status": "planned",
        "preconditions": {
            "job_verified": True,
            "ownership_verification_required": True,
            "dry_run_first": True,
        },
        "parameters": parameters,
        "execution_requires_explicit_authorization": True,
    }
    _validate(plan, ACTION_SCHEMA)
    path = job_dir / "control/actions" / f"{action_id}.json"
    if path.exists():
        raise FileExistsError(path)
    _write_json(path, plan)
    _log(job, "external_action_planned", action=action, action_id=action_id)
    _store_job(job_dir, job)
    return plan


def load_external_action_plan(path: Path) -> dict[str, Any]:
    """Load one local guarded action plan."""

    plan = json.loads(path.read_text(encoding="utf-8"))
    _validate(plan, ACTION_SCHEMA)
    return plan
