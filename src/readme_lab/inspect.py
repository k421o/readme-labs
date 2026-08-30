"""Extract deterministic structural signals from Markdown READMEs."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt

from readme_lab.domain import load_taxonomy, validate_observation

ROLE_IDS = {
    "repository_root",
    "published_package",
    "cli_tool",
    "end_user_application",
    "framework_or_platform",
    "source_distribution",
    "monorepo_root",
    "component",
    "experiment",
    "fixture_or_example",
    "archive",
    "profile",
    "unspecified",
}


def _normalized_heading(value: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", value.casefold()).split())


def _observation_id(repository: str, revision: str, path: str, digest: str) -> str:
    identity = "\0".join((repository, revision, path, digest)).encode()
    return f"sha256:{hashlib.sha256(identity).hexdigest()}"


def _infer_role(path: Path) -> tuple[str, str, list[str]]:
    if path.name.casefold() in {"readme.md", "readme"} and len(path.parts) == 1:
        return "repository_root", "inferred", []
    return (
        "unspecified",
        "inferred",
        ["Document role was not declared and could not be inferred conservatively."],
    )


def inspect_readme(
    path: Path,
    *,
    repository: str,
    revision: str,
    role: str | None = None,
    observed_at: datetime | None = None,
    source_path: str | None = None,
    retrieval_url: str | None = None,
    license_spdx: str | None = None,
) -> dict[str, Any]:
    """Create and validate a READMEObservation for one Markdown file."""

    if role is not None and role not in ROLE_IDS:
        expected = ", ".join(sorted(ROLE_IDS))
        raise ValueError(f"unknown role {role!r}; expected one of: {expected}")

    content = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode()).hexdigest()
    tokens = MarkdownIt("commonmark").parse(content)

    headings: list[dict[str, Any]] = []
    links = 0
    code_blocks = 0

    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            inline = tokens[index + 1]
            line = token.map[0] + 1 if token.map else 1
            headings.append(
                {"level": int(token.tag[1:]), "text": inline.content, "line": line}
            )
        if token.type in {"fence", "code_block"}:
            code_blocks += 1
        if token.type == "inline" and token.children:
            links += sum(child.type == "link_open" for child in token.children)

    aliases: dict[str, set[str]] = defaultdict(set)
    for category in load_taxonomy()["categories"]:
        for alias in category["heading_aliases"]:
            aliases[_normalized_heading(alias)].add(category["id"])

    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for heading in headings:
        if heading["level"] == 1 and "identity" not in evidence:
            evidence["identity"].append(
                {
                    "kind": "document_title",
                    "text": heading["text"],
                    "line": heading["line"],
                }
            )
        normalized = _normalized_heading(heading["text"])
        for category_id in aliases.get(normalized, set()):
            evidence[category_id].append(
                {
                    "kind": "heading_alias",
                    "text": heading["text"],
                    "line": heading["line"],
                }
            )

    recorded_path = source_path or path.as_posix()
    inferred_role, assignment, limitations = _infer_role(Path(recorded_path))
    primary_role = role or inferred_role
    if role is not None:
        assignment = "declared"

    timestamp = observed_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("observed_at must include a timezone")

    observation: dict[str, Any] = {
        "schema_version": "1.0.0",
        "observation_id": _observation_id(
            repository, revision, recorded_path, digest
        ),
        "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
        "source": {
            "repository": repository,
            "revision": revision,
            "path": recorded_path,
            "content_sha256": digest,
        },
        "role": {
            "primary": primary_role,
            "secondary": [],
            "assignment": assignment,
        },
        "structure": {
            "line_count": len(content.splitlines()),
            "word_count": len(re.findall(r"\b\w+\b", content)),
            "heading_count": len(headings),
            "link_count": links,
            "code_block_count": code_blocks,
            "headings": headings,
        },
        "category_signals": [
            {"category_id": category_id, "evidence": category_evidence}
            for category_id, category_evidence in sorted(evidence.items())
        ],
        "limitations": [
            *limitations,
            "Category signals use exact normalized heading aliases and do not infer "
            "semantic coverage from prose.",
            "This structural observation is not a README quality score.",
        ],
    }
    if retrieval_url is not None:
        observation["source"]["retrieval_url"] = retrieval_url
    if license_spdx is not None:
        observation["source"]["license_spdx"] = license_spdx
    validate_observation(observation)
    return observation
