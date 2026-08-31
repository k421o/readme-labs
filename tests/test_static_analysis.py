from __future__ import annotations

import json
from pathlib import Path

import pytest

from readme_lab.static_analysis import load_static_analyzer

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
