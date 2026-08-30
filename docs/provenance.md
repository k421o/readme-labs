# Import provenance

`readme-labs` was extracted from README research that began in
[`k421o/repository-guidance`](https://github.com/k421o/repository-guidance).

The initial research commits were replayed with their original author, date,
and message onto the `readme-labs` bootstrap branch:

| Source commit | Imported commit | Material |
| --- | --- | --- |
| `e84fccc` | `fd85bca` | Evidence-backed README anatomy |
| `6f91608` | `e8d6ec5` | Expanded source companion |
| `ef4e054` | `2a278ec` | Exploratory repository watchlist |

Commit identifiers changed because the commits have a new parent in the new
repository. Their patches and authorship were preserved through `git am`.

The README review rubric originated in
`skills/documentation-signal-review/references/readme-review.md` in
`repository-guidance`. Its operational rules are being re-derived here against
the expanded anatomy rather than copied into two independently editable skills.

A concurrent extraction task independently imported the broader purpose,
pitfall, and blind reconstruction research through
[`readme-labs` PR #2](https://github.com/k421o/readme-labs/pull/2). It merged as
`158202b`, published immutable tag `v0.1.0`, and used
`skills/readme-contract-review` as its release capability. While this bootstrap
branch was still isolated, [`repository-guidance` PR #7](https://github.com/k421o/repository-guidance/pull/7)
removed its editable README copies and released `v0.2.0` with a commit-and-tree
lock on that tag.

The two tasks did not exchange state before publication. Their artifacts are
reconciled in
[`docs/migrations/2026-08-30-concurrent-bootstrap-reconciliation.md`](migrations/2026-08-30-concurrent-bootstrap-reconciliation.md):
unique research and immutable history are retained, while the domain-first
layout, `capabilities/readme-review`, versioned contracts, evaluation lab, and
generated product adapters are the current editable authority.
