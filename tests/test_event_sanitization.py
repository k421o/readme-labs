from __future__ import annotations

import hashlib
import json
from pathlib import Path

from readme_lab.event_sanitization import sanitize_event_jsonl, sanitize_stderr_log


def _digest(value: str) -> dict[str, str | int]:
    payload = value.encode()
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_length": len(payload),
    }


def test_command_output_is_replaced_without_losing_execution_metadata() -> None:
    aggregated_output = "# Example\n\nREADME body.\n"
    output = "nested output"
    raw_event = {
        "type": "item.completed",
        "item": {
            "id": "item_1",
            "type": "command_execution",
            "command": "sed -n '1,80p' README.md",
            "aggregated_output": aggregated_output,
            "exit_code": 0,
            "status": "completed",
            "details": {"output": output},
        },
    }

    sanitized_text = sanitize_event_jsonl(json.dumps(raw_event) + "\n")
    sanitized = json.loads(sanitized_text)

    assert aggregated_output not in sanitized_text
    assert output not in sanitized_text
    assert sanitized["item"]["command"] == "sed -n '1,80p' README.md"
    assert sanitized["item"]["exit_code"] == 0
    assert sanitized["item"]["status"] == "completed"
    assert sanitized["item"]["aggregated_output"] == _digest(aggregated_output)
    assert sanitized["item"]["details"]["output"] == _digest(output)
    assert sanitize_event_jsonl(sanitized_text) == sanitized_text


def test_all_raw_output_field_names_are_sanitized_recursively() -> None:
    raw_event = {
        "type": "item.completed",
        "items": [
            {
                "stdout": "standard output",
                "stderr": "standard error",
            }
        ],
    }

    sanitized = json.loads(sanitize_event_jsonl(json.dumps(raw_event)))

    assert sanitized["items"][0]["stdout"] == _digest("standard output")
    assert sanitized["items"][0]["stderr"] == _digest("standard error")


def test_invalid_lines_are_replaced_with_hash_only_records() -> None:
    invalid_json = b"not JSON: # README body"
    non_object_json = b'"another README body"'
    invalid_utf8 = b"\xffprivate bytes"
    raw = b"\n".join((invalid_json, non_object_json, invalid_utf8)) + b"\n"

    sanitized_text = sanitize_event_jsonl(raw)
    records = [json.loads(line) for line in sanitized_text.splitlines()]

    assert "README body" not in sanitized_text
    assert "private bytes" not in sanitized_text
    assert [record["line_number"] for record in records] == [1, 2, 3]
    assert [record["reason"] for record in records] == [
        "invalid_json",
        "non_object_json",
        "invalid_utf8",
    ]
    for raw_line, record in zip(
        (invalid_json, non_object_json, invalid_utf8), records, strict=True
    ):
        assert record["type"] == "readme_lab.invalid_event_redacted"
        assert record["invalid_line"] == {
            "sha256": hashlib.sha256(raw_line).hexdigest(),
            "byte_length": len(raw_line),
        }


def test_empty_event_stream_stays_empty() -> None:
    assert sanitize_event_jsonl("") == ""


def test_stderr_is_replaced_by_one_digest_record() -> None:
    raw = "executor failure: private README bytes\n"

    sanitized = sanitize_stderr_log(raw)

    assert raw not in sanitized
    assert json.loads(sanitized) == _digest(raw)
    assert (
        sanitized
        == json.dumps(_digest(raw), separators=(",", ":"), sort_keys=True) + "\n"
    )


def test_prepublication_trace_is_sanitized_and_matches_its_run_binding() -> None:
    run_path = Path(
        "evals/runs/v0.2.0-rc.1/independent-review/prepublication-review.run.json"
    )
    run = json.loads(run_path.read_text(encoding="utf-8"))
    events_path = run_path.parent / run["artifacts"]["events"]
    events = events_path.read_bytes()

    assert hashlib.sha256(events).hexdigest() == run["artifacts"]["events_sha256"]
    assert sanitize_event_jsonl(events) == events.decode()
    assert run["event_sanitization"]["policy"] == ("readme-labs-output-digest-v1")
