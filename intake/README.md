# Evidence intake

Intake records outside README work without making it canonical. An intake may
reference or snapshot README files, repositories, articles, research results,
research methods, evaluation machinery, skills, plugins, tooling, automation,
scripts, bundles, agent responses, or user-response evidence.

Each manifest separates:

- the source repository or publication identity;
- the exact revision, path, object identity, and content digest when available;
- the role an item may play in the domain;
- whether its bytes are referenced or preserved as a checked-in snapshot; and
- limitations such as local-only provenance, licensing, missing source bodies,
  or uncommitted workspace state.

Admission means “available for inquiry.” It does not mean correct, preferred,
compatible, or authoritative.

Checked-in snapshots live under `snapshots/`. Large, restricted, or
third-party bodies should remain in external storage with immutable references
and permitted derived observations in Git.

When selected material is itself a completed README, intake provenance can feed
a document artifact package under `readmes/records/`. Intake continues to record
source admission; the artifact package records exact README identity,
occurrences, collection purposes, and attached analysis. Generated work remains
editable until a separate explicit capture chooses the completed bytes.

The [managed repository ingestion controller](../docs/repository-ingestion.md)
acquires and isolates Git URLs, local Git workspaces, and non-Git directories
before producing these records. Its operational job logs live in a non-Git
domain-container yard rather than this repository. A receipt under `receipts/`
is durable only after selected material lands and verifies. Owned Git-to-Git
migrations may instead use a receipt under `migrations/` that links equal
source and destination content plus the physical source-deletion commit; they
do not retain a redundant artifact snapshot.

The first real controller replay is recorded in
[`receipts/reademe-temp-controller-v1.json`](receipts/reademe-temp-controller-v1.json).
It links the already-landed `reademe-temp` intake, candidate, experiment plan,
and agent-review run, then proves that only the isolated managed checkout was
deleted.

The versioned controller contracts are:

- [`ingestion-job-v1.schema.json`](ingestion-job-v1.schema.json)
- [`ingestion-inventory-v1.schema.json`](ingestion-inventory-v1.schema.json)
- [`ingestion-selection-v1.schema.json`](ingestion-selection-v1.schema.json)
- [`external-action-plan-v1.schema.json`](external-action-plan-v1.schema.json)
- [`finalization-receipt-v1.schema.json`](finalization-receipt-v1.schema.json)
- [`git-migration-receipt-v1.schema.json`](git-migration-receipt-v1.schema.json)
