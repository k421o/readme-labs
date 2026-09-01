from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
from pathlib import Path

import pytest

AUDIT_REPOSITORY = runpy.run_path("scripts/check_readme_bodies.py")["audit_repository"]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def tracked_repository(tmp_path: Path, files: dict[str, str]) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=repository,
        check=True,
    )
    for relative, content in files.items():
        write(repository / relative, content)
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    return repository


def commit(repository: Path, message: str = "fixture") -> str:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=readme-labs",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
        ],
        cwd=repository,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def write_upstream(repository: Path, *, source_revision: str) -> None:
    upstream = {
        "artifact_kind": "test_adapter",
        "generated_by": "scripts/build_test_product.py",
        "sources": [
            {
                "source": "capabilities/example",
                "destination": "skills/example",
                "source_revision": source_revision,
                "source_sha256": tree_sha256(repository / "capabilities/example"),
            }
        ],
    }
    write(
        repository / "products/example/UPSTREAM.json",
        json.dumps(upstream),
    )
    subprocess.run(
        ["git", "add", "products/example/UPSTREAM.json"],
        cwd=repository,
        check=True,
    )


def test_embedded_record_body_seeds_renamed_duplicate_detection(
    tmp_path: Path,
) -> None:
    body = "# Captured subject\n\nExact README bytes.\n"
    record = {
        "artifact": {
            "media_type": "text/markdown",
            "storage": {"mode": "embedded", "path": "artifact.md"},
        }
    }
    repository = tracked_repository(
        tmp_path,
        {
            "readmes/records/rm-example/record.json": json.dumps(record),
            "readmes/records/rm-example/artifact.md": body,
            "intake/snapshots/renamed-subject.txt": body,
        },
    )

    violations = AUDIT_REPOSITORY(repository)

    assert len(violations) == 1
    assert "has 2 durable owners" in violations[0]
    assert "readmes/records/rm-example/artifact.md" in violations[0]
    assert "intake/snapshots/renamed-subject.txt" in violations[0]


def test_products_prefix_does_not_allow_an_unclassified_duplicate(
    tmp_path: Path,
) -> None:
    body = "# Product subject\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": body,
            "products/example/README.md": body,
        },
    )

    violations = AUDIT_REPOSITORY(repository)

    assert len(violations) == 1
    assert "has 2 durable owners" in violations[0]


def test_exact_upstream_source_destination_pair_is_generated_distribution(
    tmp_path: Path,
) -> None:
    body = "# Generated distribution subject\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": body,
            "products/example/skills/example/README.md": body,
        },
    )
    source_revision = commit(repository)
    write_upstream(repository, source_revision=source_revision)

    assert AUDIT_REPOSITORY(repository) == []


def test_file_source_provenance_is_verified_and_exempted(tmp_path: Path) -> None:
    body = "# Generated file distribution subject\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": body,
            "products/example/skills/example/README.md": body,
        },
    )
    source_revision = commit(repository)
    source = repository / "capabilities/example/README.md"
    upstream = {
        "artifact_kind": "test_adapter",
        "generated_by": "scripts/build_test_product.py",
        "sources": [
            {
                "source": "capabilities/example/README.md",
                "destination": "skills/example/README.md",
                "source_revision": source_revision,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
    }
    write(
        repository / "products/example/UPSTREAM.json",
        json.dumps(upstream),
    )
    subprocess.run(
        ["git", "add", "products/example/UPSTREAM.json"],
        cwd=repository,
        check=True,
    )

    assert AUDIT_REPOSITORY(repository) == []


def test_upstream_pair_does_not_allow_an_unlisted_third_copy(tmp_path: Path) -> None:
    body = "# One source and one generated destination\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": body,
            "products/example/skills/example/README.md": body,
            "experiments/durable-copy.md": body,
        },
    )
    source_revision = commit(repository)
    write_upstream(repository, source_revision=source_revision)

    violations = AUDIT_REPOSITORY(repository)

    assert len(violations) == 1
    assert "has 2 durable owners" in violations[0]
    assert "experiments/durable-copy.md" in violations[0]


