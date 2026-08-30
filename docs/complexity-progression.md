# Complexity progression

`readme-labs` should gain structure only when the work produces evidence that
the structure is needed. This document describes that progression so the
repository can grow without prematurely turning a research domain into a
plugin, platform, or collection of loosely related projects.

## Current position

The repository begins as a **domain module with an evaluation lab**:

- a canonical model of README roles and information categories;
- evidence and provenance for that model;
- a manifest-driven corpus that can support reproducible analysis;
- executable observations and evaluation scenarios; and
- one installable capability derived from the domain work.

It is intentionally not yet a marketplace product, a general evaluation
framework, or a monorepo of README tools.

## Two independent axes

Domain maturity and product maturity are related, but neither implies the
other.

| Domain maturity | Meaning |
| --- | --- |
| Exploratory | Findings are hypotheses backed by examples. |
| Described | Terms, roles, and observations have explicit definitions. |
| Measured | A reproducible corpus and analysis support or challenge claims. |
| Evaluated | Capabilities are tested against scenarios and known failure modes. |
| Stable | Versioned domain artifacts have demonstrated compatibility and use. |

| Product maturity | Meaning |
| --- | --- |
| Internal | A capability can be exercised from the source repository. |
| Experimental | An installable package exists, with evidence and limitations. |
| Preview | The interface is intentionally offered to outside consumers. |
| Stable | Compatibility, release, support, and upgrade promises are explicit. |

For example, a valid experimental plugin can exist while the domain model is
still exploratory. That is useful for testing, but it does not make the
plugin—or the research—stable.

## Domain-side stages

### 1. Embedded heuristic

README guidance starts as a small reference inside a broader repository
guidance capability.

Move on when the topic develops independent questions, evidence, or testing
needs that are awkward to express in the parent capability.

### 2. Domain module

The work receives its own repository, charter, vocabulary, research record,
and explicit consumer boundary. Findings can still be mostly qualitative.

Move on when claims need to be compared systematically or when a capability
needs repeatable regression tests.

### 3. Evaluation lab

Add task capsules, fixtures, mutations, outcome measures, and increasingly
realistic execution environments. Keep the first contracts local and narrow.

Move on when scenario results reveal questions that cannot be answered from a
small curated set of repositories.

### 4. Corpus and measurement system

Add a sampling plan, pinned manifests, extraction code, structural observation
records, and reproducible analyses. Raw third-party content remains external
unless its license and purpose clearly permit redistribution.

Move on when longitudinal or cross-ecosystem measurements are reliable enough
to influence released guidance.

### 5. Executable replay

Replace approximations with cloned repositories, pinned toolchains, container
or virtual-machine isolation, and replayable tasks where the extra fidelity
changes the result. Do not require the most expensive environment for every
test.

Move on when more than one domain genuinely needs the same environment or
scoring contracts.

### 6. Shared platform

Extract reusable evaluation infrastructure only after repeated use has made a
stable contract visible. A future `guidance-eval` project should be the result
of demonstrated reuse, not an initial abstraction target.

## Source-side growth

The source tree should progress in the same evidence-led order:

```text
research notes
    ↓
domain definitions and schemas
    ↓
corpus manifests and structural observations
    ↓
evaluation scenarios and results
    ↓
canonical capability source
    ↓
generated or pinned product adapters
    ↓
downstream bundles
```

Each arrow is a dependency direction. Research may motivate domain changes;
products must not silently redefine the domain model, and downstream bundles
must not become editable forks of the capability.

## Consumer progression

Consumers should receive increasingly deliberate artifacts:

1. During exploration, they may link to a document or invoke source directly.
2. During experimentation, they may install a clearly labeled generated
   package pinned to a commit.
3. During preview, they consume a versioned release with change notes and
   compatibility checks.
4. At stability, they receive a supported interface and migration policy.

`repository-guidance` is a downstream curated bundle. It should eventually
consume a released README capability and record the upstream version and hash;
it should not maintain a second editable copy.

## Environment fidelity ladder

Testing should use the least expensive environment that can expose the
behavior under study:

| Level | Environment | Best for |
| --- | --- | --- |
| Static | Markdown fixture and expected observation | Parser and taxonomy tests |
| Snapshot | Pinned repository files with metadata | Structural review scenarios |
| Mutated snapshot | One controlled defect applied to a snapshot | Sensitivity and regression tests |
| Local repository | Temporary Git repository with realistic files | Discovery, path, and Git-context behavior |
| Container replay | Pinned image, tools, and repository revision | Build/install/documentation task behavior |
| Remote replay | Disposable hosted environment with policy controls | Network, platform, and integration behavior |

A result must state its fidelity level. A higher level is justified when a
lower level hides an important failure mode, not merely because it feels more
realistic.

## Gates for adding a product

Add or promote a product adapter only when all applicable statements are true:

- the target user and job are named;
- the canonical source remains outside the adapter;
- generation or synchronization is reproducible and checked;
- the adapter passes its native validation;
- relevant scenarios pass at a declared environment fidelity;
- maturity and limitations are visible to installers; and
- the release boundary and downstream update path are documented.

A repository-owned local/Git marketplace and native installation are
mechanical delivery choices, not evidence of domain correctness. They may be
required to verify a product adapter without claiming public, verified, or
stable marketplace status.

## Gates for extracting another repository

Create another repository only when at least one of these conditions persists:

- it has a distinct lifecycle, ownership boundary, or release cadence;
- multiple independent consumers need the same stable interface;
- its data size, licensing, or security model requires separate operations;
- its runtime or infrastructure materially conflicts with this repository; or
- keeping it here repeatedly obscures rather than clarifies the README domain.

Until then, prefer a well-named directory with a narrow contract. In
particular, corpus analysis belongs here while it directly tests README claims;
large redistributable datasets or a genuinely general evaluation engine may
later move behind versioned interfaces.

## Change procedure

When complexity increases:

1. Record the observed pressure or failure mode.
2. Identify the smallest new boundary that addresses it.
3. State which maturity axis changes and which does not.
4. Add a test, schema, or reproducible example for the new contract.
5. Update dependency and provenance records.
6. Revisit the decision after real use.

This procedure makes repository shape an auditable outcome of the work rather
than an irreversible upfront prediction.
