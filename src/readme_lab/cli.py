"""Command-line entry point for readme-labs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from readme_lab.agent_evaluation import run_agent_evaluation
from readme_lab.candidates import materialize_candidate, verify_candidate
from readme_lab.capsule import materialize_capsule
from readme_lab.corpus import collect_corpus, summarize_observations, write_summary
from readme_lab.evaluation import run_codex_capsule, score_review_response
from readme_lab.experiments import load_experiment_plan
from readme_lab.inspect import ROLE_IDS, inspect_readme
from readme_lab.intake import fingerprint_git_path, verify_intake_manifest


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
    run_parser = capsule_subparsers.add_parser(
        "run", help="execute a blinded README review through Codex"
    )
    run_parser.add_argument("capsule", type=Path)
    run_parser.add_argument("--workspace", type=Path, required=True)
    run_parser.add_argument("--run-dir", type=Path, required=True)
    run_parser.add_argument("--run-id", required=True)
    run_parser.add_argument("--artifact-revision", required=True)
    run_parser.add_argument("--plugin-id", default="readme-labs@readme-labs")
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default="high",
    )
    score_parser = capsule_subparsers.add_parser(
        "score", help="apply deterministic checks to a held-out response"
    )
    score_parser.add_argument("capsule", type=Path)
    score_parser.add_argument("--response", type=Path, required=True)
    score_parser.add_argument("--events", type=Path)
    score_parser.add_argument("--stderr", type=Path)
    score_parser.add_argument("--output", type=Path)

    corpus_parser = subparsers.add_parser("corpus", help="collect and analyze corpora")
    corpus_subparsers = corpus_parser.add_subparsers(
        dest="corpus_command", required=True
    )
    collect_parser = corpus_subparsers.add_parser(
        "collect", help="fetch pinned documents and emit observations"
    )
    collect_parser.add_argument("manifest", type=Path)
    collect_parser.add_argument("--cache", type=Path, required=True)
    collect_parser.add_argument("--observations", type=Path, required=True)
    summarize_parser = corpus_subparsers.add_parser(
        "summarize", help="summarize a READMEObservation JSON Lines file"
    )
    summarize_parser.add_argument("observations", type=Path)
    summarize_parser.add_argument("--output", type=Path)

    intake_parser = subparsers.add_parser(
        "intake", help="fingerprint and verify outside evidence"
    )
    intake_subparsers = intake_parser.add_subparsers(
        dest="intake_command", required=True
    )
    intake_fingerprint_parser = intake_subparsers.add_parser(
        "fingerprint", help="describe an immutable Git file or tree"
    )
    intake_fingerprint_parser.add_argument("--source-root", type=Path, required=True)
    intake_fingerprint_parser.add_argument("--revision", required=True)
    intake_fingerprint_parser.add_argument("--path", required=True)
    intake_fingerprint_parser.add_argument(
        "--artifact-type", choices=("file", "tree"), required=True
    )
    intake_verify_parser = intake_subparsers.add_parser(
        "verify", help="verify an intake manifest and its snapshots"
    )
    intake_verify_parser.add_argument("manifest", type=Path)
    intake_verify_parser.add_argument("--source-root", type=Path)

    candidate_parser = subparsers.add_parser(
        "candidate", help="verify or materialize an experimental candidate"
    )
    candidate_subparsers = candidate_parser.add_subparsers(
        dest="candidate_command", required=True
    )
    candidate_verify_parser = candidate_subparsers.add_parser(
        "verify", help="verify candidate bytes and source bindings"
    )
    candidate_verify_parser.add_argument("candidate", type=Path)
    candidate_materialize_parser = candidate_subparsers.add_parser(
        "materialize", help="copy a verified candidate into an isolated directory"
    )
    candidate_materialize_parser.add_argument("candidate", type=Path)
    candidate_materialize_parser.add_argument("--destination", type=Path, required=True)

    experiment_parser = subparsers.add_parser(
        "experiment", help="validate an open-ended experiment plan"
    )
    experiment_subparsers = experiment_parser.add_subparsers(
        dest="experiment_command", required=True
    )
    experiment_validate_parser = experiment_subparsers.add_parser(
        "validate", help="validate completion and decision boundaries"
    )
    experiment_validate_parser.add_argument("plan", type=Path)

    agent_eval_parser = subparsers.add_parser(
        "agent-eval", help="run a soft advisory agent evaluator"
    )
    agent_eval_subparsers = agent_eval_parser.add_subparsers(
        dest="agent_eval_command", required=True
    )
    agent_eval_run_parser = agent_eval_subparsers.add_parser(
        "run", help="review a resulting README from one evaluator perspective"
    )
    agent_eval_run_parser.add_argument("evaluator", type=Path)
    agent_eval_run_parser.add_argument("--repository", type=Path, required=True)
    agent_eval_run_parser.add_argument("--readme", required=True)
    agent_eval_run_parser.add_argument("--run-dir", type=Path, required=True)
    agent_eval_run_parser.add_argument("--run-id", required=True)
    agent_eval_run_parser.add_argument("--candidate-id", required=True)
    agent_eval_run_parser.add_argument("--model", required=True)
    agent_eval_run_parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default="high",
    )
    agent_eval_run_parser.add_argument("--codex-executable", default="codex")
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
    if args.command == "capsule" and args.capsule_command == "run":
        result = run_codex_capsule(
            args.capsule,
            workspace=args.workspace,
            run_dir=args.run_dir,
            run_id=args.run_id,
            artifact_revision=args.artifact_revision,
            plugin_id=args.plugin_id,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "capsule" and args.capsule_command == "score":
        score = score_review_response(
            args.capsule,
            args.response,
            events_path=args.events,
            stderr_path=args.stderr,
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(score, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(score, indent=2, sort_keys=True))
        return 0
    if args.command == "corpus" and args.corpus_command == "collect":
        result = collect_corpus(
            args.manifest,
            cache_dir=args.cache,
            observations_path=args.observations,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "corpus" and args.corpus_command == "summarize":
        summary = summarize_observations(args.observations)
        if args.output:
            write_summary(args.output, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "intake" and args.intake_command == "fingerprint":
        fingerprint = fingerprint_git_path(
            args.source_root,
            revision=args.revision,
            source_path=args.path,
            artifact_type=args.artifact_type,
        )
        print(json.dumps(fingerprint, indent=2, sort_keys=True))
        return 0
    if args.command == "intake" and args.intake_command == "verify":
        verification = verify_intake_manifest(
            args.manifest, source_root=args.source_root
        )
        print(json.dumps(verification, indent=2, sort_keys=True))
        return 0 if verification["verified"] else 1
    if args.command == "candidate" and args.candidate_command == "verify":
        verification = verify_candidate(args.candidate)
        print(json.dumps(verification, indent=2, sort_keys=True))
        return 0 if verification["verified"] else 1
    if args.command == "candidate" and args.candidate_command == "materialize":
        materialization = materialize_candidate(
            args.candidate, args.destination
        )
        print(json.dumps(materialization, indent=2, sort_keys=True))
        return 0
    if args.command == "experiment" and args.experiment_command == "validate":
        plan = load_experiment_plan(args.plan)
        print(
            json.dumps(
                {
                    "experiment_id": plan["id"],
                    "planned_trial_count": len(plan["planned_trials"]),
                    "automated_results_authority": plan["completion_policy"][
                        "automated_results_authority"
                    ],
                    "valid": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "agent-eval" and args.agent_eval_command == "run":
        run = run_agent_evaluation(
            args.evaluator,
            repository=args.repository,
            readme_path=args.readme,
            run_dir=args.run_dir,
            run_id=args.run_id,
            candidate_id=args.candidate_id,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            codex_executable=args.codex_executable,
        )
        print(json.dumps(run, indent=2, sort_keys=True))
        return 0 if run["result"] == "completed" else 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