def test_generated_provenance_rejects_current_source_digest_mismatch(
    tmp_path: Path,
) -> None:
    body = "# Generated distribution subject\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": body,
            "products/example/skills/example/README.md": body,
        },
    )
    source_revision = commit(repository)
    write_upstream(repository, source_revision=source_revision)
    upstream_path = repository / "products/example/UPSTREAM.json"
    upstream = json.loads(upstream_path.read_text(encoding="utf-8"))
    upstream["sources"][0]["source_sha256"] = "b" * 64
    write(upstream_path, json.dumps(upstream))

    violations = AUDIT_REPOSITORY(repository)

    assert any(
        "generated source digest does not match current source" in violation
        for violation in violations
    )


def test_generated_provenance_rejects_revision_with_different_source(
    tmp_path: Path,
) -> None:
    original = "# Original generated subject\n"
    current = "# Current generated subject\n"
    repository = tracked_repository(
        tmp_path,
        {
            "capabilities/example/README.md": original,
            "products/example/skills/example/README.md": original,
        },
    )
    old_revision = commit(repository, "old source")
    write(repository / "capabilities/example/README.md", current)
    write(repository / "products/example/skills/example/README.md", current)
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    commit(repository, "current source")
    write_upstream(repository, source_revision=old_revision)

    violations = AUDIT_REPOSITORY(repository)

    assert any(
        "generated source revision does not match declared digest" in violation
        for violation in violations
    )


@pytest.mark.parametrize("suffix", ["json", "jsonl"])
def test_complete_body_inside_nested_json_string_is_rejected(
    tmp_path: Path, suffix: str
) -> None:
    body = "# Logged subject\n\nThe entire README must not enter a log.\n"
    event = {"item": {"result": {"aggregated_output": body + "more output\n"}}}
    serialized = json.dumps(event) + ("\n" if suffix == "jsonl" else "")
    repository = tracked_repository(
        tmp_path,
        {
            "README.md": body,
            f"experiments/runs/example/events.{suffix}": serialized,
        },
    )

    violations = AUDIT_REPOSITORY(repository)

    assert any(
        "complete README body embedded in JSON string" in violation
        and f"events.{suffix}" in violation
        and "$.item.result.aggregated_output" in violation
        for violation in violations
    )
    assert any(
        "durable event output must be a digest object" in violation
        for violation in violations
    )


@pytest.mark.parametrize("suffix", ["json", "jsonl"])
def test_raw_event_output_is_rejected_even_without_a_complete_readme(
    tmp_path: Path, suffix: str
) -> None:
    event = {"item": {"result": {"stdout": "partial diagnostic"}}}
    serialized = json.dumps(event) + ("\n" if suffix == "jsonl" else "")
    repository = tracked_repository(
        tmp_path,
        {
            "README.md": "# Subject\n",
            f"evals/runs/example/events.{suffix}": serialized,
        },
    )

    violations = AUDIT_REPOSITORY(repository)

    assert violations == [
        "durable event output must be a digest object: "
        f"evals/runs/example/events.{suffix}"
        + (":1" if suffix == "jsonl" else "")
        + " $.item.result.stdout"
    ]


def test_digest_only_event_and_stderr_outputs_are_accepted(tmp_path: Path) -> None:
    digest = {
        "sha256": hashlib.sha256(b"private output").hexdigest(),
        "byte_length": len(b"private output"),
    }
    repository = tracked_repository(
        tmp_path,
        {
            "README.md": "# Subject\n",
            "evals/runs/example/events.jsonl": json.dumps(
                {"item": {"aggregated_output": digest}}
            )
            + "\n",
            "evals/runs/example/stderr.log": json.dumps(digest) + "\n",
        },
    )

    assert AUDIT_REPOSITORY(repository) == []


def test_raw_stderr_is_rejected(tmp_path: Path) -> None:
    repository = tracked_repository(
        tmp_path,
        {
            "README.md": "# Subject\n",
            "evals/runs/example/stderr.log": "private diagnostics\n",
        },
    )

    violations = AUDIT_REPOSITORY(repository)

    assert len(violations) == 1
    assert "durable stderr must be a digest object" in violations[0]


def test_partial_body_reference_is_not_a_second_body(tmp_path: Path) -> None:
    body = "# Subject\n\nA sufficiently distinctive complete README body.\n"
    repository = tracked_repository(
        tmp_path,
        {
            "README.md": body,
            "experiments/run.json": json.dumps(
                {"summary": "The subject starts with # Subject."}
            ),
        },
    )

    assert AUDIT_REPOSITORY(repository) == []
