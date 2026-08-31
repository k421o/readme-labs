# readme-labs

`readme-labs` is a research and evaluation repository for README structure,
authoring, review, and agent behavior. Its installable skills and plugins are
applications of that work, not the organizing purpose of the repository.

The project is currently moving from a **domain module** into an **evaluation
laboratory**. It is establishing a common model for README roles and content,
then using controlled fixtures, pinned public repositories, mutation tests, and
eventually executable environments to test that model.

## Current work

- Build an evidence-backed anatomy for root, package, component, experiment,
  fixture, and archive READMEs.
- Represent individual documents as versioned `READMEObservation` records.
- Collect reproducible corpus manifests without treating popularity as quality
  or copying an unbounded raw corpus into Git.
- Evaluate README review and authoring behavior on both controlled and natural
  repositories.
- Ingest outside research, methods, skills, bundles, and trial evidence without
  prematurely making them canonical.
- Acquire repositories and local work through an isolated, disposition-aware
  ingestion yard before admitting selected domain artifacts.
- Compare isolated candidate capabilities through complete experimental runs,
  soft agent perspectives, and eventually privacy-bounded user-response work.
- Derive agent capabilities from the domain evidence and test them before
  treating them as products.

The initial findings are in
[`research/readme-anatomy-v1.md`](research/readme-anatomy-v1.md). Its
[source companion](research/readme-anatomy-v1-sources.md) separates standards,
platform behavior, empirical research, public training-corpus evidence, and
repository examples. The
[watchlist](research/readme-anatomy-v1-repository-watchlist.md) records
interesting repositories without prematurely treating them as evidence.

## Repository model

```text
Sources                         Stable domain core                   Consumers
──────────────────────          ──────────────────────────           ─────────────────────
Synthetic fixtures ─┐           README roles and taxonomy      ┌─ Candidate library
Real repositories ──┤─ ingest → READMEObservation records →    ├─ Experimental evaluation
Outside research ───┤           evidence and interpretation     ├─ Canonical capabilities
Skills and methods ─┘                                             └─ Derived products
```

The middle is intended to remain stable while sources and consumers grow
through adapters. See the [domain charter](docs/domain-charter.md) for scope and
evidence rules.

## Complexity progression

Domain maturity and product maturity advance independently. An experimental
plugin can exist while the domain is still an evaluation laboratory; being
installable does not make the repository product-first or establish a stable
user contract.

The maintained progression, entry and exit signals, repository-split triggers,
and dependency rules are in
[`docs/complexity-progression.md`](docs/complexity-progression.md).

## Project layout

```text
domain/         README roles, taxonomy, and observation schemas
research/       Findings, sources, examples, and interpretation
corpus/         Versioned manifests, labels, and sampling plans
intake/         Outside research, methods, artifacts, and provenance
candidates/     Reproducible non-authoritative skills, bundles, and methods
experiments/    Hypotheses, advisory evaluators, runs, and user-response envelopes
evals/          Task capsules, mutations, environments, and scorecards
capabilities/   Agent-facing projections derived from the domain model
products/       Packaging adapters created only when a capability earns them
src/            Deterministic collection and analysis code
tests/          Schema, parser, provenance, and evaluation-contract tests
```

Directories are added when their current contents justify them. The future
shape in the complexity progression is not a request for empty scaffolding.

## Development

Python 3.12+ and [`uv`](https://docs.astral.sh/uv/) are required.

```console
uv sync --dev
uv run ruff check .
uv run pytest
```

Verify an admitted source, candidate, and experiment plan:

```console
uv run readme-lab intake verify intake/manifests/reademe-temp-v1.json
uv run readme-lab candidate verify \
  candidates/reademe-temp-modular-readme-v1/candidate.json
uv run readme-lab experiment validate \
  experiments/plans/reademe-temp-modular-readme-v1.json
```

Initialize a managed ingestion yard outside the repository and inspect its
commands:

```console
uv run readme-lab ingest init --domain-root /path/to/readme-domain
uv run readme-lab ingest --help
```

The [repository-ingestion architecture](docs/repository-ingestion.md) defines
clone isolation, remote severing, preservation policies, owned Git migration,
private publication, archival, physical source cleanup, and finalization.

Inspect one README as a local observation:

```console
uv run readme-lab inspect README.md \
  --repository k421o/readme-labs \
  --revision "$(git rev-parse HEAD)"
```

The emitted record describes structure and provenance. It is not a quality
score.

## First factory status

The initial milestone now includes:

- v1 README roles, semantic taxonomy, and `READMEObservation` schema;
- an AST-based inspector and deterministic contract tests;
- a 16-repository, Git-blob-verified high-exposure pilot with derived
  observations and descriptive analysis;
- deterministic local-Git finding and no-finding scenarios with held-out
  scorecards;
- the canonical `readme-review` capability and a blinded Codex runner;
- a generated experimental Codex plugin adapter; and
- a repository-owned local/Git marketplace for native discovery and
  installation from immutable repository revisions.

The marketplace is the proper mechanical Codex delivery path for this
repository. It is not a public or verified marketplace listing, and it does
not make the product adapter authoritative over the canonical capability.

The immutable `v0.1.0` tag was published by a concurrent extraction before the
current architecture and release policy were reconciled. It is a historical
compatibility artifact pinned by a downstream release, not a current support
promise and not evidence for the present capability. See the
[factory runbook](docs/factory-runbook.md), [release policy](docs/release-policy.md),
[v0.2.0 release record](docs/releases/v0.2.0.md),
[downstream integration boundary](docs/downstream-integration.md), and
[concurrency reconciliation](docs/migrations/2026-08-30-concurrent-bootstrap-reconciliation.md).

## Derived capabilities

The first experimental capability is `capabilities/readme-review`. Research,
the domain model, and evaluation artifacts remain canonical; packaging copies
must be generated from a pinned capability version rather than edited
independently.

Candidate trees under `candidates/` are intentionally different: they are
testable experimental specimens with immutable provenance, not editable forks
or current products. The
[adaptive domain laboratory](docs/experimental-architecture.md) defines intake,
candidate, experiment, observation, promotion, and regression boundaries.

`repository-guidance` is already a downstream integration surface: its `v0.2.0`
release removed the editable README copy and pins the immutable historical
`readme-labs@v0.1.0` artifact. That pin records compatibility, not active
support. A future migration may update the lock to a release of the current
`readme-review` capability after the new gates pass; AGENTS.md guidance and
cross-surface routing remain locally owned downstream.

## License

MIT
