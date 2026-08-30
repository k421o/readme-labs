from __future__ import annotations

import argparse
from pathlib import Path


def count_nonempty(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(bool(line.strip()) for line in lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(count_nonempty(args.path))
