# README artifact records and evidence packages

README Labs treats a completed README snapshot as data. The artifact record is
the document-centered unit that keeps immutable Markdown bytes or an immutable
source reference together with provenance, repository context, collection use,
lineage, diagnostics, and reviews.

This model begins only at explicit capture. It does not constrain how a README
is drafted, generated, or revised.

## Authoring and capture boundary

```text
authoring workspace                    README artifact registry
────────────────────────────────       ───────────────────────────────────
README.md                              rm-<digest-prefix>/
freely editable                         ├── artifact.md or artifact.ref.json
agents may iterate                      ├── record.json
no artifact identity yet   capture →    ├── evidence/*.json
                                        └── report.md
```

An authoring agent works on the repository's ordinary `README.md` and should
not be asked to reason about immutable artifacts. A separate capture operation
selects the completed bytes, computes their identity, and copies them into the
registry. Editing the working README afterward is normal; capturing the changed
bytes produces another artifact that can declare lineage such as `supersedes`.

The artifact bytes are immutable after capture. The surrounding record may
append provenance events, repository occurrences, collection memberships,
lineage, and evidence without changing those bytes.

## Data model

```text
                             README artifact
                         SHA-256 identity of bytes
                                    │
             ┌──────────────────────┼───────────────────────┐
             │                      │                       │
       provenance events      repository occurrences   memberships
       generated/retrieved    repo + revision/tree      reference corpus
       ingested/authored      path + document role      candidate output
       synthetic              evaluation context        personal corpus
             │                      │                       │
             └──────────────────────┼───────────────────────┘
                                    │
                              evidence records
                       artifact-scoped or occurrence-scoped
                                    │
                         report.md and SQLite catalog
                          generated, non-authoritative
```

The axes stay separate deliberately:

| Concept | What it records | Why it is separate |
| --- | --- | --- |
| Artifact | Exact Markdown content and digest. | The same bytes can appear in several repositories or uses. |
| Capture | When and why bytes crossed from mutable work into the registry. | Immutability must not leak into generation. |
| Custody | Ownership, visibility, body-retention policy, and license when known. | A public reference and private generated output need different storage rules. |
| Provenance event | How the artifact originated or entered the domain. | One artifact can have generated and later ingestion provenance. |
| Occurrence | Repository, revision or tree, path, and README role. | Contextual review depends on placement, not only bytes. |
| Membership | The artifact's present lab use. | A generated output can later become a reference without changing its origin. |
| Lineage | Relationships between immutable versions. | Revision produces a new artifact instead of overwriting prior evidence. |
| Evidence | One structural, diagnostic, agent, or human observation. | Measurements retain producer, scope, limitations, and source-run identity. |

`generated` and `retrieved` are therefore provenance events, not mutually
exclusive permanent document types. `generated_output`, `reference_sample`, and
`personal_corpus` are collection purposes, not origins.

## Identity and naming

The complete content SHA-256 is the artifact authority. A readable package ID
uses the first 16 hexadecimal characters and is verified against the full
digest:

```text
artifact id: sha256:f96b8e9d6c94dee97c7c65c011d29d...
record id:   rm-f96b8e9d6c94dee9
stored body: readmes/records/rm-f96b8e9d6c94dee9/artifact.md
```

Captured content is called `artifact.md`, not `README.md`. The original name and
path remain metadata. This prevents a stored specimen from looking like an
active repository entrypoint and avoids collisions when records are displayed
together.

Record, occurrence, provenance, and evidence IDs are deterministic. Verification
rejects a package when its directory, identifiers, bytes, source hashes, or
context bindings disagree.

## Body storage and custody

An owned or permitted completed output can use embedded storage:

```text
rm-f96b8e9d6c94dee9/
├── artifact.md
├── record.json
├── evidence/
└── report.md
```

A third-party, restricted, large, or otherwise non-retained body uses a pinned
reference:

```text
rm-1f2de14735b1ee9d/
├── artifact.ref.json
├── record.json
├── evidence/
└── report.md
```

`artifact.ref.json` records the locator, repository, revision, path, and content
digest. The raw corpus cache remains untracked and separately verifies its Git
blob. Reference-only storage does not weaken identity and does not imply that a
popular repository is a quality exemplar.

