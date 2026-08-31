"""Command-line entry point for readme-labs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from readme_lab.agent_evaluation import run_agent_evaluation
from readme_lab.candidates import materialize_candidate, verify_candidate
from readme_lab.capsule import materialize_capsule
from readme_lab.corpus import collect_corpus, summarize_observations, write_summary
from readme_lab.evaluation import run_codex_capsule, score_review_response
from readme_lab.experiments import load_experiment_plan
from readme_lab.ingestion import (
    add_ingestion_selection,
    admit_ingestion,
    begin_ingestion,
    create_external_action_plan,
    finalize_ingestion,
    initialize_ingestion_yard,
    link_existing_admission,
    load_ingestion_job,
    quarantine_ingestion,
    refresh_ingestion_inventory,
    verify_ingestion,
)
from readme_lab.ingestion_actions import (
    execute_github_action,
    execute_source_cleanup,
)
from readme_lab.inspect import ROLE_IDS, inspect_readme
from readme_lab.intake import fingerprint_git_path, verify_intake_manifest
from readme_lab.migration import (
    build_git_migration_receipt,
    write_git_migration_receipt,
)
from readme_lab.readme_artifacts import (
    add_artifact_lineage,
    add_artifact_membership,
    add_artifact_occurrence,
    add_artifact_provenance,
    attach_observation_evidence,
    attach_soft_review_evidence,
    attach_static_analysis_evidence,
    capture_readme_artifact,
    inspect_captured_artifact,
    load_artifact_record,
    register_reference_artifact,
    verify_artifact_package,
)
from readme_lab.readme_catalog import build_sqlite_catalog, write_artifact_report
from readme_lab.static_analysis import (
    load_static_analysis_run,
    run_corpus_static_analysis,
    run_document_static_analysis,
)


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

    ingest_parser = subparsers.add_parser(
        "ingest", help="manage isolated repository and directory ingestion"
    )
    ingest_subparsers = ingest_parser.add_subparsers(
        dest="ingest_command", required=True
    )
    ingest_init = ingest_subparsers.add_parser(
        "init", help="initialize a non-Git README domain ingestion yard"
    )
    ingest_init.add_argument("--domain-root", type=Path, required=True)
    ingest_begin = ingest_subparsers.add_parser(
        "begin", help="acquire and inventory one isolated source"
    )
    ingest_begin.add_argument("source")
    ingest_begin.add_argument("--domain-root", type=Path, required=True)
    ingest_begin.add_argument("--job-id", required=True)
    ingest_begin.add_argument(
        "--remote-policy",
        choices=("sever", "fetch_only", "preserve"),
        default="sever",
    )
    ingest_begin.add_argument(
        "--ownership", choices=("owned", "external", "unknown"), default="unknown"
    )
    ingest_begin.add_argument("--repository-id")
    ingest_begin.add_argument("--include-ignored", action="store_true")
    ingest_begin.add_argument(
        "--lfs-policy", choices=("pointers", "fetch"), default="pointers"
    )
    ingest_begin.add_argument(
        "--submodule-policy", choices=("record", "fetch"), default="record"
    )
    ingest_inventory = ingest_subparsers.add_parser(
        "inventory", help="refresh a managed checkout inventory"
    )
    ingest_inventory.add_argument("--yard", type=Path, required=True)
    ingest_inventory.add_argument("--job-id", required=True)
    ingest_status = ingest_subparsers.add_parser(
        "status", help="show one ingestion job"
    )
    ingest_status.add_argument("--yard", type=Path, required=True)
    ingest_status.add_argument("--job-id", required=True)
    ingest_select = ingest_subparsers.add_parser(
        "select", help="add one exact artifact selection"
    )
    ingest_select.add_argument("--yard", type=Path, required=True)
    ingest_select.add_argument("--job-id", required=True)
    ingest_select.add_argument("--selection-id", required=True)
    ingest_select.add_argument("--path", required=True)
    ingest_select.add_argument(
        "--role",
        required=True,
        choices=(
            "readme_artifact",
            "skill",
            "skill_bundle",
            "research_content",
            "research_method",
            "research_protocol",
            "research_data",
            "evaluation_method",
            "trial_evidence",
            "whole_solution",
        ),
    )
    ingest_select.add_argument(
        "--preservation",
        required=True,
        choices=("reference", "selected", "replayable", "archive", "git_migration"),
    )
    ingest_select.add_argument("--context", action="append", default=[])
    ingest_select.add_argument("--candidate-id")
    ingest_select.add_argument(
        "--candidate-kind",
        choices=(
            "skill",
            "skill_bundle",
            "plugin",
            "research_method",
            "evaluation_method",
            "workflow",
            "repository_solution",
            "other",
        ),
    )
    ingest_select.add_argument("--candidate-format")
    ingest_select.add_argument("--candidate-entrypoint")
    ingest_admit = ingest_subparsers.add_parser(
        "admit", help="generate domain records or link already-landed records"
    )
    ingest_admit.add_argument("--yard", type=Path, required=True)
    ingest_admit.add_argument("--job-id", required=True)
    ingest_admit.add_argument("--domain-repository", type=Path, required=True)
    ingest_admit.add_argument("--manifest-id")
    ingest_admit.add_argument("--title")
    ingest_admit.add_argument(
        "--link-target",
        action="append",
        default=[],
        metavar="KIND=REPOSITORY_PATH",
    )
    ingest_verify = ingest_subparsers.add_parser(
        "verify", help="verify source selections and durable targets"
    )
    ingest_verify.add_argument("--yard", type=Path, required=True)
    ingest_verify.add_argument("--job-id", required=True)
    ingest_verify.add_argument("--domain-repository", type=Path, required=True)
    ingest_finalize = ingest_subparsers.add_parser(
        "finalize", help="settle a verified checkout and emit a receipt"
    )
    ingest_finalize.add_argument("--yard", type=Path, required=True)
    ingest_finalize.add_argument("--job-id", required=True)
    ingest_finalize.add_argument("--domain-repository", type=Path, required=True)
    ingest_finalize.add_argument(
        "--workspace-disposition",
        choices=("retain", "delete", "archive_local"),
        required=True,
    )
    ingest_finalize.add_argument(
        "--remote-disposition",
        choices=("none", "publish_private", "archive_owned", "owned_git_migration"),
        default="none",
    )
    ingest_finalize.add_argument("--migration-receipt", action="append", default=[])
    ingest_finalize.add_argument("--limitation", action="append", default=[])
    ingest_finalize.add_argument("--no-export-receipt", action="store_true")
    ingest_quarantine = ingest_subparsers.add_parser(
        "quarantine", help="move an unfinished job aside without rejecting it"
    )
    ingest_quarantine.add_argument("--yard", type=Path, required=True)
    ingest_quarantine.add_argument("--job-id", required=True)
    ingest_quarantine.add_argument("--reason", required=True)
    ingest_plan = ingest_subparsers.add_parser(
        "plan-action", help="record a dry-run-first external or cleanup action"
    )
    ingest_plan.add_argument("--yard", type=Path, required=True)
    ingest_plan.add_argument("--job-id", required=True)
    ingest_plan.add_argument("--action-id", required=True)
    ingest_plan.add_argument(
        "--action",
        choices=("publish_private", "archive_owned", "source_cleanup"),
        required=True,
    )
    ingest_plan.add_argument("--parameters", type=Path, required=True)
    ingest_execute_github = ingest_subparsers.add_parser(
        "execute-github", help="dry-run or explicitly execute a GitHub action plan"
    )
    ingest_execute_github.add_argument("--yard", type=Path, required=True)
    ingest_execute_github.add_argument("--plan", type=Path, required=True)
    ingest_execute_github.add_argument("--execute", action="store_true")
    ingest_execute_github.add_argument("--gh-executable", default="gh")
    ingest_execute_cleanup = ingest_subparsers.add_parser(
        "execute-source-cleanup",
        help="dry-run or physically remove and settle exact owned source paths",
    )
    ingest_execute_cleanup.add_argument("--yard", type=Path, required=True)
    ingest_execute_cleanup.add_argument("--plan", type=Path, required=True)
    ingest_execute_cleanup.add_argument("--authorized-source", type=Path, required=True)
    ingest_execute_cleanup.add_argument("--domain-repository", type=Path, required=True)
    ingest_execute_cleanup.add_argument("--execute", action="store_true")
    ingest_execute_cleanup.add_argument("--gh-executable", default="gh")
    ingest_migration = ingest_subparsers.add_parser(
        "migration-receipt",
        help="record an already-settled Git-to-Git migration without duplicate bytes",
    )
    ingest_migration.add_argument("--receipt-id", required=True)
    ingest_migration.add_argument("--output", type=Path, required=True)
    ingest_migration.add_argument("--source-repository", type=Path, required=True)
    ingest_migration.add_argument("--source-repository-id", required=True)
    ingest_migration.add_argument("--source-revision", required=True)
    ingest_migration.add_argument("--source-path", required=True)
    ingest_migration.add_argument("--source-deletion-revision", required=True)
    ingest_migration.add_argument("--destination-repository", type=Path, required=True)
    ingest_migration.add_argument("--destination-repository-id", required=True)
    ingest_migration.add_argument("--destination-revision", required=True)
    ingest_migration.add_argument("--destination-path", required=True)
    ingest_migration.add_argument(
        "--artifact-type", choices=("file", "tree"), required=True
    )
    ingest_migration.add_argument(
        "--source-settlement",
        choices=("local_commit", "pushed", "pr_open", "merged"),
        required=True,
    )
    ingest_migration.add_argument(
        "--destination-settlement",
        choices=("local_commit", "pushed", "pr_open", "merged"),
        required=True,
    )
    ingest_migration.add_argument(
        "--source-ownership-basis",
        choices=("explicit_owner_assertion", "github_admin_verified"),
        default="explicit_owner_assertion",
    )
    ingest_migration.add_argument(
        "--destination-ownership-basis",
        choices=("explicit_owner_assertion", "github_admin_verified"),
        default="explicit_owner_assertion",
    )
    ingest_migration.add_argument("--reference", action="append", default=[])
    ingest_migration.add_argument("--limitation", action="append", default=[])

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

    static_analysis_parser = subparsers.add_parser(
        "static-analysis", help="run evidence-only static README analyzers"
    )
    static_analysis_subparsers = static_analysis_parser.add_subparsers(
        dest="static_analysis_command", required=True
    )
    static_analysis_run = static_analysis_subparsers.add_parser(
        "run", help="produce diagnostics for one README artifact"
    )
    static_analysis_run.add_argument("analyzer", type=Path)
    static_analysis_run.add_argument("readme", type=Path)
    static_analysis_run.add_argument("--output", type=Path, required=True)
    static_analysis_run.add_argument("--run-id", required=True)
    static_analysis_run.add_argument("--subject-id", required=True)
    static_analysis_run.add_argument(
        "--source-kind",
        choices=("local", "generated", "ingested", "candidate"),
        required=True,
    )
    static_analysis_run.add_argument("--recorded-path")
    static_analysis_run.add_argument("--repository")
    static_analysis_run.add_argument("--revision")
    static_analysis_run.add_argument(
        "--profile", choices=("feedback", "all"), default="feedback"
    )
    static_analysis_corpus = static_analysis_subparsers.add_parser(
        "corpus", help="characterize an analyzer on a pinned README corpus"
    )
    static_analysis_corpus.add_argument("analyzer", type=Path)
    static_analysis_corpus.add_argument("manifest", type=Path)
    static_analysis_corpus.add_argument("--cache", type=Path, required=True)
    static_analysis_corpus.add_argument("--output", type=Path, required=True)
    static_analysis_corpus.add_argument("--run-id", required=True)
    static_analysis_verify = static_analysis_subparsers.add_parser(
        "verify", help="validate a run envelope against its exact analyzer spec"
    )
    static_analysis_verify.add_argument("analyzer", type=Path)
    static_analysis_verify.add_argument("run", type=Path)

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

    artifact_parser = subparsers.add_parser(
        "artifact", help="capture and verify document-centered README records"
    )
    artifact_subparsers = artifact_parser.add_subparsers(
        dest="artifact_command", required=True
    )
    artifact_capture = artifact_subparsers.add_parser(
        "capture", help="capture a selected completed README without editing its source"
    )
    artifact_capture.add_argument("source", type=Path)
    artifact_capture.add_argument("--registry", type=Path, required=True)
    artifact_capture.add_argument(
        "--provenance-kind",
        choices=("generated", "ingested", "authored", "synthetic"),
        required=True,
    )
    artifact_capture.add_argument(
        "--boundary",
        choices=(
            "completed_generation",
            "ingestion_selection",
            "explicit_manual_capture",
        ),
        required=True,
    )
    artifact_capture.add_argument(
        "--pre-capture-editability",
        choices=("mutable", "not_applicable", "unknown"),
        required=True,
    )
    artifact_capture.add_argument(
        "--ownership", choices=("owned", "third_party", "unknown"), required=True
    )
    artifact_capture.add_argument(
        "--visibility",
        choices=("public", "private", "local_only", "unknown"),
        required=True,
    )
    artifact_capture.add_argument("--repository")
    artifact_capture.add_argument("--revision")
    artifact_capture.add_argument("--recorded-path")
    artifact_capture.add_argument("--role", default="unspecified")
    artifact_capture.add_argument("--tree")
    artifact_capture.add_argument(
        "--producer-kind",
        choices=("skill", "candidate", "workflow", "human", "other"),
    )
    artifact_capture.add_argument("--producer-id")
    artifact_capture.add_argument("--producer-version")
    artifact_capture.add_argument("--producer-run-id")
    artifact_capture.add_argument(
        "--membership", action="append", default=[], metavar="COLLECTION=PURPOSE"
    )
    artifact_capture.add_argument("--captured-at")
    artifact_capture.add_argument("--license-spdx")
    artifact_capture.add_argument("--limitation", action="append", default=[])

    artifact_reference = artifact_subparsers.add_parser(
        "reference",
        help="register pinned source identity without copying the README body",
    )
    artifact_reference.add_argument("--registry", type=Path, required=True)
    artifact_reference.add_argument("--content-sha256", required=True)
    artifact_reference.add_argument("--locator", required=True)
    artifact_reference.add_argument("--repository", required=True)
    artifact_reference.add_argument("--revision", required=True)
    artifact_reference.add_argument("--recorded-path", required=True)
    artifact_reference.add_argument("--role", required=True)
    artifact_reference.add_argument(
        "--ownership",
        choices=("owned", "third_party", "unknown"),
        default="third_party",
    )
    artifact_reference.add_argument(
        "--visibility",
        choices=("public", "private", "local_only", "unknown"),
        default="public",
    )
    artifact_reference.add_argument("--byte-length", type=int)
    artifact_reference.add_argument("--original-name", default="README.md")
    artifact_reference.add_argument(
        "--membership", action="append", default=[], metavar="COLLECTION=PURPOSE"
    )
    artifact_reference.add_argument("--captured-at")
    artifact_reference.add_argument("--license-spdx")
    artifact_reference.add_argument("--limitation", action="append", default=[])

    artifact_verify = artifact_subparsers.add_parser(
        "verify", help="verify artifact identity, storage, and metadata"
    )
    artifact_verify.add_argument("record", type=Path)
    artifact_verify.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )

    artifact_occurrence = artifact_subparsers.add_parser(
        "add-occurrence",
        help="record another repository placement for the same captured bytes",
    )
    artifact_occurrence.add_argument("record", type=Path)
    artifact_occurrence.add_argument("--repository", required=True)
    artifact_occurrence.add_argument("--revision", required=True)
    artifact_occurrence.add_argument("--recorded-path", required=True)
    artifact_occurrence.add_argument("--role", required=True)
    artifact_occurrence.add_argument("--tree")
    artifact_occurrence.add_argument("--retrieval-url")

    artifact_provenance = artifact_subparsers.add_parser(
        "add-provenance",
        help="record another origin event without changing captured bytes",
    )
    artifact_provenance.add_argument("record", type=Path)
    artifact_provenance.add_argument(
        "--kind",
        choices=("generated", "retrieved", "ingested", "authored", "synthetic"),
        required=True,
    )
    artifact_provenance.add_argument("--recorded-at", required=True)
    artifact_provenance.add_argument("--repository")
    artifact_provenance.add_argument("--revision")
    artifact_provenance.add_argument("--recorded-path")
    artifact_provenance.add_argument("--locator")
    artifact_provenance.add_argument(
        "--producer-kind",
        choices=("skill", "candidate", "workflow", "human", "other"),
    )
    artifact_provenance.add_argument("--producer-id")
    artifact_provenance.add_argument("--producer-version")
    artifact_provenance.add_argument("--producer-run-id")
    artifact_provenance.add_argument("--limitation", action="append", default=[])

    artifact_membership = artifact_subparsers.add_parser(
        "add-membership",
        help="add a collection purpose independently of artifact provenance",
    )
    artifact_membership.add_argument("record", type=Path)
    artifact_membership.add_argument("--collection", required=True)
    artifact_membership.add_argument(
        "--purpose",
        choices=(
            "reference_sample",
            "generated_output",
            "candidate_output",
            "fixture",
            "regression_baseline",
            "accepted_example",
            "personal_corpus",
            "experiment_subject",
        ),
        required=True,
    )
    artifact_membership.add_argument("--recorded-at", required=True)

    artifact_lineage = artifact_subparsers.add_parser(
        "add-lineage", help="relate a captured revision to another artifact"
    )
    artifact_lineage.add_argument("record", type=Path)
    artifact_lineage.add_argument(
        "--relationship",
        choices=("derived_from", "variant_of", "supersedes", "reproduces"),
        required=True,
    )
    artifact_lineage.add_argument("--target-record-id")
    artifact_lineage.add_argument("--target-artifact-id")
    artifact_lineage.add_argument("--note")

    artifact_inspect = artifact_subparsers.add_parser(
        "inspect", help="attach a structural observation of captured artifact bytes"
    )
    artifact_inspect.add_argument("record", type=Path)
    artifact_inspect.add_argument("--occurrence-id", required=True)
    artifact_inspect.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )
    artifact_inspect.add_argument("--observed-at")

    artifact_attach_observation = artifact_subparsers.add_parser(
        "attach-observation",
        help="attach one existing READMEObservation by exact content identity",
    )
    artifact_attach_observation.add_argument("record", type=Path)
    artifact_attach_observation.add_argument("observation", type=Path)
    artifact_attach_observation.add_argument("--document-id")
    artifact_attach_observation.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )

    artifact_attach_static = artifact_subparsers.add_parser(
        "attach-static",
        help="attach one subject from a verified static-analysis run",
    )
    artifact_attach_static.add_argument("record", type=Path)
    artifact_attach_static.add_argument("run", type=Path)
    artifact_attach_static.add_argument("--analyzer", type=Path, required=True)
    artifact_attach_static.add_argument("--subject-id", required=True)
    artifact_attach_static.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )

    artifact_attach_review = artifact_subparsers.add_parser(
        "attach-review",
        help="attach a soft review to its exact repository occurrence",
    )
    artifact_attach_review.add_argument("record", type=Path)
    artifact_attach_review.add_argument("run_dir", type=Path)
    artifact_attach_review.add_argument("--evaluator", type=Path, required=True)
    artifact_attach_review.add_argument("--occurrence-id", required=True)
    artifact_attach_review.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )

    artifact_report = artifact_subparsers.add_parser(
        "report", help="generate or check the human-readable evidence projection"
    )
    artifact_report.add_argument("record", type=Path)
    artifact_report.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )
    artifact_report.add_argument("--check", action="store_true")

    artifact_catalog = artifact_subparsers.add_parser(
        "catalog", help="rebuild a disposable SQLite index from JSON records"
    )
    artifact_catalog.add_argument("records", type=Path)
    artifact_catalog.add_argument("--output", type=Path, required=True)
    artifact_catalog.add_argument(
        "--repository-root", type=Path, default=Path.cwd()
    )
    return parser


def _memberships(values: list[str]) -> list[tuple[str, str]]:
    memberships = []
    for value in values:
        if "=" not in value:
            raise ValueError("memberships use COLLECTION=PURPOSE")
        collection, purpose = value.split("=", 1)
        if not collection or not purpose:
            raise ValueError("memberships require both collection and purpose")
        memberships.append((collection, purpose))
    return memberships


def _optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _producer(args: argparse.Namespace) -> dict[str, str | None] | None:
    supplied = any(
        value is not None
        for value in (
            args.producer_kind,
            args.producer_id,
            args.producer_version,
            args.producer_run_id,
        )
    )
    if not supplied:
        return None
    if args.producer_kind is None or args.producer_id is None:
        raise ValueError("producer metadata requires --producer-kind and --producer-id")
    return {
        "kind": args.producer_kind,
        "id": args.producer_id,
        "version": args.producer_version,
        "run_id": args.producer_run_id,
    }


def _print_evidence(path: Path) -> None:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "evidence_path": path.as_posix(),
                "evidence_id": evidence["evidence_id"],
                "kind": evidence["kind"],
                "result": evidence["result"],
            },
            indent=2,
            sort_keys=True,
        )
    )


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
    if args.command == "ingest" and args.ingest_command == "init":
        yard = initialize_ingestion_yard(args.domain_root)
        print(json.dumps({"yard": yard.as_posix()}, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "begin":
        job = begin_ingestion(
            domain_root=args.domain_root,
            job_id=args.job_id,
            source=args.source,
            remote_policy=args.remote_policy,
            ownership=args.ownership,
            repository_id=args.repository_id,
            include_ignored=args.include_ignored,
            lfs_policy=args.lfs_policy,
            submodule_policy=args.submodule_policy,
        )
        print(json.dumps(job, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "inventory":
        inventory = refresh_ingestion_inventory(yard=args.yard, job_id=args.job_id)
        print(json.dumps(inventory, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "status":
        job = load_ingestion_job(args.yard, args.job_id)
        print(json.dumps(job, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "select":
        selection = add_ingestion_selection(
            yard=args.yard,
            job_id=args.job_id,
            selection_id=args.selection_id,
            source_path=args.path,
            role=args.role,
            preservation=args.preservation,
            context_paths=args.context,
            candidate_id=args.candidate_id,
            candidate_kind=args.candidate_kind,
            candidate_format=args.candidate_format,
            candidate_entrypoint=args.candidate_entrypoint,
        )
        print(json.dumps(selection, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "admit":
        if args.link_target:
            targets = []
            for raw in args.link_target:
                if "=" not in raw:
                    raise ValueError("linked targets use KIND=REPOSITORY_PATH")
                targets.append(tuple(raw.split("=", 1)))
            admission = link_existing_admission(
                yard=args.yard,
                job_id=args.job_id,
                domain_repository=args.domain_repository,
                targets=targets,
            )
        else:
            if not args.manifest_id or not args.title:
                raise ValueError(
                    "generated admission requires --manifest-id and --title"
                )
            admission = admit_ingestion(
                yard=args.yard,
                job_id=args.job_id,
                domain_repository=args.domain_repository,
                manifest_id=args.manifest_id,
                title=args.title,
            )
        print(json.dumps(admission, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "verify":
        result = verify_ingestion(
            yard=args.yard,
            job_id=args.job_id,
            domain_repository=args.domain_repository,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "finalize":
        result = finalize_ingestion(
            yard=args.yard,
            job_id=args.job_id,
            domain_repository=args.domain_repository,
            workspace_disposition=args.workspace_disposition,
            remote_disposition=args.remote_disposition,
            export_receipt=not args.no_export_receipt,
            migration_receipts=args.migration_receipt,
            limitations=args.limitation,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "quarantine":
        destination = quarantine_ingestion(
            yard=args.yard, job_id=args.job_id, reason=args.reason
        )
        print(
            json.dumps(
                {"job_id": args.job_id, "quarantined_at": destination.as_posix()},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "ingest" and args.ingest_command == "plan-action":
        parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
        plan = create_external_action_plan(
            yard=args.yard,
            job_id=args.job_id,
            action_id=args.action_id,
            action=args.action,
            parameters=parameters,
        )
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "execute-github":
        result = execute_github_action(
            yard=args.yard,
            plan_path=args.plan,
            execute=args.execute,
            gh_executable=args.gh_executable,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "execute-source-cleanup":
        result = execute_source_cleanup(
            yard=args.yard,
            plan_path=args.plan,
            authorized_source=args.authorized_source,
            domain_repository=args.domain_repository,
            execute=args.execute,
            gh_executable=args.gh_executable,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "ingest" and args.ingest_command == "migration-receipt":
        receipt = build_git_migration_receipt(
            receipt_id=args.receipt_id,
            source_repository=args.source_repository,
            source_repository_id=args.source_repository_id,
            source_revision=args.source_revision,
            source_path=args.source_path,
            source_deletion_revision=args.source_deletion_revision,
            destination_repository=args.destination_repository,
            destination_repository_id=args.destination_repository_id,
            destination_revision=args.destination_revision,
            destination_path=args.destination_path,
            artifact_type=args.artifact_type,
            source_settlement=args.source_settlement,
            destination_settlement=args.destination_settlement,
            source_ownership_basis=args.source_ownership_basis,
            destination_ownership_basis=args.destination_ownership_basis,
            references=args.reference,
            limitations=args.limitation,
        )
        write_git_migration_receipt(args.output, receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    if args.command == "candidate" and args.candidate_command == "verify":
        verification = verify_candidate(args.candidate)
        print(json.dumps(verification, indent=2, sort_keys=True))
        return 0 if verification["verified"] else 1
    if args.command == "candidate" and args.candidate_command == "materialize":
        materialization = materialize_candidate(args.candidate, args.destination)
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
    if args.command == "static-analysis" and args.static_analysis_command == "run":
        run = run_document_static_analysis(
            args.analyzer,
            readme_path=args.readme,
            output=args.output,
            run_id=args.run_id,
            subject_id=args.subject_id,
            source_kind=args.source_kind,
            recorded_path=args.recorded_path,
            repository=args.repository,
            revision=args.revision,
            profile=args.profile,
        )
        print(json.dumps(run, indent=2, sort_keys=True))
        return 0 if run["result"] == "completed" else 1
    if (
        args.command == "static-analysis"
        and args.static_analysis_command == "corpus"
    ):
        run = run_corpus_static_analysis(
            args.analyzer,
            manifest_path=args.manifest,
            cache_dir=args.cache,
            output=args.output,
            run_id=args.run_id,
        )
        print(json.dumps(run, indent=2, sort_keys=True))
        return 0 if run["result"] == "completed" else 1
    if (
        args.command == "static-analysis"
        and args.static_analysis_command == "verify"
    ):
        run = load_static_analysis_run(args.run, analyzer_path=args.analyzer)
        print(
            json.dumps(
                {
                    "run_id": run["run_id"],
                    "mode": run["mode"],
                    "result": run["result"],
                    "summary": run["summary"],
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
    if args.command == "artifact" and args.artifact_command == "capture":
        record_dir = capture_readme_artifact(
            args.source,
            registry=args.registry,
            provenance_kind=args.provenance_kind,
            boundary=args.boundary,
            pre_capture_editability=args.pre_capture_editability,
            ownership=args.ownership,
            visibility=args.visibility,
            repository=args.repository,
            revision=args.revision,
            recorded_path=args.recorded_path,
            role=args.role,
            tree=args.tree,
            producer=_producer(args),
            memberships=_memberships(args.membership),
            captured_at=_optional_datetime(args.captured_at),
            license_spdx=args.license_spdx,
            limitations=args.limitation,
        )
        record = load_artifact_record(record_dir)
        print(
            json.dumps(
                {
                    "record_dir": record_dir.as_posix(),
                    "record_id": record["record_id"],
                    "artifact_id": record["artifact"]["id"],
                    "valid": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "artifact" and args.artifact_command == "reference":
        record_dir = register_reference_artifact(
            registry=args.registry,
            content_sha256=args.content_sha256,
            locator=args.locator,
            repository=args.repository,
            revision=args.revision,
            recorded_path=args.recorded_path,
            role=args.role,
            ownership=args.ownership,
            visibility=args.visibility,
            byte_length=args.byte_length,
            original_name=args.original_name,
            memberships=_memberships(args.membership),
            captured_at=_optional_datetime(args.captured_at),
            license_spdx=args.license_spdx,
            limitations=args.limitation,
        )
        record = load_artifact_record(record_dir)
        print(
            json.dumps(
                {
                    "record_dir": record_dir.as_posix(),
                    "record_id": record["record_id"],
                    "artifact_id": record["artifact"]["id"],
                    "valid": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "artifact" and args.artifact_command == "add-occurrence":
        occurrence = add_artifact_occurrence(
            args.record,
            repository=args.repository,
            revision=args.revision,
            recorded_path=args.recorded_path,
            role=args.role,
            tree=args.tree,
            retrieval_url=args.retrieval_url,
        )
        print(json.dumps(occurrence, indent=2, sort_keys=True))
        return 0
    if args.command == "artifact" and args.artifact_command == "add-provenance":
        provenance = add_artifact_provenance(
            args.record,
            kind=args.kind,
            recorded_at=_optional_datetime(args.recorded_at),
            repository=args.repository,
            revision=args.revision,
            recorded_path=args.recorded_path,
            locator=args.locator,
            producer=_producer(args),
            limitations=args.limitation,
        )
        print(json.dumps(provenance, indent=2, sort_keys=True))
        return 0
    if args.command == "artifact" and args.artifact_command == "add-membership":
        membership = add_artifact_membership(
            args.record,
            collection_id=args.collection,
            purpose=args.purpose,
            recorded_at=_optional_datetime(args.recorded_at),
        )
        print(json.dumps(membership, indent=2, sort_keys=True))
        return 0
    if args.command == "artifact" and args.artifact_command == "add-lineage":
        lineage = add_artifact_lineage(
            args.record,
            relationship=args.relationship,
            target_record_id=args.target_record_id,
            target_artifact_id=args.target_artifact_id,
            note=args.note,
        )
        print(json.dumps(lineage, indent=2, sort_keys=True))
        return 0
    if args.command == "artifact" and args.artifact_command == "inspect":
        evidence_path = inspect_captured_artifact(
            args.record,
            occurrence_id=args.occurrence_id,
            repository_root=args.repository_root,
            observed_at=_optional_datetime(args.observed_at),
        )
        _print_evidence(evidence_path)
        return 0
    if (
        args.command == "artifact"
        and args.artifact_command == "attach-observation"
    ):
        evidence_path = attach_observation_evidence(
            args.record,
            observations_path=args.observation,
            repository_root=args.repository_root,
            document_id=args.document_id,
        )
        _print_evidence(evidence_path)
        return 0
    if args.command == "artifact" and args.artifact_command == "attach-static":
        evidence_path = attach_static_analysis_evidence(
            args.record,
            run_path=args.run,
            analyzer_path=args.analyzer,
            subject_id=args.subject_id,
            repository_root=args.repository_root,
        )
        _print_evidence(evidence_path)
        return 0
    if args.command == "artifact" and args.artifact_command == "attach-review":
        evidence_path = attach_soft_review_evidence(
            args.record,
            run_dir=args.run_dir,
            evaluator_path=args.evaluator,
            occurrence_id=args.occurrence_id,
            repository_root=args.repository_root,
        )
        _print_evidence(evidence_path)
        return 0
    if args.command == "artifact" and args.artifact_command == "report":
        report = write_artifact_report(
            args.record,
            repository_root=args.repository_root,
            check=args.check,
        )
        print(
            json.dumps(
                {"report": report.as_posix(), "checked": args.check},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "artifact" and args.artifact_command == "catalog":
        result = build_sqlite_catalog(
            args.records,
            output=args.output,
            repository_root=args.repository_root,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "artifact" and args.artifact_command == "verify":
        verification = verify_artifact_package(
            args.record, repository_root=args.repository_root
        )
        print(json.dumps(verification, indent=2, sort_keys=True))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
