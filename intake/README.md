# Evidence intake

Intake is a transactional transport and provenance boundary. It records outside
work without making that work canonical, but it is not a durable staging area
for completed README bodies. An intake may reference or snapshot repositories,
articles, research results, research methods, evaluation machinery, skills,
plugins, tooling, automation, scripts, bundles, agent responses, or
user-response evidence. A completed README follows the move-first landing
described below.

Each manifest separates:

- the source repository or publication identity;
- the exact revision, path, object identity, and content digest when available;
- the role an item may play in the domain;
- whether its bytes are referenced, preserved as a checked-in non-README
  snapshot, or landed in a final README artifact record; and
- limitations such as local-only provenance, licensing, missing source bodies,
  or uncommitted workspace state.

Admission means “available for inquiry.” It does not mean correct, preferred,
compatible, or authoritative.

Checked-in snapshots live under `snapshots/` for selected non-README material
and explicit replay context. Large, restricted, or third-party bodies should
remain in external storage with immutable references and permitted derived
observations in Git.

When a selected file is a completed README, admission transfers the managed
checkout copy directly to `readmes/records/<record>/artifact.md`. A version 2
manifest records the source digest, final body path, transfer time, and verified
absence of the prior managed path. It does not retain an intake snapshot of the
README. Generated work remains editable before selection; ordinary explicit
capture from an external authoring workspace remains available, but neither
route may create two durable body-owning paths in this repository.

Git is the history and rollback mechanism for landed bodies. Provenance and
occurrence metadata may name earlier paths and revisions without requiring
those paths to remain live. Experiments may materialize a disposable root
`README.md` from the final body, then remove it. Evidence and durable execution
logs store identity, measurements, and sanitized metadata rather than complete
README content.

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
- [`source-manifest-v1.schema.json`](source-manifest-v1.schema.json), retained
  for historical snapshot manifests
- [`source-manifest-v2.schema.json`](source-manifest-v2.schema.json), which adds
  move-first README landings
- [`external-action-plan-v1.schema.json`](external-action-plan-v1.schema.json)
- [`finalization-receipt-v1.schema.json`](finalization-receipt-v1.schema.json)
- [`git-migration-receipt-v1.schema.json`](git-migration-receipt-v1.schema.json)
