"""Run versioned static analyzers as evidence-only README measurements."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from markdown_it import MarkdownIt

from readme_lab.artifacts import load_schema, resolve_contained, sha256, timestamp
from readme_lab.corpus import materialize_corpus_documents

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "experiments" / "schemas"
ANALYZER_SCHEMA = "static-analyzer-v1.schema.json"
RUN_SCHEMA = "static-analysis-run-v1.schema.json"
MARKDOWN_STRUCTURE_IMPLEMENTATION = (
    "readme_lab.static_analysis:markdown_structure_v1"
)


def load_static_analyzer(path: Path) -> dict[str, Any]:
    """Load one adapter without treating its native output as universal."""

    path = path.resolve()
    analyzer = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(
        load_schema(ANALYZER_SCHEMA, schema_root=SCHEMA_ROOT)
    ).validate(analyzer)
    rule_ids = [rule["id"] for rule in analyzer["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("static analyzer rule ids must be unique")
    documentation = resolve_contained(path.parent, analyzer["documentation"])
    if not documentation.is_file():
        raise FileNotFoundError(documentation)
    return {
        **analyzer,
        "_spec_path": path,
        "_documentation_path": documentation,
    }


def load_static_analysis_run(
    path: Path, *, analyzer_path: Path | None = None
) -> dict[str, Any]:
    """Load and validate one common static-analysis evidence envelope."""

    run = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator(
        load_schema(RUN_SCHEMA, schema_root=SCHEMA_ROOT),
        format_checker=FormatChecker(),
    ).validate(run)
    subject_ids = [subject["subject_id"] for subject in run["subjects"]]
    if len(subject_ids) != len(set(subject_ids)):
        raise ValueError("static analysis subject ids must be unique")
    if analyzer_path is not None:
        analyzer = load_static_analyzer(analyzer_path)
        expected_analyzer = {
            "id": analyzer["id"],
            "version": analyzer["adapter"]["version"],
            "adapter_kind": analyzer["adapter"]["kind"],
            "spec_sha256": sha256(analyzer["_spec_path"]),
        }
        if run["analyzer"] != expected_analyzer:
            raise ValueError("static analysis run does not match analyzer spec")
        rule_ids = {rule["id"] for rule in analyzer["rules"]}
        enabled = set(run["configuration"]["enabled_rule_ids"])
        if not enabled or not enabled <= rule_ids:
            raise ValueError("static analysis run enables unknown rules")
        if run["configuration"]["profile"] == "all" and enabled != rule_ids:
            raise ValueError("all profile does not enable every analyzer rule")
        if run["configuration"]["profile"] == "feedback":
            expected_feedback = {
                rule["id"]
                for rule in analyzer["rules"]
                if rule["feedback_default"]
            }
            if enabled != expected_feedback:
                raise ValueError("feedback profile does not match analyzer spec")
        for subject in run["subjects"]:
            if any(
                diagnostic["rule_id"] not in enabled
                for diagnostic in subject["diagnostics"]
            ):
                raise ValueError("static analysis run contains a disabled rule")
        if run["summary"] != _summarize(run["subjects"]):
            raise ValueError("static analysis run summary does not match subjects")
    return run


def _normalized_heading(value: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", value.casefold()).split())


def _diagnostic(
    *,
    rule_id: str,
    level: str,
    message: str,
    path: str,
    line: int | None,
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "level": level,
        "message": message,
        "location": {"path": path, "line": line, "column": None},
        "evidence": evidence,
    }


def markdown_structure_v1(path: Path, *, recorded_path: str) -> dict[str, Any]:
    """Return deterministic, context-free Markdown diagnostics for one file."""

    content = path.read_text(encoding="utf-8")
    tokens = MarkdownIt("commonmark").parse(content)
    diagnostics: list[dict[str, Any]] = []
    heading_count = 0
    image_count = 0
    previous_level: int | None = None
    first_heading_lines: dict[str, int] = {}

    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            heading_count += 1
            level = int(token.tag[1:])
            inline = tokens[index + 1]
            text = inline.content.strip()
            line = token.map[0] + 1 if token.map else None
            if previous_level is not None and level > previous_level + 1:
                diagnostics.append(
                    _diagnostic(
                        rule_id="heading-level-jump",
                        level="note",
                        message=(
                            "Heading level increases from "
                            f"h{previous_level} to h{level}."
                        ),
                        path=recorded_path,
                        line=line,
                        evidence=[f"previous_level={previous_level}", f"level={level}"],
                    )
                )
            previous_level = level
            if not text:
                diagnostics.append(
                    _diagnostic(
                        rule_id="empty-heading",
                        level="warning",
                        message="Heading has no visible text.",
                        path=recorded_path,
                        line=line,
                        evidence=[f"level={level}"],
                    )
                )
            else:
                normalized = _normalized_heading(text)
                if normalized in first_heading_lines:
                    diagnostics.append(
                        _diagnostic(
                            rule_id="duplicate-heading-text",
                            level="note",
                            message=f"Heading text repeats an earlier label: {text!r}.",
                            path=recorded_path,
                            line=line,
                            evidence=[
                                f"normalized={normalized}",
                                f"first_line={first_heading_lines[normalized]}",
                            ],
                        )
                    )
                elif line is not None:
                    first_heading_lines[normalized] = line

        if token.type == "inline" and token.children:
            for child in token.children:
                if child.type != "image":
                    continue
                image_count += 1
                if not child.content.strip():
                    line = token.map[0] + 1 if token.map else None
                    source = child.attrGet("src") or ""
                    diagnostics.append(
                        _diagnostic(
                            rule_id="image-missing-alt",
                            level="warning",
                            message="Markdown image has empty alternative text.",
                            path=recorded_path,
                            line=line,
                            evidence=[f"source={source}"],
                        )
                    )

    return {
        "result": "completed",
        "incomplete_reason": None,
        "metrics": {
            "line_count": len(content.splitlines()),
            "heading_count": heading_count,
            "image_count": image_count,
            "evaluated_rule_count": 4,
        },
        "diagnostics": diagnostics,
        "skipped_rules": [],
        "native_artifact": None,
    }


def _analyze(
    analyzer: dict[str, Any], path: Path, *, recorded_path: str
) -> dict[str, Any]:
    implementation = analyzer["adapter"]["implementation"]
    if (
        analyzer["adapter"]["kind"] != "builtin_python"
        or implementation != MARKDOWN_STRUCTURE_IMPLEMENTATION
    ):
        raise NotImplementedError(
            f"no trusted static-analysis runner is registered for {implementation}"
        )
    return markdown_structure_v1(path, recorded_path=recorded_path)


def _subject(
    analyzer: dict[str, Any],
    *,
    path: Path,
    subject_id: str,
    source_kind: str,
    recorded_path: str,
    repository: str | None,
    revision: str | None,
    retrieval_url: str | None = None,
    enabled_rule_ids: set[str],
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "kind": source_kind,
        "repository": repository,
        "revision": revision,
        "path": recorded_path,
        "content_sha256": sha256(path),
    }
    if retrieval_url is not None:
        source["retrieval_url"] = retrieval_url
    result = _analyze(analyzer, path, recorded_path=recorded_path)
    result["diagnostics"] = [
        diagnostic
        for diagnostic in result["diagnostics"]
        if diagnostic["rule_id"] in enabled_rule_ids
    ]
    result["skipped_rules"] = [
        {
            "rule_id": rule["id"],
            "reason": "excluded_from_selected_profile",
        }
        for rule in analyzer["rules"]
        if rule["id"] not in enabled_rule_ids
    ]
    result["metrics"]["evaluated_rule_count"] = len(enabled_rule_ids)
    return {
        "subject_id": subject_id,
        "source": source,
        **result,
    }


def _summarize(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    rule_counts = Counter(
        diagnostic["rule_id"]
        for subject in subjects
        for diagnostic in subject["diagnostics"]
    )
    completed = sum(subject["result"] == "completed" for subject in subjects)
    return {
        "subject_count": len(subjects),
        "completed_subject_count": completed,
        "incomplete_subject_count": len(subjects) - completed,
        "diagnostic_count": sum(rule_counts.values()),
        "diagnostics_by_rule": dict(sorted(rule_counts.items())),
    }


def _run_record(
    analyzer: dict[str, Any],
    *,
    run_id: str,
    mode: str,
    subjects: list[dict[str, Any]],
    profile: str,
    enabled_rule_ids: set[str],
    recorded_at: datetime,
    extra_limitations: list[str] | None = None,
) -> dict[str, Any]:
    run = {
        "schema_version": 1,
        "run_id": run_id,
        "recorded_at": timestamp(recorded_at),
        "mode": mode,
        "analyzer": {
            "id": analyzer["id"],
            "version": analyzer["adapter"]["version"],
            "adapter_kind": analyzer["adapter"]["kind"],
            "spec_sha256": sha256(analyzer["_spec_path"]),
        },
        "configuration": {
            "profile": profile,
            "enabled_rule_ids": sorted(enabled_rule_ids),
        },
        "automated_authority": "evidence_only",
        "hypothesis_disposition": "not_decided",
        "result": (
            "completed"
            if all(subject["result"] == "completed" for subject in subjects)
            else "incomplete"
        ),
        "subjects": subjects,
        "summary": _summarize(subjects),
        "limitations": [
            *analyzer["limitations"],
            *(extra_limitations or []),
        ],
    }
    Draft202012Validator(
        load_schema(RUN_SCHEMA, schema_root=SCHEMA_ROOT),
        format_checker=FormatChecker(),
    ).validate(run)
    return run


def _write_new_run(output: Path, run: dict[str, Any]) -> None:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_document_static_analysis(
    analyzer_path: Path,
    *,
    readme_path: Path,
    output: Path,
    run_id: str,
    subject_id: str,
    source_kind: str,
    recorded_path: str | None = None,
    repository: str | None = None,
    revision: str | None = None,
    profile: str = "feedback",
    recorded_at: datetime | None = None,
) -> dict[str, Any]:
    """Analyze one generated, ingested, candidate, or local README."""

    analyzer = load_static_analyzer(analyzer_path)
    if "document_diagnostic" not in analyzer["supported_modes"]:
        raise ValueError("analyzer does not support document diagnostics")
    readme_path = readme_path.resolve()
    if not readme_path.is_file():
        raise FileNotFoundError(readme_path)
    if profile == "all":
        enabled_rule_ids = {rule["id"] for rule in analyzer["rules"]}
    elif profile == "feedback":
        enabled_rule_ids = {
            rule["id"] for rule in analyzer["rules"] if rule["feedback_default"]
        }
    else:
        raise ValueError(f"unknown static-analysis profile: {profile}")
    subject = _subject(
        analyzer,
        path=readme_path,
        subject_id=subject_id,
        source_kind=source_kind,
        recorded_path=recorded_path or readme_path.name,
        repository=repository,
        revision=revision,
        enabled_rule_ids=enabled_rule_ids,
    )
    run = _run_record(
        analyzer,
        run_id=run_id,
        mode="document_diagnostic",
        subjects=[subject],
        profile=profile,
        enabled_rule_ids=enabled_rule_ids,
        recorded_at=recorded_at or datetime.now(UTC),
    )
    _write_new_run(output, run)
    return run


def run_corpus_static_analysis(
    analyzer_path: Path,
    *,
    manifest_path: Path,
    cache_dir: Path,
    output: Path,
    run_id: str,
    recorded_at: datetime | None = None,
) -> dict[str, Any]:
    """Characterize one analyzer across a pinned README corpus."""

    analyzer = load_static_analyzer(analyzer_path)
    if "corpus_characterization" not in analyzer["supported_modes"]:
        raise ValueError("analyzer does not support corpus characterization")
    documents = materialize_corpus_documents(manifest_path, cache_dir=cache_dir)
    enabled_rule_ids = {rule["id"] for rule in analyzer["rules"]}
    subjects = [
        _subject(
            analyzer,
            path=path,
            subject_id=item["sample_id"],
            source_kind="corpus_sample",
            recorded_path=item["path"],
            repository=item["repository"],
            revision=item["revision"],
            retrieval_url=item["source_url"],
            enabled_rule_ids=enabled_rule_ids,
        )
        for item, path in documents
    ]
    run = _run_record(
        analyzer,
        run_id=run_id,
        mode="corpus_characterization",
        subjects=subjects,
        profile="all",
        enabled_rule_ids=enabled_rule_ids,
        recorded_at=recorded_at or datetime.now(UTC),
        extra_limitations=[
            "Corpus diagnostics describe this pinned sample and do not estimate "
            "population prevalence or README quality."
        ],
    )
    _write_new_run(output, run)
    return run
