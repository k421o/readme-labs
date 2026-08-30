# README domain extraction from Repository Guidance — 2026-08-29

> **Historical migration record.** This document describes the concurrent
> `v0.1.0` extraction as it was released. PR #1 later reconciles that
> plugin-first snapshot with the domain-first repository architecture. The tag
> remains immutable, but current source authority, capability paths, and release
> gates are defined by the root README, `docs/domain-charter.md`, and
> `docs/release-policy.md`.

This is the repository-local migration record for the first README Labs
release. The cross-repository decision model and validation live in
[Agent Ops issue #44](https://github.com/k421o/agent-ops/issues/44).

## Provenance and decision

- Originating Codex session: `01a05036-1c5b-7db0-a9f8-508ea45aaa0f`
  (`Research README best practices`, 2026-08-29, America/New_York).
- Source authority before extraction:
  [`repository-guidance@7b96fff`](https://github.com/k421o/repository-guidance/tree/7b96ffff7e1b36fd194bb52b4fa4fbfcb6ade52a)
  plus draft anatomy head
  [`ef4e054`](https://github.com/k421o/repository-guidance/tree/ef4e05476cbe70e0f390a0501b6d9d8e2cd8fab1).
- Source reviews:
  [repository-guidance PR #3](https://github.com/k421o/repository-guidance/pull/3)
  and [draft PR #5](https://github.com/k421o/repository-guidance/pull/5).
- Source authority after extraction: `k421o/readme-labs` release `v0.1.0`.
- Downstream consumer: `k421o/repository-guidance`, which owns its AGENTS.md
  capability, baseline-checkpoint workflow, evaluation harness, and plugin
  routing.

README identity, research cadence, delivery contracts, rendering and registry
concerns, and review consumers form a domain distinct from ambient agent
instructions. The split is not justified by research-file count.

## Artifact classification

| Artifact | Classification and disposition |
| --- | --- |
| `skills/readme-contract-review/` | Canonical README-domain skill; moved here and removed from the former parent. |
| `research/**` | Canonical README research; moved here and removed from the former parent. |
| Draft anatomy files from repository-guidance PR #5 | Canonical research; moved under `research/` here. |
| `skills/agents-guidance-review/` | Repository Guidance source; retained there. |
| `skills/document-baseline-checkpoint/` | Repository Guidance source; retained there because it is a generic, explicitly invoked Git workflow. |
| `guidance-eval`, scenarios, oracles, scorecards, and candidate snapshot | Repository Guidance source or historical evaluation evidence; retained there. The candidate's README material is a pinned historical fixture, not a current editable authority. |
| Raw README corpus | None exists in this migration. Future manifests and schemas begin here; raw data separates only on an evidenced data lifecycle. |

The extraction copies the reviewed snapshots rather than importing unrelated
Repository Guidance history. Original authorship and evolution remain
available in PRs #3 and #5 and their exact source commits above. The first
README Labs commit and release record the adapted destination snapshot.

## Dependency and release contract

`readme-labs` is upstream. `repository-guidance` must point users to the
immutable `v0.1.0` release and release commit, and must not retain an editable
README skill or research copy. No README Labs code depends on Repository
Guidance implementation.

The current evaluation harness stays downstream. Its README-aware oracles and
historical candidate remain integration/evaluation evidence; they do not
publish README policy. A second independent domain must force and validate a
domain-neutral extension before the harness can become shared infrastructure.

## Migration and validation

- Both source checkouts were clean before isolated migration worktrees were
  created; unrelated changes in the Agent Ops canonical checkout were not
  touched.
- Extracted Markdown contains no active absolute user checkout or `~/dev` path.
- `python3 tools/validate_repository.py` checks manifest agreement, the skill
  entry point, local links, and checkout-path independence.
- README Labs CI runs that deterministic check on pull requests and `main`.
- Repository Guidance must pass its existing Ruff and pytest suite after
  source removal and consumer repointing.
- The `v0.1.0` release is created from the merged README Labs default branch
  before the downstream removal merges.

Rollback during the initial compatibility window means pinning Repository
Guidance temporarily to its last pre-extraction commit (`7b96fff`) while a
corrected README Labs release is prepared. It must not create a new editable
copy on Repository Guidance `main`. The migration is complete only after both
default branches, the release, and active repository references agree on one
source authority.
