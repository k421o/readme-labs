from pathlib import Path

from pebble_count import count_nonempty


def test_count_nonempty(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("one\n\ntwo\n", encoding="utf-8")
    assert count_nonempty(sample) == 2
