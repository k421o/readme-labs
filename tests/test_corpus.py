from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from readme_lab.corpus import (
    git_blob_sha,
    load_manifest,
    load_observations,
    summarize_observations,
)
from readme_lab.inspect import inspect_readme

PILOT = Path("corpus/manifests/pilot-high-exposure-v1.jsonl")
FIXTURE = Path("tests/fixtures/readme-with-conventional-sections.md")
PILOT_OBSERVATIONS = Path("corpus/observations/pilot-high-exposure-v1.jsonl")


def test_pilot_manifest_is_valid_pinned_and_explicitly_non_normative() -> None:
    items = load_manifest(PILOT)
    assert len(items) == 16
    assert len({item["revision"] for item in items}) == 16
    assert all(item["role_assignment"] == "annotated" for item in items)
    assert all(
        item["role_annotation"]
        == {
            "protocol": "bootstrap-role-annotation",
            "protocol_version": "1.0.0",
            "annotator": "bootstrap-corpus-author",
        }
        for item in items
    )
    assert all(item["selection"]["quality_label"] is False for item in items)
    assert all(
        item["selection"]["training_prevalence_claim"] == "none" for item in items
    )


def test_git_blob_sha_matches_documented_git_object_algorithm() -> None:
    assert git_blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_committed_pilot_observations_match_manifest_sources() -> None:
    manifest = load_manifest(PILOT)
    observations = load_observations(PILOT_OBSERVATIONS)

    assert len(observations) == len(manifest) == 16
    expected = {
        (item["repository"], item["revision"], item["path"]) for item in manifest
    }
    actual = {
        (
            item["source"]["repository"],
            item["source"]["revision"],
            item["source"]["path"],
        )
        for item in observations
    }
    assert actual == expected
    assert all(item["schema_version"] == "2.0.0" for item in observations)
    assert all(item["role"]["assignment"] == "annotated" for item in observations)
    assert all("annotation" in item["derivation"] for item in observations)


def test_summarize_observations_reports_descriptive_counts(tmp_path: Path) -> None:
    timestamp = datetime(2026, 8, 29, 12, tzinfo=UTC)
    first = inspect_readme(
        FIXTURE,
        repository="example/one",
        revision="one",
        role="published_package",
        observed_at=timestamp,
    )
    second = inspect_readme(
        FIXTURE,
        repository="example/two",
        revision="two",
        role="cli_tool",
        observed_at=timestamp,
    )
    observations = tmp_path / "observations.jsonl"
    observations.write_text(
        json.dumps(first) + "\n" + json.dumps(second) + "\n",
        encoding="utf-8",
    )

    summary = summarize_observations(observations)
    assert summary["sample_count"] == 2
    assert summary["role_counts"] == {"cli_tool": 1, "published_package": 1}
    assert summary["category_signal_rates"]["identity"] == 1.0
    assert summary["category_signal_rates"]["definition_purpose"] == 0.0
    assert "not a population prevalence" in summary["interpretation"]
