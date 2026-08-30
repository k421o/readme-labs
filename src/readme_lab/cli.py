"""Command-line entry point for readme-labs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from readme_lab.capsule import materialize_capsule
from readme_lab.inspect import ROLE_IDS, inspect_readme


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="readme-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="emit a structural READMEObservation as JSON"
    )
    inspect_parser.add_argument("path", type=Path)
    inspect_parser.add_argument("--repository", required=True)
    inspect_parser.add_argument("--revision", required=True)
    inspect_parser.add_argument("--role", choices=sorted(ROLE_IDS))

    capsule_parser = subparsers.add_parser(
        "capsule", help="work with evaluation task capsules"
    )
    capsule_subparsers = capsule_parser.add_subparsers(
        dest="capsule_command", required=True
    )
    materialize_parser = capsule_subparsers.add_parser(
        "materialize", help="create an isolated local Git scenario repository"
    )
    materialize_parser.add_argument("capsule", type=Path)
    materialize_parser.add_argument("--destination", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        observation = inspect_readme(
            args.path,
            repository=args.repository,
            revision=args.revision,
            role=args.role,
        )
        print(json.dumps(observation, indent=2, sort_keys=True))
        return 0
    if args.command == "capsule" and args.capsule_command == "materialize":
        result = materialize_capsule(args.capsule, args.destination)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
