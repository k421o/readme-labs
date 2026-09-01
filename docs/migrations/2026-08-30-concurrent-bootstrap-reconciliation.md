# Concurrent bootstrap reconciliation — 2026-08-30

## Why this record exists

Two isolated Codex tasks changed `readme-labs` from the same initial commit
without exchanging state. One task built the domain-first research and
evaluation laboratory on draft PR #1. The other completed a release-oriented
cross-repository extraction through PR #2 while PR #1 was still running.

Both tasks cited originating session
`01a05036-1c5b-7db0-a9f8-508ea45aaa0f`, but the PR #2 work was not delivered to
the active PR #1 task before it published. Isolation protected both worktrees;
coordination did not protect the shared remote authority.

## Remote timeline

| Time (UTC) | Event |
| --- | --- |
| 01:55 | Draft `readme-labs` PR #1 opened from `codex/bootstrap-readme-labs`. |
| 02:04 | PR #2 opened from the separate `codex/readme-domain-extraction` worktree. |
| 02:05 | PR #2 merged to `main` as `158202b`; `v0.1.0` was published. |
| 02:08 | `repository-guidance` PR #7 merged and removed its editable README sources. |
| 02:08 | `repository-guidance@v0.2.0` was published with a release, commit, and tree lock on `readme-labs@v0.1.0`. |
| 02:24 | PR #1 finished its domain contracts, corpus pilot, evaluation capsule, canonical capability, experimental adapter, and CI without having received PR #2 state. |

## Overlap and disposition

| Concurrent artifact | Disposition after reconciliation | Reason |
| --- | --- | --- |
| Purpose, anatomy, pitfall findings | Retained under `research/` | Unique evidence and useful earlier framing |
| Three blind reconstruction exercise sets | Retained as historical research evidence | Valuable comparisons, but score material is visible and not a current held-out evaluation |
| Anatomy v1, sources, watchlist | Retained once at their existing paths | Both tasks imported the same source material |
| `skills/readme-contract-review` | Preserved only in immutable `v0.1.0`; absent from current editable source | Prevents two canonical skills while preserving downstream compatibility |
| Root `.codex-plugin` and `.claude-plugin` manifests | Preserved only in `v0.1.0`; absent from current repository root | Restores plugin-capable, domain-first identity; products belong behind adapters |
| `tools/validate_repository.py` | Superseded by package tests, AST link checks, artifact synchronization, and CI | Avoids two validation systems with different architecture assumptions |
| Original migration record | Retained with a historical-status banner | Preserves the exact released decision context without presenting it as current architecture |
| `v0.1.0` and `repository-guidance@v0.2.0` | Left immutable | Tags and downstream locks are provenance and compatibility boundaries, not branches to rewrite |

## Authority at reconciliation

- Domain model: `domain/`.
- Research and historical evidence: `research/`.
- Canonical editable capability at reconciliation:
  `capabilities/readme-review/`.
- Evaluation contracts and runs: `evals/`.
- Current experimental product adapter: `products/codex-plugin/readme-labs/`.
- Historical downstream interface: `readme-labs@v0.1.0` skill
  `readme-contract-review`, pinned by `repository-guidance@v0.2.0`.

The historical interface and current source interface deliberately have
different names. A future downstream upgrade must treat that as a migration,
not silently substitute a branch path for a released artifact.

## Validation and remaining gate

PR #1 merges current `main`, so its eventual merge no longer discards PR #2
history. At reconciliation time, repository tests verified one generated
capability, while the immutable tag preserved the predecessor. The downstream
repository remained on its working lock.

No new release should be cut merely to make the names agree. The next release
must first add a blinded runner result, a no-material-finding scenario, and an
explicit downstream discovery/upgrade test under the current release policy.
