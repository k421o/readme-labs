# `v0.2.0-rc.1` release-candidate evidence

This directory preserves the decisive blinded evaluation pair for the first
`readme-review` factory release candidate. The executor ran the generated
plugin installed through the repository's Git marketplace at immutable
revision `0ec30675771ca90c947cca1bf86c912845e1f341`. The runner independently
hashed the product at that Git object, the marketplace checkout, and the
installed cache; all three hashes were
`433cdc93279e108833716c84fafb79102882dec8c9cf5f3ddf9886167c9fe29a`.

## Selected pair

| Scenario | Expected behavior | Result | Response SHA-256 | Score SHA-256 |
| --- | --- | --- | --- | --- |
| `missing-first-path` | Report the missing consumer install/use path | Automatic pass; semantic pass | `2451f42211242ec9cfd5a6ac3aa854bad05f1ebb7be33564fe58deef166adccb` | `7ccadc49e6c1ca20ad0ab5829d335970f64cf97b2e2f1b05371a0d389dfab550` |
| `adequate-first-path` | Return no material findings | Automatic pass; semantic pass | `85d6b11d3453b43aacc0ec83690edb2440209ee53f5445ee5ad0e25fb7025924` | `491c5f1bd140d8c6318e27e6b9da528a312a0d2ad4fdc76fdcf167398bd2c15b` |

Both runs used `gpt-5.6-terra` at high reasoning effort with
`codex-cli 0.151.0-alpha.7.2`. Network access was disabled, the factory
checkout was denied to the executor, and the held-out scorecard was read only
after executor exit. Each `run.json` binds the prompt, materialized Git state,
permission profile, response, score, events, stderr, and installed artifact.

The no-finding run contains one explicitly disclosed residual: Codex emitted a
sandbox-denial warning without a machine-attributed command event. The scorer
correlates it one-to-one with the only unmatched failed command and does not
claim exact attribution. The finding run has no such residual.

## Independent review sequence

Fresh read-only reviewers that did not have the subject plugin installed
assessed the behavior and evidence:

1. Task `01a0538b-7071-74d0-b660-d9b96ab52aa6` passed both scenario semantics
   and held final publication only for missing durable evidence, artifact
   binding, and update/rollback records.
2. Task `01a05395-164e-74a1-aff0-27afc8f4b3b3` passed replacement bundles and
   independently reproduced the Git-object, marketplace, and installed-cache
   product hash. Its dirty-checkout and direct-Git-object gaps were then
   enforced by the runner before this selected pair was produced.

The raw reports are preserved under `independent-review/`. Earlier exploratory
runs are intentionally excluded from this directory: they exposed failure
modes recorded in `evals/failure-dispositions-v0.2.0.md` but are not efficacy
evidence.

## Scope

This pair supports an experimental release, not general README-review
effectiveness. It covers one deterministic fixture, one mutation, one model,
and one run per condition. Registry rendering, broad taxonomy coverage, and
performance across natural repositories remain outside the claim.
