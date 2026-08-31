from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from readme_lab.ingestion import (
    add_ingestion_selection,
    begin_ingestion,
    create_external_action_plan,
    finalize_ingestion,
    initialize_ingestion_yard,
    link_existing_admission,
    verify_ingestion,
)
from readme_lab.ingestion_actions import execute_github_action


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repository(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "--quiet", "--initial-branch=main")
    git(path, "config", "user.name", "README Labs test")
    git(path, "config", "user.email", "test@readme-labs.invalid")
    (path / "README.md").write_text("# Example\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "--quiet", "-m", "initial")
    return path


def make_verified_job(tmp_path: Path, job_id: str) -> tuple[Path, Path]:
    domain_root = tmp_path / f"domain-{job_id}"
    domain_root.mkdir()
    domain_repository = make_repository(domain_root / "readme-labs")
    yard = initialize_ingestion_yard(domain_root)
    source = make_repository(tmp_path / f"source-{job_id}")
    begin_ingestion(
        domain_root=domain_root,
        job_id=job_id,
        source=source.as_posix(),
        ownership="owned",
    )
    add_ingestion_selection(
        yard=yard,
        job_id=job_id,
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="reference",
    )
    target = domain_repository / "intake/landed.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"landed": true}\n', encoding="utf-8")
    link_existing_admission(
        yard=yard,
        job_id=job_id,
        domain_repository=domain_repository,
        targets=[("other", "intake/landed.json")],
    )
    verify_ingestion(yard=yard, job_id=job_id, domain_repository=domain_repository)
    return yard, domain_repository


def make_fake_gh(tmp_path: Path) -> tuple[Path, Path]:
    executable = tmp_path / "fake-gh"
    state = tmp_path / "fake-gh-state.json"
    executable.write_text(
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

state_path = Path(__file__).with_name('fake-gh-state.json')
args = sys.argv[1:]

if args[:2] == ['repo', 'view']:
    if not state_path.exists():
        raise SystemExit(1)
    print(state_path.read_text())
elif args[:2] == ['repo', 'create']:
    owner, name = args[2].split('/', 1)
    state_path.write_text(json.dumps({
        'name': name,
        'owner': {'login': owner},
        'isPrivate': '--private' in args,
        'isArchived': False,
        'viewerPermission': 'ADMIN',
        'url': f'https://github.com/{owner}/{name}'
    }))
elif args and args[0] == 'api':
    value = json.loads(state_path.read_text())
    value['isArchived'] = True
    state_path.write_text(json.dumps(value))
else:
    raise SystemExit(f'unexpected fake gh invocation: {args}')
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable, state


def test_private_publication_is_dry_run_first_and_verified_private(
    tmp_path: Path,
) -> None:
    yard, domain_repository = make_verified_job(tmp_path, "publish")
    gh, state = make_fake_gh(tmp_path)
    plan = create_external_action_plan(
        yard=yard,
        job_id="publish",
        action_id="publish-private",
        action="publish_private",
        parameters={
            "owner": "k421o",
            "repository": "ingested-example",
            "history": "snapshot",
        },
    )
    plan_path = yard / "active/publish/control/actions/publish-private.json"

    dry_run = execute_github_action(
        yard=yard, plan_path=plan_path, gh_executable=gh.as_posix()
    )
    assert dry_run["dry_run"] is True
    assert plan["execution_requires_explicit_authorization"] is True
    assert not state.exists()

    result = execute_github_action(
        yard=yard,
        plan_path=plan_path,
        execute=True,
        gh_executable=gh.as_posix(),
    )

    assert result["private"] is True
    assert result["repository"] == "k421o/ingested-example"
    assert (
        yard / "active/publish/control/actions/publish-private.result.json"
    ).is_file()
    final = finalize_ingestion(
        yard=yard,
        job_id="publish",
        domain_repository=domain_repository,
        workspace_disposition="delete",
        remote_disposition="publish_private",
    )
    assert final["receipt"]["remote_disposition"] == "publish_private"


def test_owned_repository_archival_checks_administration_and_result(
    tmp_path: Path,
) -> None:
    yard, _ = make_verified_job(tmp_path, "archive")
    gh, state = make_fake_gh(tmp_path)
    state.write_text(
        json.dumps(
            {
                "name": "old-source",
                "owner": {"login": "k421o"},
                "isPrivate": True,
                "isArchived": False,
                "viewerPermission": "ADMIN",
                "url": "https://github.com/k421o/old-source",
            }
        ),
        encoding="utf-8",
    )
    create_external_action_plan(
        yard=yard,
        job_id="archive",
        action_id="archive-owned",
        action="archive_owned",
        parameters={"owner": "k421o", "repository": "old-source"},
    )
    plan_path = yard / "active/archive/control/actions/archive-owned.json"

    result = execute_github_action(
        yard=yard,
        plan_path=plan_path,
        execute=True,
        gh_executable=gh.as_posix(),
    )

    assert result["archived"] is True
    assert json.loads(state.read_text())["isArchived"] is True


def test_owned_archival_refuses_repository_administered_by_another_owner(
    tmp_path: Path,
) -> None:
    yard, _ = make_verified_job(tmp_path, "wrong-owner")
    gh, state = make_fake_gh(tmp_path)
    state.write_text(
        json.dumps(
            {
                "name": "old-source",
                "owner": {"login": "someone-else"},
                "isPrivate": True,
                "isArchived": False,
                "viewerPermission": "ADMIN",
                "url": "https://github.com/someone-else/old-source",
            }
        ),
        encoding="utf-8",
    )
    create_external_action_plan(
        yard=yard,
        job_id="wrong-owner",
        action_id="archive-owned",
        action="archive_owned",
        parameters={"owner": "k421o", "repository": "old-source"},
    )
    plan_path = yard / "active/wrong-owner/control/actions/archive-owned.json"

    with pytest.raises(PermissionError, match="does not administer"):
        execute_github_action(
            yard=yard,
            plan_path=plan_path,
            execute=True,
            gh_executable=gh.as_posix(),
        )


def test_executor_refuses_an_unregistered_copy_of_an_action_plan(
    tmp_path: Path,
) -> None:
    yard, _ = make_verified_job(tmp_path, "registered-plan")
    gh, _ = make_fake_gh(tmp_path)
    create_external_action_plan(
        yard=yard,
        job_id="registered-plan",
        action_id="publish-private",
        action="publish_private",
        parameters={
            "owner": "k421o",
            "repository": "ingested-example",
            "history": "snapshot",
        },
    )
    registered = yard / "active/registered-plan/control/actions/publish-private.json"
    copied = tmp_path / "copied-plan.json"
    copied.write_bytes(registered.read_bytes())

    with pytest.raises(PermissionError, match="registered job plan"):
        execute_github_action(
            yard=yard,
            plan_path=copied,
            gh_executable=gh.as_posix(),
        )


def test_source_cleanup_plan_rejects_repository_root(tmp_path: Path) -> None:
    yard, _ = make_verified_job(tmp_path, "root-cleanup")

    with pytest.raises(ValueError, match="repository-root"):
        create_external_action_plan(
            yard=yard,
            job_id="root-cleanup",
            action_id="clean-root",
            action="source_cleanup",
            parameters={
                "source_repository": "/tmp/example",
                "expected_head": "a" * 40,
                "paths": [
                    {
                        "path": ".",
                        "artifact_type": "tree",
                        "sha256": "b" * 64,
                    }
                ],
                "commit_message": "clean",
                "settlement": "local_commit",
            },
        )
