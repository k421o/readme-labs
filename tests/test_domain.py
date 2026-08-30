from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from readme_lab.domain import OBSERVATION_SCHEMA_PATHS, TAXONOMY_PATH


def test_domain_json_files_have_valid_versioned_contracts() -> None:
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    assert taxonomy["version"] == "1.0.0"
    assert len(taxonomy["jobs"]) == 6
    assert len(taxonomy["categories"]) == 10
    assert len({category["id"] for category in taxonomy["categories"]}) == 10
    assert set(OBSERVATION_SCHEMA_PATHS) == {"1.0.0", "2.0.0"}
    for schema_path in OBSERVATION_SCHEMA_PATHS.values():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
