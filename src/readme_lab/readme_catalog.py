"""Render README evidence packages and build a disposable SQLite catalog."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from readme_lab.readme_artifacts import (
    load_artifact_evidence,
    load_artifact_record,
    verify_artifact_package,
)

CATALOG_SCHEMA_VERSION = 1


def _cell(value: Any) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _relative_link(record_dir: Path, repository_root: Path, source: str) -> str:
    destination = repository_root.resolve() / source
    return Path(os.path.relpath(destination, record_dir.resolve())).as_posix()


def _source_links(
    evidence: dict[str, Any], *, record_dir: Path, repository_root: Path
) -> str:
    return ", ".join(
        f"[{source['role']}]"
        f"({_relative_link(record_dir, repository_root, source['path'])})"
        for source in evidence["source_records"]
    )


def _structural_section(evidence: dict[str, Any]) -> list[str]:
    payload = evidence["payload"]
    structure = payload["structure"]
    categories = ", ".join(
        f"`{item['category_id']}`" for item in payload["category_signals"]
    )
    return [
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Lines | {structure['line_count']} |",
        f"| Words | {structure['word_count']} |",
        f"| Headings | {structure['heading_count']} |",
        f"| Links | {structure['link_count']} |",
        f"| Code blocks | {structure['code_block_count']} |",
        "",
        f"Observed category signals: {categories or 'none'}. These are structural "
        "signals, not semantic-coverage or quality judgments.",
    ]


def _static_section(evidence: dict[str, Any]) -> list[str]:
    payload = evidence["payload"]
    subject = payload["subject"]
    lines = [
        "",
        f"Profile: `{payload['configuration']['profile']}`. Enabled rules: "
        + ", ".join(
            f"`{rule}`" for rule in payload["configuration"]["enabled_rule_ids"]
        )
        + ".",
        "",
    ]
    diagnostics = subject["diagnostics"]
    if diagnostics:
        lines.extend(
            [
                "| Rule | Level | Location | Message |",
                "| --- | --- | --- | --- |",
            ]
        )
        for diagnostic in diagnostics:
            location = diagnostic["location"]
            position = location["path"]
            if location["line"] is not None:
                position += f":{location['line']}"
            lines.append(
                f"| `{_cell(diagnostic['rule_id'])}` | "
                f"{_cell(diagnostic['level'])} | `{_cell(position)}` | "
                f"{_cell(diagnostic['message'])} |"
            )
    else:
        lines.append(
            "No enabled rule emitted a diagnostic. This is not a quality or merge "
            "verdict."
        )
    if subject["skipped_rules"]:
        lines.extend(
            [
                "",
                "Skipped rules: "
                + ", ".join(
                    f"`{item['rule_id']}` ({item['reason']})"
                    for item in subject["skipped_rules"]
                )
                + ".",
            ]
        )
    return lines


def _soft_review_section(evidence: dict[str, Any]) -> list[str]:
    payload = evidence["payload"]
    response = payload["response"]
    if response is None:
        return ["", evidence["summary"]]
    lines = [
        "",
        f"Recommendation: `{response['recommendation']}` with "
        f"`{response['confidence']}` confidence. This recommendation is advisory.",
        "",
        response["summary"],
    ]
    if response["strengths"]:
        lines.extend(["", "Strengths:", ""])
        lines.extend(f"- {item['claim']}" for item in response["strengths"])
    if response["concerns"]:
        lines.extend(["", "Concerns:", ""])
        for concern in response["concerns"]:
            lines.append(
                f"- **{concern['title']}** (`{concern['severity']}`): "
                f"{concern['rationale']} Suggested change: "
                f"{concern['suggested_change']}"
            )
    if response["questions"]:
        lines.extend(["", "Questions:", ""])
        lines.extend(f"- {question}" for question in response["questions"])
    return lines


def render_artifact_report(record_dir: Path, *, repository_root: Path) -> str:
    """Return a deterministic human view without collapsing evidence to a score."""

    record_dir = record_dir.resolve()
    record = load_artifact_record(record_dir)
    evidence = load_artifact_evidence(
        record_dir, repository_root=repository_root.resolve()
    )
    artifact = record["artifact"]
    storage = artifact["storage"]
    if storage["mode"] == "embedded":
        subject = "[`artifact.md`](artifact.md)"
    else:
        subject = f"[external source]({storage['locator']})"
    lines = [
        "---",
        "schema: readme-artifact-report-v1",
        f"record_id: {record['record_id']}",
        f"artifact_id: {artifact['id']}",
        "---",
        "",
        f"# README artifact `{record['record_id']}`",
        "",
        "This report is a generated projection over the canonical JSON record and "
        "attached evidence. It is not the README under review and does not carry a "
        "combined quality score.",
        "",
        "## Artifact",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Subject | {subject} |",
        f"| Content SHA-256 | `{artifact['content_sha256']}` |",
        f"| Original name | `{_cell(artifact['original_name'])}` |",
        f"| Storage | `{storage['mode']}` |",
        f"| Capture boundary | `{record['capture']['boundary']}` |",
        "| Pre-capture editability | "
        f"`{record['capture']['pre_capture_editability']}` |",
        f"| Ownership | `{record['custody']['ownership']}` |",
        f"| Visibility | `{record['custody']['visibility']}` |",
        "",
        "## Provenance",
        "",
        "| Event | Kind | Source | Producer |",
        "| --- | --- | --- | --- |",
    ]
    for item in record["provenance"]:
        source_value = item.get("source") or {}
        source = "/".join(
            str(value)
            for value in (
                source_value.get("repository"),
                source_value.get("revision"),
                source_value.get("path"),
            )
            if value is not None
        )
        producer_value = item.get("producer")
        producer = (
            f"{producer_value['kind']}:{producer_value['id']}"
            if producer_value
            else "—"
        )
        lines.append(
            f"| `{item['id']}` | `{item['kind']}` | {_cell(source or '—')} | "
            f"{_cell(producer)} |"
        )

    lines.extend(
        [
            "",
            "## Repository occurrences",
            "",
            "| Occurrence | Repository | Revision/tree | Path | Role |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if record["occurrences"]:
        for item in record["occurrences"]:
            revision = item["revision"]
            if item.get("tree"):
                revision += f" / {item['tree']}"
            lines.append(
                f"| `{item['id']}` | {_cell(item['repository'])} | "
                f"`{_cell(revision)}` | `{_cell(item['path'])}` | "
                f"`{_cell(item['role'])}` |"
            )
    else:
        lines.append("| — | — | — | — | — |")

    lines.extend(
        [
            "",
            "## Collection memberships",
            "",
            "| Collection | Purpose | Recorded at |",
            "| --- | --- | --- |",
        ]
    )
    if record["memberships"]:
        lines.extend(
            f"| `{item['collection_id']}` | `{item['purpose']}` | "
            f"{item['recorded_at']} |"
            for item in record["memberships"]
        )
    else:
        lines.append("| — | — | — |")

    lines.extend(["", "## Evidence", ""])
    if not evidence:
        lines.append("No evidence results are attached yet.")
    for item in evidence:
        lines.extend(
            [
                f"### `{item['kind']}` — `{item['evidence_id']}`",
                "",
                item["summary"],
                "",
                f"Result: `{item['result']}`. Subject scope: "
                f"`{item['subject_scope']}`. Sources: "
                +
                _source_links(
                    item, record_dir=record_dir, repository_root=repository_root
                )
                + ".",
            ]
        )
        if item["kind"] == "structural_observation":
            lines.extend(_structural_section(item))
        elif item["kind"] == "static_analysis":
            lines.extend(_static_section(item))
        elif item["kind"] == "soft_agent_review":
            lines.extend(_soft_review_section(item))
        if item["limitations"]:
            lines.extend(["", "Limitations:", ""])
            lines.extend(f"- {limitation}" for limitation in item["limitations"])
        lines.append("")

    lines.extend(
        [
            "## Authority boundary",
            "",
            "All attached automated and advisory results remain evidence only. Zero "
            "diagnostics is not approval, an evaluator recommendation is not a "
            "promotion decision, and this report does not determine experiment "
            "disposition.",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifact_report(
    record_dir: Path, *, repository_root: Path, check: bool = False
) -> Path:
    """Write or verify the generated report beside one artifact record."""

    record_dir = record_dir.resolve()
    output = record_dir / "report.md"
    expected = render_artifact_report(record_dir, repository_root=repository_root)
    if check:
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            raise ValueError(f"artifact report is stale or missing: {output}")
        return output
    output.write_text(expected, encoding="utf-8")
    return output


def _initialize_catalog(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE artifacts (
            record_id TEXT PRIMARY KEY,
            artifact_id TEXT NOT NULL UNIQUE,
            content_sha256 TEXT NOT NULL UNIQUE,
            media_type TEXT NOT NULL,
            byte_length INTEGER,
            original_name TEXT NOT NULL,
            storage_mode TEXT NOT NULL,
            capture_boundary TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            pre_capture_editability TEXT NOT NULL,
            ownership TEXT NOT NULL,
            visibility TEXT NOT NULL,
            body_policy TEXT NOT NULL,
            license_spdx TEXT
        );
        CREATE TABLE provenance (
            provenance_id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES artifacts(record_id),
            kind TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            source_repository TEXT,
            source_revision TEXT,
            source_path TEXT,
            source_locator TEXT,
            producer_kind TEXT,
            producer_id TEXT,
            producer_version TEXT,
            producer_run_id TEXT
        );
        CREATE TABLE occurrences (
            occurrence_id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES artifacts(record_id),
            repository TEXT NOT NULL,
            revision TEXT NOT NULL,
            tree TEXT,
            path TEXT NOT NULL,
            role TEXT NOT NULL,
            retrieval_url TEXT
        );
        CREATE TABLE memberships (
            record_id TEXT NOT NULL REFERENCES artifacts(record_id),
            collection_id TEXT NOT NULL,
            purpose TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (record_id, collection_id, purpose)
        );
        CREATE TABLE lineage (
            record_id TEXT NOT NULL REFERENCES artifacts(record_id),
            relationship TEXT NOT NULL,
            target_record_id TEXT,
            target_artifact_id TEXT,
            note TEXT
        );
        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES artifacts(record_id),
            artifact_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            subject_scope TEXT NOT NULL,
            occurrence_id TEXT REFERENCES occurrences(occurrence_id),
            recorded_at TEXT NOT NULL,
            producer_kind TEXT NOT NULL,
            producer_id TEXT NOT NULL,
            producer_version TEXT,
            result TEXT NOT NULL,
            summary TEXT NOT NULL,
            recommendation TEXT,
            confidence TEXT,
            diagnostic_count INTEGER
        );
        CREATE TABLE evidence_sources (
            evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
            role TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            selector TEXT,
            PRIMARY KEY (evidence_id, role, path)
        );
        CREATE TABLE diagnostics (
            evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
            ordinal INTEGER NOT NULL,
            rule_id TEXT NOT NULL,
            level TEXT NOT NULL,
            path TEXT NOT NULL,
            line INTEGER,
            column_number INTEGER,
            message TEXT NOT NULL,
            PRIMARY KEY (evidence_id, ordinal)
        );
        """
    )
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES (?, ?)",
        ("schema_version", str(CATALOG_SCHEMA_VERSION)),
    )


