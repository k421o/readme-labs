"""Collect pinned README bodies and summarize structural observations."""

from __future__ import annotations

import hashlib
import json
import statistics
import urllib.request
from collections import Counter
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readme_lab.domain import load_taxonomy
from readme_lab.inspect import inspect_readme

MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "corpus" / ("manifest-item-v1.schema.json")
)


def _load_manifest_schema() -> dict[str, Any]:
    if MANIFEST_SCHEMA_PATH.is_file():
        text = MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
    else:
        packaged = resources.files("readme_lab").joinpath(
            "data", "manifest-item-v1.schema.json"
        )
        text = packaged.read_text(encoding="utf-8")
    schema = json.loads(text)
    if not isinstance(schema, dict):
        raise TypeError("manifest schema must be a JSON object")
    return schema


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Load and validate a JSON Lines corpus manifest."""

    validator = Draft202012Validator(
        _load_manifest_schema(), format_checker=FormatChecker()
    )
    items: list[dict[str, Any]] = []
    for _line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        item = json.loads(line)
        validator.validate(item)
        items.append(item)
    sample_ids = [item["sample_id"] for item in items]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError(f"duplicate sample_id in {path}")
    return items


def git_blob_sha(content: bytes) -> str:
    """Return the Git SHA-1 object identifier for raw blob content."""

    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "readme-labs/0.1 corpus collector"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def collect_corpus(
    manifest_path: Path,
    *,
    cache_dir: Path,
    observations_path: Path,
) -> dict[str, Any]:
    """Fetch, verify, cache, and inspect every item in a manifest."""

    items = load_manifest(manifest_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    observations: list[dict[str, Any]] = []

    for item in items:
        sample_dir = cache_dir / item["sample_id"]
        sample_dir.mkdir(parents=True, exist_ok=True)
        cached_path = sample_dir / Path(item["path"]).name
        content = (
            cached_path.read_bytes()
            if cached_path.exists()
            else _fetch(item["source_url"])
        )
        actual_blob_sha = git_blob_sha(content)
        if actual_blob_sha != item["blob_sha"]:
            raise ValueError(
                f"blob mismatch for {item['sample_id']}: "
                f"expected {item['blob_sha']}, got {actual_blob_sha}"
            )
        if not cached_path.exists():
            cached_path.write_bytes(content)

        observed_at = datetime.fromisoformat(
            item["collected_at"].replace("Z", "+00:00")
        )
        observations.append(
            inspect_readme(
                cached_path,
                repository=item["repository"],
                revision=item["revision"],
                role=item["role_primary"],
                role_assignment=item["role_assignment"],
                annotation=item.get("role_annotation"),
                observed_at=observed_at,
                source_path=item["path"],
                retrieval_url=item["source_url"],
                license_spdx=item["license_spdx"],
            )
        )

    observations_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = "".join(
        json.dumps(item, sort_keys=True) + "\n" for item in observations
    )
    observations_path.write_text(serialized, encoding="utf-8")
    return {
        "manifest": manifest_path.as_posix(),
        "observations": observations_path.as_posix(),
        "sample_count": len(observations),
    }


def load_observations(path: Path) -> list[dict[str, Any]]:
    """Load observation JSON Lines for aggregate analysis."""

    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def summarize_observations(path: Path) -> dict[str, Any]:
    """Return descriptive statistics for a READMEObservation set."""

    observations = load_observations(path)
    if not observations:
        raise ValueError(f"no observations in {path}")

    roles = Counter(item["role"]["primary"] for item in observations)
    categories = Counter(
        {category["id"]: 0 for category in load_taxonomy()["categories"]}
    )
    categories.update(
        signal["category_id"]
        for item in observations
        for signal in item["category_signals"]
    )
    sample_count = len(observations)

    def values(field: str) -> list[int]:
        return [item["structure"][field] for item in observations]

    return {
        "analysis_version": "1.0.0",
        "source_observations": path.as_posix(),
        "observation_schema_versions": sorted(
            {item["schema_version"] for item in observations}
        ),
        "sample_count": sample_count,
        "role_counts": dict(sorted(roles.items())),
        "category_signal_counts": dict(sorted(categories.items())),
        "category_signal_rates": {
            category: round(count / sample_count, 4)
            for category, count in sorted(categories.items())
        },
        "structure": {
            field: {
                "mean": round(statistics.fmean(values(field)), 2),
                "median": statistics.median(values(field)),
                "minimum": min(values(field)),
                "maximum": max(values(field)),
            }
            for field in (
                "word_count",
                "heading_count",
                "link_count",
                "code_block_count",
            )
        },
        "interpretation": (
            "Descriptive results for a purposive high-exposure pilot; not a "
            "population prevalence or training-data estimate."
        ),
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    """Write a stable formatted aggregate report."""

    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")