README Labs metadata is never inserted into the subject README. Doing so would
change the bytes being measured, break source fidelity, and create recursive
hash changes. JSON sidecars are canonical. YAML front matter appears only in the
generated `report.md`, which is explicitly not the subject.

## Evidence scope and containment

An evidence record is a single-subject projection of an existing observation or
run. It is stored under the artifact package and binds back to every original
source file by repository-relative path and SHA-256.

```text
multi-document or contextual execution record
                      │
                      ├── exact run remains in experiments/runs/
                      │
                      └── selected subject projection
                              │
                    readmes/records/<record>/evidence/<id>.json
```

This gives each README a complete document-centered view without duplicating a
corpus-wide run or replacing its execution context.

Evidence has one of two scopes:

- **Artifact scope** observes only the immutable bytes. Static Markdown analysis
  uses this scope.
- **Occurrence scope** observes the artifact in a repository placement. A role
  annotation, repository-contextual soft review, or user-response trial uses
  this scope.

The current adapters attach:

- a generated or imported `READMEObservation`;
- one subject from a verified static-analysis run; and
- one completed or incomplete soft-agent review bound to its exact Git
  revision/tree occurrence.

Every evidence record preserves `authority: evidence_only` and
`decision_disposition: not_decided`. A static run with zero diagnostics and a
soft review recommending changes can coexist without contradiction because they
answer different questions. Neither result determines promotion or experiment
disposition.

## Human and query projections

`report.md` is generated from `record.json` and `evidence/*.json`. It presents
artifact identity, provenance, occurrences, memberships, structural metrics,
static diagnostics, and contextual review details together. It deliberately has
no combined score.

SQLite is a rebuildable query projection, not a source of truth. The catalog
contains normalized tables for artifacts, provenance, occurrences, memberships,
lineage, evidence, evidence sources, and diagnostics. It can support corpus
queries or a future local visualization without introducing binary merge state
into Git.

```text
canonical JSON packages
        │
        ├── generate report.md
        └── rebuild catalog.sqlite ──→ query, chart, local dashboard
```

`readmes/catalog.sqlite*` is ignored. A remote database such as Supabase is not
part of this increment; it would be justified only by a demonstrated shared
service, synchronization, or remote-query boundary. Personal-corpus membership
is already representable, while visibility and custody remain available to keep
private or local-only records out of inappropriate publication paths.

## Commands

Capture a completed generated README after authoring ends:

```console
uv run readme-lab artifact capture /path/to/README.md \
  --registry readmes/records \
  --provenance-kind generated \
  --boundary completed_generation \
  --pre-capture-editability mutable \
  --ownership owned \
  --visibility local_only \
  --producer-kind skill \
  --producer-id example-readme-skill \
  --membership example-run=generated_output
```

Register a public reference without retaining its body:

```console
uv run readme-lab artifact reference \
  --registry readmes/records \
  --content-sha256 <sha256> \
  --locator <immutable-raw-url> \
  --repository owner/project \
  --revision <revision> \
  --recorded-path README.md \
  --role repository_root \
  --membership public-reference-v1=reference_sample
```

Attach existing evidence and build the projections:

```console
uv run readme-lab artifact attach-static readmes/records/<record> <run.json> \
  --analyzer experiments/analyzers/<analyzer>/analyzer.json \
  --subject-id <subject>

uv run readme-lab artifact attach-review readmes/records/<record> <run-dir> \
  --evaluator experiments/evaluators/<evaluator>/evaluator.json \
  --occurrence-id <occurrence>

uv run readme-lab artifact report readmes/records/<record>
uv run readme-lab artifact verify readmes/records/<record>
uv run readme-lab artifact catalog readmes/records \
  --output readmes/catalog.sqlite
```

Additional commands append occurrences, provenance, memberships, and lineage.
They may update `record.json`; they never edit `artifact.md`.

## Exercised records and future UAT

The [record index](../readmes/records/README.md) contains two complete acceptance
cases:

1. an embedded generated README with structural, static, and contextual soft
   review evidence; and
2. a reference-only public README with corpus observation and static evidence.

The owner-led [UAT walkthrough issue](https://github.com/k421o/readme-labs/issues/12)
will exercise these workflows through real runs. UAT observations may motivate
later changes, but the facilitating agent does not gain authority to redesign
the architecture during the walkthrough.