def _insert_artifact(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> None:
    artifact = record["artifact"]
    custody = record["custody"]
    capture = record["capture"]
    connection.execute(
        "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            record["record_id"],
            artifact["id"],
            artifact["content_sha256"],
            artifact["media_type"],
            artifact["byte_length"],
            artifact["original_name"],
            artifact["storage"]["mode"],
            capture["boundary"],
            capture["captured_at"],
            capture["pre_capture_editability"],
            custody["ownership"],
            custody["visibility"],
            custody["body_policy"],
            custody.get("license_spdx"),
        ),
    )
    for item in record["provenance"]:
        source = item.get("source") or {}
        producer = item.get("producer") or {}
        connection.execute(
            "INSERT INTO provenance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["id"],
                record["record_id"],
                item["kind"],
                item["recorded_at"],
                source.get("repository"),
                source.get("revision"),
                source.get("path"),
                source.get("locator"),
                producer.get("kind"),
                producer.get("id"),
                producer.get("version"),
                producer.get("run_id"),
            ),
        )
    for item in record["occurrences"]:
        connection.execute(
            "INSERT INTO occurrences VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["id"],
                record["record_id"],
                item["repository"],
                item["revision"],
                item.get("tree"),
                item["path"],
                item["role"],
                item.get("retrieval_url"),
            ),
        )
    for item in record["memberships"]:
        connection.execute(
            "INSERT INTO memberships VALUES (?, ?, ?, ?)",
            (
                record["record_id"],
                item["collection_id"],
                item["purpose"],
                item["recorded_at"],
            ),
        )
    for item in record["lineage"]:
        connection.execute(
            "INSERT INTO lineage VALUES (?, ?, ?, ?, ?)",
            (
                record["record_id"],
                item["relationship"],
                item.get("target_record_id"),
                item.get("target_artifact_id"),
                item.get("note"),
            ),
        )
    for item in evidence_records:
        payload = item["payload"]
        recommendation = payload.get("recommendation")
        confidence = payload.get("confidence")
        diagnostics = (
            payload.get("subject", {}).get("diagnostics", [])
            if item["kind"] == "static_analysis"
            else []
        )
        connection.execute(
            "INSERT INTO evidence VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["evidence_id"],
                record["record_id"],
                item["artifact_id"],
                item["kind"],
                item["subject_scope"],
                item["occurrence_id"],
                item["recorded_at"],
                item["producer"]["kind"],
                item["producer"]["id"],
                item["producer"]["version"],
                item["result"],
                item["summary"],
                recommendation,
                confidence,
                len(diagnostics) if item["kind"] == "static_analysis" else None,
            ),
        )
        for source in item["source_records"]:
            connection.execute(
                "INSERT INTO evidence_sources VALUES (?, ?, ?, ?, ?)",
                (
                    item["evidence_id"],
                    source["role"],
                    source["path"],
                    source["sha256"],
                    source["selector"],
                ),
            )
        for ordinal, diagnostic in enumerate(diagnostics):
            location = diagnostic["location"]
            connection.execute(
                "INSERT INTO diagnostics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["evidence_id"],
                    ordinal,
                    diagnostic["rule_id"],
                    diagnostic["level"],
                    location["path"],
                    location["line"],
                    location["column"],
                    diagnostic["message"],
                ),
            )


def build_sqlite_catalog(
    records_root: Path, *, output: Path, repository_root: Path
) -> dict[str, Any]:
    """Rebuild a disposable query catalog from canonical JSON packages."""

    records_root = records_root.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    record_dirs = sorted(
        path for path in records_root.glob("rm-*") if (path / "record.json").is_file()
    )
    connection = sqlite3.connect(temporary)
    try:
        _initialize_catalog(connection)
        evidence_count = 0
        for record_dir in record_dirs:
            verify_artifact_package(record_dir, repository_root=repository_root)
            record = load_artifact_record(record_dir)
            evidence = load_artifact_evidence(
                record_dir, repository_root=repository_root
            )
            evidence_count += len(evidence)
            _insert_artifact(connection, record, evidence)
        connection.commit()
    except Exception:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise
    connection.close()
    temporary.replace(output)
    return {
        "catalog": output.as_posix(),
        "schema_version": CATALOG_SCHEMA_VERSION,
        "artifact_count": len(record_dirs),
        "evidence_count": evidence_count,
    }
