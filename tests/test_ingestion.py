from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from readme_lab.candidates import verify_candidate
from readme_lab.ingestion import (
    add_ingestion_selection,
    admit_ingestion,
    begin_ingestion,
    create_external_action_plan,
    finalize_ingestion,
    initialize_ingestion_yard,
    link_existing_admission,
    load_finalization_receipt,
    load_ingestion_job,
    quarantine_ingestion,
    refresh_ingestion_inventory,
    verify_ingestion,
)
from readme_lab.ingestion_actions import execute_source_cleanup
from readme_lab.intake import verify_intake_manifest
from readme_lab.migration import load_git_migration_receipt
from readme_lab.readme_artifacts import load_artifact_record, record_id_for_digest


def git(repository: Path, *arguments: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=check,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_bytes(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout


def make_repository(path: Path, *, initial_file: str = "README.md") -> Path:
    path.mkdir(parents=True)
    git(path, "init", "--quiet", "--initial-branch=main")
    git(path, "config", "user.name", "README Labs test")
    git(path, "config", "user.email", "test@readme-labs.invalid")
    (path / initial_file).parent.mkdir(parents=True, exist_ok=True)
    (path / initial_file).write_text("initial\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "--quiet", "-m", "initial")
    return path


def make_domain(tmp_path: Path) -> tuple[Path, Path, Path]:
    domain_root = tmp_path / "readme-domain"
    domain_root.mkdir()
    domain_repository = make_repository(domain_root / "readme-labs")
    yard = initialize_ingestion_yard(domain_root)
    assert not (domain_root / ".git").exists()
    return domain_root, domain_repository, yard


def test_checked_in_reademe_temp_controller_receipt_proves_landed_targets() -> None:
    receipt = load_finalization_receipt(
        Path("intake/receipts/reademe-temp-controller-v1.json")
    )

    assert receipt["source"] == {
        "git_head": "30775d179343b47e24ae0c7b543332d86802f486",
        "git_tree": "37cd2a380443f0dd9acbe1f1f5834082733a9c9b",
        "kind": "local_git",
        "remote": None,
        "repository_id": "local:reademe-temp",
    }
    assert receipt["remote_policy"] == "sever"
    assert receipt["workspace_disposition"] == "delete"
    assert receipt["checkout_present"] is False
    assert receipt["status"] == "completed"
    assert all(item["preservation"] == "reference" for item in receipt["selections"])
    assert {item["id"] for item in receipt["selections"]} == {
        "current-main-readme",
        "notebooklm-research-record",
        "related-research-documents",
        "notebooklm-extraction-method",
        "current-main-modular-templates",
        "modular-readme-forward-test",
    }
    assert {target["kind"] for target in receipt["admission_targets"]} == {
        "intake_manifest",
        "candidate",
        "experiment_plan",
        "experiment_run",
    }
    receipt_revision = "b10ff9c1ad032c6861b7d03463f52d9ac5d8e208"
    for target in receipt["admission_targets"]:
        historical_bytes = git_bytes(
            Path.cwd(), "show", f"{receipt_revision}:{target['path']}"
        )
        assert hashlib.sha256(historical_bytes).hexdigest() == target["sha256"]


def test_domain_container_must_not_be_a_git_repository(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "repository")

    with pytest.raises(ValueError, match="must not be a Git"):
        initialize_ingestion_yard(repository)


def test_local_git_acquisition_preserves_workspace_and_severs_remotes(
    tmp_path: Path,
) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "source", initial_file="staged.txt")
    (source / "unstaged.txt").write_text("old\n", encoding="utf-8")
    (source / ".gitignore").write_text("*.secret\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "fixtures")
    git(
        source,
        "remote",
        "add",
        "upstream",
        "https://embedded-token@github.com/example/source.git?credential=bad",
    )
    (source / "staged.txt").write_text("staged change\n", encoding="utf-8")
    git(source, "add", "staged.txt")
    (source / "unstaged.txt").write_text("unstaged change\n", encoding="utf-8")
    (source / "new.txt").write_text("untracked\n", encoding="utf-8")
    (source / "private.secret").write_text("ignored\n", encoding="utf-8")

    job = begin_ingestion(
        domain_root=domain_root,
        job_id="dirty-source",
        source=source.as_posix(),
        remote_policy="sever",
        ownership="owned",
    )
    checkout = yard / "active/dirty-source/checkout"
    inventory = json.loads(
        (yard / "active/dirty-source/control/inventory.json").read_text()
    )

    assert job["source"]["dirty"] is True
    assert job["source"]["untracked"] is True
    assert job["acquisition"]["original_remotes"] == [
        {
            "repository_path": ".",
            "name": "upstream",
            "fetch_url": "https://github.com/example/source.git",
            "push_url": "https://github.com/example/source.git",
        }
    ]
    assert git(checkout, "remote") == ""
    assert (checkout / "staged.txt").read_text() == "staged change\n"
    assert (checkout / "unstaged.txt").read_text() == "unstaged change\n"
    assert (checkout / "new.txt").read_text() == "untracked\n"
    assert not (checkout / "private.secret").exists()
    assert inventory["ignored_files_policy"] == "excluded"
    assert inventory["git"]["staged"] == ["staged.txt"]
    assert inventory["git"]["modified"] == ["unstaged.txt"]
    assert inventory["git"]["untracked"] == ["new.txt"]
    assert (
        os.stat(source / ".git/objects").st_ino
        != os.stat(checkout / ".git/objects").st_ino
    )


def test_fetch_only_disables_push_and_git_url_acquisition_works(
    tmp_path: Path,
) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "remote-source")

    job = begin_ingestion(
        domain_root=domain_root,
        job_id="file-url",
        source=source.as_uri(),
        remote_policy="fetch_only",
    )
    checkout = yard / "active/file-url/checkout"

    assert job["source"]["kind"] == "git_url"
    assert git(checkout, "remote", "get-url", "origin") == source.as_uri()
    assert git(checkout, "remote", "get-url", "--push", "origin").startswith(
        "disabled://readme-labs/file-url/"
    )


def test_non_git_source_severs_nested_repository_remotes(tmp_path: Path) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = tmp_path / "mixed-directory"
    source.mkdir()
    nested = make_repository(source / "nested")
    git(nested, "remote", "add", "origin", "https://token@github.com/acme/nested.git")

    job = begin_ingestion(
        domain_root=domain_root,
        job_id="nested-source",
        source=source.as_posix(),
        remote_policy="sever",
    )

    assert job["source"]["kind"] == "local_directory"
    assert job["acquisition"]["original_remotes"][0]["fetch_url"] == (
        "https://github.com/acme/nested.git"
    )
    assert git(yard / "active/nested-source/checkout/nested", "remote") == ""


def test_selected_skill_lands_as_candidate_then_managed_checkout_is_deleted(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "skill-source")
    skill = source / ".agents/skills/example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Example skill\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "add skill")
    begin_ingestion(
        domain_root=domain_root,
        job_id="example-skill",
        source=source.as_posix(),
        remote_policy="sever",
        ownership="owned",
    )
    add_ingestion_selection(
        yard=yard,
        job_id="example-skill",
        selection_id="example-skill",
        source_path=".agents/skills/example",
        role="skill",
        preservation="selected",
        candidate_id="example-skill-candidate",
        candidate_kind="skill",
        candidate_format="codex_skill",
        candidate_entrypoint=".",
    )
    admission = admit_ingestion(
        yard=yard,
        job_id="example-skill",
        domain_repository=domain_repository,
        manifest_id="example-skill-intake",
        title="Example skill intake",
    )

    assert [target["kind"] for target in admission["targets"]] == [
        "intake_manifest",
        "candidate",
    ]
    manifest = domain_repository / "intake/manifests/example-skill-intake.json"
    descriptor = domain_repository / "candidates/example-skill-candidate/candidate.json"
    assert verify_intake_manifest(
        manifest,
        source_root=yard / "active/example-skill/checkout",
        repository_root=domain_repository,
    )["verified"]
    assert verify_candidate(descriptor)["verified"]
    assert verify_ingestion(
        yard=yard,
        job_id="example-skill",
        domain_repository=domain_repository,
    )["verified"]

    result = finalize_ingestion(
        yard=yard,
        job_id="example-skill",
        domain_repository=domain_repository,
        workspace_disposition="delete",
    )

    assert result["receipt"]["checkout_present"] is False
    assert not (yard / "completed/example-skill/checkout").exists()
    assert (source / ".agents/skills/example/SKILL.md").is_file()
    assert (domain_repository / "intake/receipts/example-skill.json").is_file()
    assert load_ingestion_job(yard, "example-skill")["status"] == "finalized"


def test_selected_readme_moves_directly_to_its_final_artifact_record(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "readme-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="readme-landing",
        source=source.as_posix(),
        ownership="owned",
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="readme-landing",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )

    admission = admit_ingestion(
        yard=yard,
        job_id="readme-landing",
        domain_repository=domain_repository,
        manifest_id="readme-landing",
        title="README landing",
    )

    record_id = record_id_for_digest(selection["sha256"])
    record_dir = domain_repository / "readmes/records" / record_id
    checkout_readme = yard / "active/readme-landing/checkout/README.md"
    manifest_path = domain_repository / "intake/manifests/readme-landing.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    item = manifest["items"][0]

    assert [target["kind"] for target in admission["targets"]] == [
        "intake_manifest",
        "readme_record",
    ]
    assert manifest["schema_version"] == 2
    assert item["intake_mode"] == "landed"
    assert "snapshot" not in item
    assert item["landing"] == {
        "artifact_type": "file",
        "managed_source_absent": True,
        "managed_source_path": "README.md",
        "path": f"readmes/records/{record_id}/artifact.md",
        "record_id": record_id,
        "sha256": selection["sha256"],
        "transferred_at": load_artifact_record(record_dir)["capture"][
            "captured_at"
        ],
    }
    assert not checkout_readme.exists()
    assert (record_dir / "artifact.md").read_text(encoding="utf-8") == "initial\n"
    assert not (domain_repository / "intake/snapshots/readme-landing").exists()
    assert source.joinpath("README.md").is_file()
    assert verify_intake_manifest(
        manifest_path,
        source_root=yard / "active/readme-landing/checkout",
        repository_root=domain_repository,
    )["verified"]
    verification = verify_ingestion(
        yard=yard,
        job_id="readme-landing",
        domain_repository=domain_repository,
    )
    assert verification["selections"] == [
        {
            "id": "readme",
            "source_absent": True,
            "destination_verified": True,
            "verified": True,
        }
    ]


def test_readme_landing_rolls_back_when_manifest_verification_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "rollback-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="readme-rollback",
        source=source.as_posix(),
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="readme-rollback",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    monkeypatch.setattr(
        "readme_lab.ingestion.verify_intake_manifest",
        lambda *args, **kwargs: {"verified": False},
    )

    with pytest.raises(ValueError, match="did not verify"):
        admit_ingestion(
            yard=yard,
            job_id="readme-rollback",
            domain_repository=domain_repository,
            manifest_id="readme-rollback",
            title="README rollback",
        )

    checkout_readme = yard / "active/readme-rollback/checkout/README.md"
    record_id = record_id_for_digest(selection["sha256"])
    assert checkout_readme.read_text(encoding="utf-8") == "initial\n"
    assert not (domain_repository / "readmes/records" / record_id).exists()
    assert not (
        domain_repository / "intake/manifests/readme-rollback.json"
    ).exists()


def test_admission_rejects_selection_drift_before_moving_readme(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "drift-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="readme-drift",
        source=source.as_posix(),
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="readme-drift",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    checkout_readme = yard / "active/readme-drift/checkout/README.md"
    checkout_readme.write_text("changed after selection\n", encoding="utf-8")

    with pytest.raises(ValueError, match="changed before admission"):
        admit_ingestion(
            yard=yard,
            job_id="readme-drift",
            domain_repository=domain_repository,
            manifest_id="readme-drift",
            title="README drift",
        )

    assert checkout_readme.read_text(encoding="utf-8") == (
        "changed after selection\n"
    )
    assert not (
        domain_repository
        / "readmes/records"
        / record_id_for_digest(selection["sha256"])
    ).exists()
    assert not (domain_repository / "intake/manifests/readme-drift.json").exists()
    assert load_ingestion_job(yard, "readme-drift")["status"] == "selected"


def test_identical_readme_selections_converge_on_one_durable_body(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "same-body-source")
    (source / "docs/README.md").parent.mkdir()
    (source / "docs/README.md").write_text("initial\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "add identical README")
    begin_ingestion(
        domain_root=domain_root,
        job_id="same-body",
        source=source.as_posix(),
    )
    first = add_ingestion_selection(
        yard=yard,
        job_id="same-body",
        selection_id="root-readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    second = add_ingestion_selection(
        yard=yard,
        job_id="same-body",
        selection_id="docs-readme",
        source_path="docs/README.md",
        role="readme_artifact",
        preservation="selected",
    )

    admit_ingestion(
        yard=yard,
        job_id="same-body",
        domain_repository=domain_repository,
        manifest_id="same-body",
        title="Same README body",
    )

    assert first["sha256"] == second["sha256"]
    assert len(list((domain_repository / "readmes/records").glob("*/artifact.md"))) == 1
    checkout = yard / "active/same-body/checkout"
    assert not (checkout / "README.md").exists()
    assert not (checkout / "docs/README.md").exists()


def test_overlapping_selection_paths_are_rejected(tmp_path: Path) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "overlap-source")
    (source / "docs/guide.md").parent.mkdir()
    (source / "docs/guide.md").write_text("guide\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "add docs")
    begin_ingestion(
        domain_root=domain_root,
        job_id="overlap",
        source=source.as_posix(),
    )
    add_ingestion_selection(
        yard=yard,
        job_id="overlap",
        selection_id="docs",
        source_path="docs",
        role="research_content",
        preservation="selected",
    )

    with pytest.raises(ValueError, match="paths overlap"):
        add_ingestion_selection(
            yard=yard,
            job_id="overlap",
            selection_id="guide",
            source_path="docs/guide.md",
            role="research_content",
            preservation="selected",
        )


def test_plugin_tooling_automation_and_script_selections_remain_explicit(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "mixed-source")
    artifacts = {
        "plugin": ("plugin", "plugin/plugin.json", "codex_plugin"),
        "tooling": ("tooling", "tools/check.py", "python_tool"),
        "automation": (
            "automation",
            ".github/workflows/readme.yml",
            "github_actions_workflow",
        ),
        "script": ("script", "scripts/rewrite.py", "python_script"),
    }
    for role, (_, relative, _) in artifacts.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{role}\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "add mixed README tooling")

    begin_ingestion(
        domain_root=domain_root,
        job_id="mixed-artifacts",
        source=source.as_posix(),
        remote_policy="sever",
        ownership="external",
    )
    for role, (candidate_kind, relative, candidate_format) in artifacts.items():
        add_ingestion_selection(
            yard=yard,
            job_id="mixed-artifacts",
            selection_id=f"example-{role}",
            source_path=relative,
            role=role,
            preservation="selected",
            candidate_id=f"example-{role}-candidate",
            candidate_kind=candidate_kind,
            candidate_format=candidate_format,
            candidate_entrypoint=Path(relative).name,
        )

    admission = admit_ingestion(
        yard=yard,
        job_id="mixed-artifacts",
        domain_repository=domain_repository,
        manifest_id="mixed-artifacts-intake",
        title="Mixed README-related artifact intake",
    )
    manifest = json.loads(
        (domain_repository / "intake/manifests/mixed-artifacts-intake.json").read_text()
    )

    assert {item["kind"] for item in manifest["items"]} == set(artifacts)
    assert [target["kind"] for target in admission["targets"]].count("candidate") == 4
    for role in artifacts:
        descriptor = (
            domain_repository
            / f"candidates/example-{role}-candidate/candidate.json"
        )
        candidate = json.loads(descriptor.read_text())
        assert candidate["kind"] == role
        assert verify_candidate(descriptor)["verified"] is True

    assert verify_ingestion(
        yard=yard,
        job_id="mixed-artifacts",
        domain_repository=domain_repository,
    )["verified"] is True


def test_replayable_selection_preserves_explicit_context_only(tmp_path: Path) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "research-source")
    (source / "protocol.md").write_text("method\n", encoding="utf-8")
    (source / "data.csv").write_text("value\n1\n", encoding="utf-8")
    (source / "unselected.md").write_text("do not copy\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "research")
    begin_ingestion(
        domain_root=domain_root,
        job_id="protocol",
        source=source.as_posix(),
    )
    add_ingestion_selection(
        yard=yard,
        job_id="protocol",
        selection_id="protocol",
        source_path="protocol.md",
        role="research_protocol",
        preservation="replayable",
        context_paths=["data.csv"],
    )
    admit_ingestion(
        yard=yard,
        job_id="protocol",
        domain_repository=domain_repository,
        manifest_id="protocol-intake",
        title="Protocol intake",
    )
    manifest = json.loads(
        (domain_repository / "intake/manifests/protocol-intake.json").read_text()
    )

    assert [item["id"] for item in manifest["items"]] == [
        "protocol",
        "protocol-context-1",
    ]
    assert not list(
        (domain_repository / "intake/snapshots/protocol-intake").rglob("unselected.md")
    )


def test_non_git_directory_can_be_archived_but_archive_policy_cannot_delete(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = tmp_path / "notes"
    source.mkdir()
    (source / "method.md").write_text("method\n", encoding="utf-8")
    begin_ingestion(
        domain_root=domain_root,
        job_id="local-notes",
        source=source.as_posix(),
        ownership="external",
    )
    add_ingestion_selection(
        yard=yard,
        job_id="local-notes",
        selection_id="method",
        source_path="method.md",
        role="research_method",
        preservation="archive",
    )
    admit_ingestion(
        yard=yard,
        job_id="local-notes",
        domain_repository=domain_repository,
        manifest_id="local-notes-intake",
        title="Local notes intake",
    )
    verify_ingestion(
        yard=yard,
        job_id="local-notes",
        domain_repository=domain_repository,
    )

    with pytest.raises(ValueError, match="requires local archive"):
        finalize_ingestion(
            yard=yard,
            job_id="local-notes",
            domain_repository=domain_repository,
            workspace_disposition="delete",
        )
    result = finalize_ingestion(
        yard=yard,
        job_id="local-notes",
        domain_repository=domain_repository,
        workspace_disposition="archive_local",
    )

    assert Path(result["job_directory"]) == yard / "archive/external/local-notes"
    assert (yard / "archive/external/local-notes/checkout/method.md").is_file()


def test_unfinished_job_can_only_be_quarantined_not_finalized(tmp_path: Path) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = tmp_path / "notes"
    source.mkdir()
    (source / "note.md").write_text("note\n", encoding="utf-8")
    begin_ingestion(
        domain_root=domain_root,
        job_id="unfinished",
        source=source.as_posix(),
    )

    with pytest.raises(ValueError, match="verified"):
        finalize_ingestion(
            yard=yard,
            job_id="unfinished",
            domain_repository=domain_repository,
            workspace_disposition="delete",
        )
    destination = quarantine_ingestion(
        yard=yard, job_id="unfinished", reason="method requires review"
    )

    assert destination == yard / "quarantine/unfinished"
    assert load_ingestion_job(yard, "unfinished")["status"] == "quarantined"


def test_finalization_preflights_receipt_collision_before_deleting_checkout(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "collision-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="collision",
        source=source.as_posix(),
    )
    add_ingestion_selection(
        yard=yard,
        job_id="collision",
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
        job_id="collision",
        domain_repository=domain_repository,
        targets=[("other", "intake/landed.json")],
    )
    verify_ingestion(yard=yard, job_id="collision", domain_repository=domain_repository)
    receipt = domain_repository / "intake/receipts/collision.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("collision\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        finalize_ingestion(
            yard=yard,
            job_id="collision",
            domain_repository=domain_repository,
            workspace_disposition="delete",
        )

    assert (yard / "active/collision/checkout/README.md").is_file()


def test_finalization_reverifies_landed_body_before_deleting_checkout(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "finalization-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="finalization-reverify",
        source=source.as_posix(),
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="finalization-reverify",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    admit_ingestion(
        yard=yard,
        job_id="finalization-reverify",
        domain_repository=domain_repository,
        manifest_id="finalization-reverify",
        title="Finalization reverify",
    )
    verify_ingestion(
        yard=yard,
        job_id="finalization-reverify",
        domain_repository=domain_repository,
    )
    record = (
        domain_repository
        / "readmes/records"
        / record_id_for_digest(selection["sha256"])
    )
    (record / "artifact.md").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="changed after ingestion verification"):
        finalize_ingestion(
            yard=yard,
            job_id="finalization-reverify",
            domain_repository=domain_repository,
            workspace_disposition="delete",
        )

    assert (yard / "active/finalization-reverify/checkout").is_dir()
    assert load_ingestion_job(yard, "finalization-reverify")["status"] == "verified"


def test_owned_git_migration_cleans_source_physically_and_uses_history_receipt(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "source")
    skill = source / "skills/example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Migrated skill\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "add migratable skill")
    source_revision = git(source, "rev-parse", "HEAD")
    destination = make_repository(tmp_path / "destination")
    destination_skill = destination / "domain/example"
    destination_skill.mkdir(parents=True)
    (destination_skill / "SKILL.md").write_text("# Migrated skill\n", encoding="utf-8")
    git(destination, "add", ".")
    git(destination, "commit", "--quiet", "-m", "land migrated skill")
    destination_revision = git(destination, "rev-parse", "HEAD")

    begin_ingestion(
        domain_root=domain_root,
        job_id="owned-migration",
        source=source.as_posix(),
        ownership="owned",
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="owned-migration",
        selection_id="example-skill",
        source_path="skills/example",
        role="skill",
        preservation="git_migration",
    )
    landed = domain_repository / "intake/landed-migration.json"
    landed.parent.mkdir(parents=True)
    landed.write_text('{"landed": true}\n', encoding="utf-8")
    link_existing_admission(
        yard=yard,
        job_id="owned-migration",
        domain_repository=domain_repository,
        targets=[("other", "intake/landed-migration.json")],
    )
    verify_ingestion(
        yard=yard,
        job_id="owned-migration",
        domain_repository=domain_repository,
    )
    parameters = {
        "source_repository": source.as_posix(),
        "expected_head": source_revision,
        "paths": [
            {
                "path": selection["path"],
                "artifact_type": selection["artifact_type"],
                "sha256": selection["sha256"],
            }
        ],
        "commit_message": "Remove migrated example skill",
        "settlement": "local_commit",
        "destination": {
            "repository": destination.as_posix(),
            "repository_id": "owned:destination",
            "ownership": "owned",
            "revision": destination_revision,
            "path": "domain/example",
            "settlement": "local_commit",
            "references": [],
            "limitations": [],
        },
        "migration_receipt": "intake/migrations/owned-migration.json",
        "migration_receipt_id": "owned-migration",
    }
    plan = create_external_action_plan(
        yard=yard,
        job_id="owned-migration",
        action_id="clean-source",
        action="source_cleanup",
        parameters=parameters,
    )
    plan_path = yard / "active/owned-migration/control/actions/clean-source.json"

    dry_run = execute_source_cleanup(
        yard=yard,
        plan_path=plan_path,
        authorized_source=source,
        domain_repository=domain_repository,
    )
    assert dry_run["dry_run"] is True
    assert (source / "skills/example/SKILL.md").is_file()
    assert plan["execution_requires_explicit_authorization"] is True

    receipt_path = domain_repository / "intake/migrations/owned-migration.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text("collision\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        execute_source_cleanup(
            yard=yard,
            plan_path=plan_path,
            authorized_source=source,
            domain_repository=domain_repository,
            execute=True,
        )
    assert (source / "skills/example/SKILL.md").is_file()
    assert git(source, "status", "--short") == ""
    receipt_path.unlink()

    result = execute_source_cleanup(
        yard=yard,
        plan_path=plan_path,
        authorized_source=source,
        domain_repository=domain_repository,
        execute=True,
    )

    assert result["paths_absent"] is True
    assert not (source / "skills/example").exists()
    assert "skills/example" not in git(source, "ls-tree", "-r", "--name-only", "HEAD")
    receipt = load_git_migration_receipt(receipt_path)
    assert receipt["duplicate_snapshot_retained"] is False
    assert receipt["source"]["revision"] == source_revision
    assert receipt["source"]["deletion_revision"] == result["deletion_revision"]
    assert receipt["destination"]["revision"] == destination_revision
    assert not (domain_repository / "intake/snapshots/owned-migration").exists()

    final = finalize_ingestion(
        yard=yard,
        job_id="owned-migration",
        domain_repository=domain_repository,
        workspace_disposition="delete",
        remote_disposition="owned_git_migration",
        migration_receipts=["intake/migrations/owned-migration.json"],
    )
    assert final["receipt"]["remote_disposition"] == "owned_git_migration"


def test_refresh_inventory_does_not_reselect_changed_bytes(tmp_path: Path) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="refresh",
        source=source.as_posix(),
    )
    checkout = yard / "active/refresh/checkout"
    (checkout / "later.txt").write_text("later\n", encoding="utf-8")

    inventory = refresh_ingestion_inventory(yard=yard, job_id="refresh")

    assert inventory["git"]["untracked"] == ["later.txt"]


def test_symlinks_are_inventoried_and_cannot_silently_enter_a_snapshot(
    tmp_path: Path,
) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = tmp_path / "linked-notes"
    source.mkdir()
    (source / "target.md").write_text("target\n", encoding="utf-8")
    (source / "link.md").symlink_to("target.md")
    begin_ingestion(
        domain_root=domain_root,
        job_id="symlinked",
        source=source.as_posix(),
    )
    inventory = json.loads(
        (yard / "active/symlinked/control/inventory.json").read_text()
    )

    assert inventory["symlinks"] == ["link.md"]
    with pytest.raises(ValueError, match="symlink cannot be a selection root"):
        add_ingestion_selection(
            yard=yard,
            job_id="symlinked",
            selection_id="linked-file",
            source_path="link.md",
            role="research_content",
            preservation="selected",
        )


def test_git_migration_rejects_dirty_or_untracked_source_content(
    tmp_path: Path,
) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "dirty-migration")
    (source / "README.md").write_text("changed\n", encoding="utf-8")
    begin_ingestion(
        domain_root=domain_root,
        job_id="dirty-migration",
        source=source.as_posix(),
        ownership="owned",
    )

    with pytest.raises(ValueError, match="committed, clean"):
        add_ingestion_selection(
            yard=yard,
            job_id="dirty-migration",
            selection_id="readme",
            source_path="README.md",
            role="readme_artifact",
            preservation="git_migration",
        )


def test_candidate_cannot_be_declared_without_preserved_candidate_bytes(
    tmp_path: Path,
) -> None:
    domain_root, _, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "candidate-reference")
    begin_ingestion(
        domain_root=domain_root,
        job_id="candidate-reference",
        source=source.as_posix(),
    )

    with pytest.raises(ValueError, match="require selected or replayable"):
        add_ingestion_selection(
            yard=yard,
            job_id="candidate-reference",
            selection_id="readme",
            source_path="README.md",
            role="readme_artifact",
            preservation="reference",
            candidate_id="readme-candidate",
            candidate_kind="other",
            candidate_format="markdown",
            candidate_entrypoint="README.md",
        )


def test_failed_cleanup_commit_restores_physically_deleted_source(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "hooked-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="hooked-cleanup",
        source=source.as_posix(),
        ownership="owned",
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="hooked-cleanup",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    admit_ingestion(
        yard=yard,
        job_id="hooked-cleanup",
        domain_repository=domain_repository,
        manifest_id="hooked-cleanup",
        title="Hook rollback fixture",
    )
    verify_ingestion(
        yard=yard,
        job_id="hooked-cleanup",
        domain_repository=domain_repository,
    )
    parameters = {
        "source_repository": source.as_posix(),
        "expected_head": git(source, "rev-parse", "HEAD"),
        "paths": [
            {
                "path": selection["path"],
                "artifact_type": selection["artifact_type"],
                "sha256": selection["sha256"],
            }
        ],
        "commit_message": "Remove landed README",
        "settlement": "local_commit",
    }
    create_external_action_plan(
        yard=yard,
        job_id="hooked-cleanup",
        action_id="clean-source",
        action="source_cleanup",
        parameters=parameters,
    )
    hook = source / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)

    with pytest.raises(subprocess.CalledProcessError):
        execute_source_cleanup(
            yard=yard,
            plan_path=(
                yard / "active/hooked-cleanup/control/actions/clean-source.json"
            ),
            authorized_source=source,
            domain_repository=domain_repository,
            execute=True,
        )

    assert (source / "README.md").read_text() == "initial\n"
    assert git(source, "status", "--short") == ""


def test_source_cleanup_reverifies_artifact_package_before_deleting_source(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "cleanup-reverify-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="cleanup-reverify",
        source=source.as_posix(),
        ownership="owned",
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="cleanup-reverify",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="selected",
    )
    admit_ingestion(
        yard=yard,
        job_id="cleanup-reverify",
        domain_repository=domain_repository,
        manifest_id="cleanup-reverify",
        title="Cleanup reverify fixture",
    )
    verify_ingestion(
        yard=yard,
        job_id="cleanup-reverify",
        domain_repository=domain_repository,
    )
    create_external_action_plan(
        yard=yard,
        job_id="cleanup-reverify",
        action_id="clean-source",
        action="source_cleanup",
        parameters={
            "source_repository": source.as_posix(),
            "expected_head": git(source, "rev-parse", "HEAD"),
            "paths": [
                {
                    "path": selection["path"],
                    "artifact_type": selection["artifact_type"],
                    "sha256": selection["sha256"],
                }
            ],
            "commit_message": "Remove landed README",
            "settlement": "local_commit",
        },
    )
    record = (
        domain_repository
        / "readmes/records"
        / record_id_for_digest(selection["sha256"])
    )
    (record / "record.json").unlink()

    with pytest.raises(ValueError, match="changed after ingestion verification"):
        execute_source_cleanup(
            yard=yard,
            plan_path=(
                yard / "active/cleanup-reverify/control/actions/clean-source.json"
            ),
            authorized_source=source,
            domain_repository=domain_repository,
            execute=True,
        )

    assert (source / "README.md").read_text(encoding="utf-8") == "initial\n"
    assert git(source, "status", "--short") == ""


def test_source_cleanup_cannot_treat_a_reference_record_as_landed_bytes(
    tmp_path: Path,
) -> None:
    domain_root, domain_repository, yard = make_domain(tmp_path)
    source = make_repository(tmp_path / "reference-source")
    begin_ingestion(
        domain_root=domain_root,
        job_id="reference-cleanup",
        source=source.as_posix(),
        ownership="owned",
    )
    selection = add_ingestion_selection(
        yard=yard,
        job_id="reference-cleanup",
        selection_id="readme",
        source_path="README.md",
        role="readme_artifact",
        preservation="reference",
    )
    record = domain_repository / "intake/reference.json"
    record.parent.mkdir(parents=True)
    record.write_text('{"reference": true}\n', encoding="utf-8")
    link_existing_admission(
        yard=yard,
        job_id="reference-cleanup",
        domain_repository=domain_repository,
        targets=[("other", "intake/reference.json")],
    )
    verify_ingestion(
        yard=yard,
        job_id="reference-cleanup",
        domain_repository=domain_repository,
    )
    create_external_action_plan(
        yard=yard,
        job_id="reference-cleanup",
        action_id="clean-source",
        action="source_cleanup",
        parameters={
            "source_repository": source.as_posix(),
            "expected_head": git(source, "rev-parse", "HEAD"),
            "paths": [
                {
                    "path": selection["path"],
                    "artifact_type": selection["artifact_type"],
                    "sha256": selection["sha256"],
                }
            ],
            "commit_message": "Unsafe cleanup",
            "settlement": "local_commit",
        },
    )

    with pytest.raises(ValueError, match="preserved bytes"):
        execute_source_cleanup(
            yard=yard,
            plan_path=(
                yard / "active/reference-cleanup/control/actions/clean-source.json"
            ),
            authorized_source=source,
            domain_repository=domain_repository,
            execute=True,
        )

    assert (source / "README.md").is_file()
    assert git(source, "status", "--short") == ""
