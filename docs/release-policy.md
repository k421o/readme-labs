# Evidence-backed release policy

The repository versions domain contracts, capabilities, and product adapters
separately. A Git commit, valid plugin manifest, or successful local install is
not by itself a released support promise.

## Artifact classes

- **Domain artifacts:** taxonomies, schemas, and evidence interpretations.
- **Capability artifacts:** canonical skills derived from a named domain
  version and evaluated against a published scenario set.
- **Product adapters:** generated installation surfaces, such as the Codex
  plugin, that pin a capability revision and content hash.
- **Data artifacts:** manifests, observations, annotations, and reports with a
  declared sampling and licensing boundary.

Each release states its artifact class and maturity. Product and domain
maturity may differ.

Release gates apply only when promoting an artifact under the named release
contract. They are not candidate-admission rules and do not grant automated
tests authority to reject an experimental hypothesis. A candidate that fails a
current contract may complete its planned trials and propose a new versioned
contract; it simply cannot be released as compatible with the old one.

## Capability release candidate gates

- Skill and interface metadata pass native validation.
- Referenced domain contracts and source revision are pinned.
- Deterministic contract tests pass.
- At least one relevant mutated scenario and one no-material-finding scenario
  are executed by a runner that cannot see their scorecards.
- Results include prompts, executor/model identifiers when available,
  environment fidelity, scores, failures, and residual risks.
- An independent run or reviewer separates capability evidence from the
  author's bootstrap dry run.
- Change notes describe new instructions, likely behavioral effects, and
  rollback.

Automatic checks diagnose declared properties and execution integrity.
Independent semantic review and owner or designated-review synthesis retain
the decision authority. An incomplete evaluator run is recorded as incomplete,
not as evidence that the candidate is useless.

The first factory release records its blinded finding and no-material-finding
runs under `evals/runs/` and its independent assessment in the `v0.2.0` release
record. The earlier author dry run remains explicitly excluded from efficacy
evidence.

## Historical `v0.1.0` release

`v0.1.0` was published from a concurrent extraction task before this policy and
the domain-first bootstrap branch were reconciled. It contains the predecessor
`readme-contract-review` skill, root-level Codex and Claude plugin manifests,
and three reconstruction exercises. `repository-guidance@v0.2.0` pins it by
commit and tree hash.

The tag and release remain immutable provenance and a downstream compatibility
boundary. They do not create a current support promise or retroactively
demonstrate that the current
`readme-review` capability or `0.1.0-dev.1` generated adapter passed the gates
above. Future releases must state which policy revision and scenario evidence
they satisfy; they must not move or rewrite `v0.1.0`.

## Product promotion gates

- Generated content is byte-identical to the pinned canonical capability.
- Provenance records include version, source revision, and tree hash.
- The target product's native validator and discovery checks pass.
- Installation, update, and rollback paths are exercised in a disposable
  environment.
- Marketplace, default-install, authentication, and support policies are
  intentional and documented.
- Downstream compatibility is tested against the released artifact rather than
  a source-tree approximation.

The repository-owned `.agents/plugins/marketplace.json` is the native
mechanical delivery surface for the generated adapter. A Git marketplace
installed from an immutable release or commit is allowed at experimental
maturity. It is not public or verified marketplace publication and does not
transfer source authority away from `capabilities/readme-review`.

## Data release gates

- Sampling frame, collection date, exclusions, and units are explicit.
- Source revisions and derivation code are reproducible.
- Raw redistribution is supported by license and purpose, or raw files remain
  external and only permitted derived data is published.
- Missingness, deduplication, annotation agreement, and important biases are
  reported.
- Prevalence, exposure, quality, and training-data claims remain distinct.

## Release record

A release record should include:

- tag and artifact class;
- maturity and compatibility;
- source/domain/schema versions;
- content hashes and generation command;
- evaluation or analysis evidence;
- known limitations;
- downstream consumers; and
- upgrade and rollback instructions.
