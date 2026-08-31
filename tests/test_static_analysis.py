from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from readme_lab.corpus import git_blob_sha, load_manifest
from readme_lab.static_analysis import (
    load_static_analysis_run,
    load_static_analyzer,
    markdown_structure_v1,
    run_corpus_static_analysis,
    run_document_static_analysis,
)

ANALYZER = Path(
    "experiments/analyzers/markdown-structure-v1/analyzer.json"
)


def test_initial_static_analyzer_is_evidence_only_and_non_prescriptive() -> None:
    analyzer = load_static_analyzer(ANALYZER)

    assert analyzer["authority"] == "evidence_only"
    assert analyzer["supported_modes"] == [
        "document_diagnostic",
        "corpus_characterization",
    ]
    assert {rule["id"] for rule in analyzer["rules"]} == {
        "heading-level-jump",
        "empty-heading",
        "duplicate-heading-text",
        "image-missing-alt",
    }
    assert all("section" not in rule["id"] for rule in analyzer["rules"])
    feedback_rules = {
        rule["id"] for rule in analyzer["rules"] if rule["feedback_default"]
    }
    assert "duplicate-heading-text" not in feedback_rules


def test_static_run_contract_has_no_quality_verdict_or_acceptance_gate() -> None:
    schema = json.loads(
        Path("experiments/schemas/static-analysis-run-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    serialized = json.dumps(schema)

    assert '"automated_authority"' in serialized
    assert '"hypothesis_disposition"' in serialized
    assert '"quality_score"' not in serialized
    assert '"verdict"' not in serialized
    assert '"passed"' not in serialized


def test_static_analyzer_rejects_duplicate_rule_ids(tmp_path: Path) -> None:
    source = json.loads(ANALYZER.read_text(encoding="utf-8"))
    source["rules"].append(source["rules"][0])
    (tmp_path / "rules.md").write_text("rules\n", encoding="utf-8")
    path = tmp_path / "analyzer.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="rule ids must be unique"):
        load_static_analyzer(path)


def test_markdown_structure_analyzer_localizes_each_initial_rule(
    tmp_path: Path,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Example\n\n"
        "### Details\n\n"
        "##\n\n"
        "## details\n\n"
        "![](diagram.png)\n",
        encoding="utf-8",
    )

    result = markdown_structure_v1(readme, recorded_path="README.md")

    assert result["result"] == "completed"
    assert [item["rule_id"] for item in result["diagnostics"]] == [
        "heading-level-jump",
        "empty-heading",
        "duplicate-heading-text",
        "image-missing-alt",
    ]
    assert [item["location"]["line"] for item in result["diagnostics"]] == [
        3,
        5,
        7,
        9,
    ]


def test_document_run_binds_diagnostics_to_exact_generated_readme(
    tmp_path: Path,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Example\n\n### Use\n", encoding="utf-8")
    output = tmp_path / "run.json"

    run = run_document_static_analysis(
        ANALYZER,
        readme_path=readme,
        output=output,
        run_id="generated-readme-static-v1",
        subject_id="generated-readme",
        source_kind="generated",
        recorded_path="README.md",
        repository="local:example",
        revision="working-tree",
        recorded_at=datetime(2026, 8, 30, tzinfo=UTC),
    )

    assert load_static_analysis_run(output, analyzer_path=ANALYZER) == run
    assert run["mode"] == "document_diagnostic"
    assert run["configuration"] == {
        "profile": "feedback",
        "enabled_rule_ids": [
            "empty-heading",
            "heading-level-jump",
            "image-missing-alt",
        ],
    }
    assert run["automated_authority"] == "evidence_only"
    assert run["hypothesis_disposition"] == "not_decided"
    assert run["summary"]["diagnostics_by_rule"] == {"heading-level-jump": 1}
    assert "verdict" not in run


def test_corpus_mode_reuses_pinned_manifest_as_substrate(tmp_path: Path) -> None:
    templates = load_manifest(
        Path("corpus/manifests/pilot-high-exposure-v1.jsonl")
    )[:2]
    contents = [b"# One\n\n## Use\n", b"# Two\n\n### Deep\n"]
    manifest = tmp_path / "manifest.jsonl"
    cache = tmp_path / "cache"
    items = []
    for index, (template, content) in enumerate(zip(templates, contents, strict=True)):
        item = {**template}
        item["sample_id"] = f"sample-{index + 1}"
        item["repository"] = f"example/repository-{index + 1}"
        item["revision"] = str(index + 1) * 40
        item["path"] = "README.md"
        item["blob_sha"] = git_blob_sha(content)
        item["source_url"] = f"https://example.invalid/{index + 1}/README.md"
        item["collected_at"] = "2026-08-30T00:00:00Z"
        sample = cache / item["sample_id"]
        sample.mkdir(parents=True)
        (sample / "README.md").write_bytes(content)
        items.append(item)
    manifest.write_text(
        "".join(json.dumps(item) + "\n" for item in items), encoding="utf-8"
    )
    output = tmp_path / "corpus-run.json"

    run = run_corpus_static_analysis(
        ANALYZER,
        manifest_path=manifest,
        cache_dir=cache,
        output=output,
        run_id="small-corpus-static-v1",
        recorded_at=datetime(2026, 8, 30, tzinfo=UTC),
    )

    assert load_static_analysis_run(output, analyzer_path=ANALYZER) == run
    assert run["mode"] == "corpus_characterization"
    assert run["configuration"]["profile"] == "all"
    assert run["summary"] == {
        "subject_count": 2,
        "completed_subject_count": 2,
        "incomplete_subject_count": 0,
        "diagnostic_count": 1,
        "diagnostics_by_rule": {"heading-level-jump": 1},
    }
    assert [item["source"]["kind"] for item in run["subjects"]] == [
        "corpus_sample",
        "corpus_sample",
    ]


def test_static_analysis_refuses_to_overwrite_a_run(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Example\n", encoding="utf-8")
    output = tmp_path / "run.json"
    output.write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        run_document_static_analysis(
            ANALYZER,
            readme_path=readme,
            output=output,
            run_id="collision",
            subject_id="readme",
            source_kind="local",
        )

    assert output.read_text(encoding="utf-8") == "preserve me\n"


def test_repeated_heading_rule_is_characterized_but_not_default_feedback(
    tmp_path: Path,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Example\n\n## Use\n\n## Use\n", encoding="utf-8")

    feedback = run_document_static_analysis(
        ANALYZER,
        readme_path=readme,
        output=tmp_path / "feedback.json",
        run_id="feedback-profile",
        subject_id="readme",
        source_kind="generated",
    )
    complete = run_document_static_analysis(
        ANALYZER,
        readme_path=readme,
        output=tmp_path / "all.json",
        run_id="all-profile",
        subject_id="readme",
        source_kind="generated",
        profile="all",
    )

    assert feedback["summary"]["diagnostic_count"] == 0
    assert feedback["subjects"][0]["skipped_rules"] == [
        {
            "rule_id": "duplicate-heading-text",
            "reason": "excluded_from_selected_profile",
        }
    ]
    assert complete["summary"]["diagnostics_by_rule"] == {
        "duplicate-heading-text": 1
    }


def test_static_analysis_run_rejects_a_tampered_summary(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Example\n", encoding="utf-8")
    output = tmp_path / "run.json"
    run_document_static_analysis(
        ANALYZER,
        readme_path=readme,
        output=output,
        run_id="tamper-test",
        subject_id="readme",
        source_kind="local",
    )
    run = json.loads(output.read_text(encoding="utf-8"))
    run["summary"]["diagnostic_count"] = 99
    output.write_text(json.dumps(run), encoding="utf-8")

    with pytest.raises(ValueError, match="summary does not match"):
        load_static_analysis_run(output, analyzer_path=ANALYZER)
