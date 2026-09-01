"""Sanitize executor JSONL before it becomes durable evaluation evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any, NoReturn

RAW_OUTPUT_FIELDS = frozenset({"aggregated_output", "output", "stderr", "stdout"})


def _reject_non_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-JSON numeric constant: {value}")


def _canonical_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="surrogatepass")
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8", errors="surrogatepass")


def _digest(value: Any) -> dict[str, str | int]:
    payload = _canonical_bytes(value)
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_length": len(payload),
    }


def _is_digest(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"sha256", "byte_length"}:
        return False
    sha256 = value["sha256"]
    byte_length = value["byte_length"]
    return (
        isinstance(sha256, str)
        and len(sha256) == 64
        and all(character in "0123456789abcdef" for character in sha256)
        and isinstance(byte_length, int)
        and not isinstance(byte_length, bool)
        and byte_length >= 0
    )


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if not isinstance(value, dict):
        return value

    sanitized = {
        key: _sanitize_value(item)
        for key, item in value.items()
        if key not in RAW_OUTPUT_FIELDS
    }
    for key in RAW_OUTPUT_FIELDS:
        if key in value:
            output = value[key]
            sanitized[key] = output if _is_digest(output) else _digest(output)
    return sanitized


def _invalid_line(raw_line: bytes, *, line_number: int, reason: str) -> dict[str, Any]:
    return {
        "type": "readme_lab.invalid_event_redacted",
        "line_number": line_number,
        "reason": reason,
        "invalid_line": _digest(raw_line),
    }


def sanitize_event_jsonl(raw: str | bytes) -> str:
    """Return deterministic JSONL with raw command output replaced by digests.

    Invalid UTF-8, invalid JSON, and non-object JSON lines become hash-only
    records so malformed executor output cannot copy source material into a
    durable event log. Sanitizing an already-sanitized stream is idempotent.
    """

    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8", errors="surrogatepass")
    else:
        raw_bytes = raw
    if not raw_bytes:
        return ""

    sanitized_lines: list[str] = []
    for line_number, raw_line in enumerate(raw_bytes.splitlines(), start=1):
        try:
            decoded = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            event = _invalid_line(
                raw_line,
                line_number=line_number,
                reason="invalid_utf8",
            )
        else:
            try:
                parsed = json.loads(
                    decoded,
                    parse_constant=_reject_non_json_constant,
                )
            except (json.JSONDecodeError, ValueError):
                event = _invalid_line(
                    raw_line,
                    line_number=line_number,
                    reason="invalid_json",
                )
            else:
                if isinstance(parsed, dict):
                    event = _sanitize_value(parsed)
                else:
                    event = _invalid_line(
                        raw_line,
                        line_number=line_number,
                        reason="non_object_json",
                    )
        sanitized_lines.append(
            json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    return "\n".join(sanitized_lines) + "\n"


def sanitize_stderr_log(raw: str | bytes) -> str:
    """Return a deterministic hash-only representation of executor stderr."""

    return (
        json.dumps(
            _digest(raw),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
