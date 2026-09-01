# First README factory runbook

This runbook reconstructs the source, evidence, packaging, and installation
boundaries for the first `readme-review` release without relying on task chat.

## Authority map

| Question | Authoritative repository surface |
| --- | --- |
| README concepts and observations | `domain/`, interpreted with `research/` evidence |
| Editable agent behavior | the named skill directories under `capabilities/` |
| Blinded scenarios and scoring | `evals/` |
| Codex packaging | generated `products/codex-plugin/readme-labs/` |
| Native installation discovery | `.agents/plugins/marketplace.json` |
| Version promises and limitations | `docs/releases/` and GitHub releases |
| Downstream routing | the consuming repository |

Path location, historical ancestry, and packaging format do not override this
map. Agent Labs and Agent Skills are neither inputs nor authorities. A future
catalog entry may consume an immutable release, but the factory must work
without it.

## Reproduce the source checks

From a clean `readme-labs` checkout:

```console
uv sync --locked --dev
uv run ruff check .
uv run pytest
uv run python scripts/check_markdown_links.py
uv run python scripts/build_plugin.py --check
uv build
```

`scripts/build_plugin.py` copies the explicitly allowlisted canonical
capabilities into the product and writes per-source revisions and hashes to
`UPSTREAM.json`. Every generated skill must be byte-identical to its source
tree. Edit a canonical capability, rebuild, and commit both sides; never edit a
packaged copy directly.

## Install through the repository marketplace

Use a disposable, authenticated Codex home and a full immutable Git revision.
Authenticate it through normal Codex login; do not copy credentials into the
repository or a run record.

```console
export README_LABS_TEST_HOME="$(mktemp -d)"
CODEX_HOME="$README_LABS_TEST_HOME" codex login
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin marketplace add \
  https://github.com/k421o/readme-labs.git \
  --ref <full-40-character-release-commit> \
  --sparse .agents/plugins \
  --sparse products/codex-plugin/readme-labs \
  --json
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin add \
  readme-labs@readme-labs --json
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin list --json
```

This is a repository-owned local/Git marketplace installation. It is the
proper native Codex flow, but it is not a public or verified listing.

## Run the blinded pair

Choose new paths outside the factory checkout for every run. The runner
refuses existing paths and refuses to place the workspace or run record inside
the held-out checkout.

```console
CODEX_HOME="$README_LABS_TEST_HOME" uv run readme-lab capsule run \
  evals/scenarios/missing-first-path/capsule.toml \
  --workspace /tmp/readme-labs-finding-workspace \
  --run-dir /tmp/readme-labs-finding-run \
  --run-id release-finding \
  --artifact-revision <full-40-character-release-commit> \
  --model gpt-5.6-terra \
  --reasoning-effort high

CODEX_HOME="$README_LABS_TEST_HOME" uv run readme-lab capsule run \
  evals/scenarios/adequate-first-path/capsule.toml \
  --workspace /tmp/readme-labs-no-finding-workspace \
  --run-dir /tmp/readme-labs-no-finding-run \
  --run-id release-no-finding \
  --artifact-revision <full-40-character-release-commit> \
  --model gpt-5.6-terra \
  --reasoning-effort high
```

The two `score.json` files must pass automatic gates and then receive an
independent semantic review. Inspect the response evidence and anti-findings;
do not infer efficacy from category matching alone. Preserve executor version,
model, reasoning effort, prompt hash, network policy, materialized Git hashes,
response, score, stderr, and failure dispositions.

This is a release-candidate procedure for a capability claiming the current
interface. It does not gate admission of a differently shaped candidate. Open
experiments follow `docs/experimental-architecture.md`: automated results are
evidence only and an admitted hypothesis completes its declared run unless a
recorded safety, authorization, or infrastructure stop makes it incomplete.

## Update and rollback

Codex Git marketplace configuration pins a ref. To move deliberately between
immutable releases, replace the configured marketplace source and reinstall
the plugin, then verify inventory:

```console
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin marketplace remove readme-labs
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin marketplace add \
  https://github.com/k421o/readme-labs.git \
  --ref <target-full-40-character-commit> \
  --sparse .agents/plugins \
  --sparse products/codex-plugin/readme-labs \
  --json
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin add \
  readme-labs@readme-labs --json
CODEX_HOME="$README_LABS_TEST_HOME" codex plugin list --json
```

Rollback is the same operation with the recorded previous immutable commit.
The release record names the tested predecessor and final inventory. Do not use
a moving branch or reinterpret `v0.1.0` as the same interface: that tag contains
the predecessor `readme-contract-review` product shape.

## Release and consume

The release record in `docs/releases/` names the artifact class, maturity,
source and domain revisions, hashes, evaluation evidence, known limitations,
compatibility, downstream consumers, and rollback. A consumer should install
the GitHub release directly through the repository marketplace and exercise
normal skill discovery; it must not need a source checkout, Agent Labs, Agent
Skills, a wrapper, or an independently edited copy.
