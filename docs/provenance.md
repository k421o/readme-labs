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

Until the downstream migration is complete, the existing files in
`repository-guidance` remain compatibility sources. New README-domain changes
belong in `readme-labs`; a later downstream change will replace the old editable
copy with a pinned released artifact or separate installation boundary.
