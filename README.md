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
Synthetic fixtures ─┐           README roles and taxonomy      ┌─ Review capability
Real repositories ──┤─ ingest → READMEObservation records →    ├─ Evaluation harness
Package registries ─┤           evidence and scoring rules      ├─ Corpus analysis
Repository history ─┘                                             └─ Derived products
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

Inspect one README as a local observation:

```console
uv run readme-lab inspect README.md \
  --repository k421o/readme-labs \
  --revision "$(git rev-parse HEAD)"
```

The emitted record describes structure and provenance. It is not a quality
score.

## Derived capabilities

The first experimental capability is `capabilities/readme-review`. Research,
the domain model, and evaluation artifacts remain canonical; packaging copies
must be generated from a pinned capability version rather than edited
independently.

`repository-guidance` remains a downstream integration surface. After a README
capability has an evidence-backed release, that plugin may consume the released
artifact while continuing to own AGENTS.md guidance and cross-surface routing.

## License

MIT
Research, evidence, evaluation, and derived capabilities for README structure, authoring, and review.
