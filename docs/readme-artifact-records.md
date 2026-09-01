# README artifact records and evidence packages

README Labs treats a completed README as data. The artifact record is the
document-centered unit that keeps immutable Markdown bytes or an immutable
source reference together with provenance, repository context, collection use,
lineage, diagnostics, and reviews. At the current repository head, one logical
README has exactly one durable body-owning path.

This model begins only at an explicit external capture or managed custody
transfer. It does not constrain how a README is drafted, generated, or revised
before that boundary.

## Authoring and admission boundary

```text
external authoring workspace ── explicit capture ──┐
managed ingestion checkout  ── verified move   ──┼─▶ rm-<digest-prefix>/
                                                  │    ├── artifact.md
                                                  │    ├── record.json
                                                  │    ├── evidence/*.json
                                                  │    └── report.md
immutable third-party source ─ pinned reference ─┘
```

An authoring agent works on an ordinary `README.md` and should not be asked to
reason about immutable artifacts. Explicit `artifact capture` is for an
external or otherwise non-durable authoring workspace: it computes the completed
bytes' identity and creates their sole body-owning path inside README Labs.
Managed repository admission instead moves the selected file from its isolated
checkout directly into that final path. Intake keeps landing metadata, not a
snapshot of the body.

The artifact bytes are immutable after admission. The surrounding record may
append provenance events, repository occurrences, collection memberships,
lineage, and evidence without changing those bytes. A changed body has a new
content identity. When it supersedes the current owned version of the same
logical README, Git preserves the retired record and bytes; they do not remain
as a parallel live rollback copy at `HEAD`.

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
| Artifact | Exact Markdown content and digest. | One stored body can have several repository occurrences or uses without being copied. |
| Admission | When and why completed bytes crossed into the registry by external capture or managed transfer. | Immutability must not leak into generation, and custody must not create parallel owners. |
| Custody | Ownership, visibility, body-retention policy, and license when known. | A public reference and private generated output need different storage rules. |
| Provenance event | How the artifact originated or entered the domain. | One artifact can have generated and later ingestion provenance. |
| Occurrence | Repository, revision or tree, path, and README role. | Contextual review depends on placement, not only bytes. |
| Membership | The artifact's present lab use. | A generated output can later become a reference without changing its origin. |
| Lineage | Relationships between immutable versions. | Metadata can identify a superseded Git-held version without retaining its body at another live path. |
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

Embedded content is called `artifact.md`, not `README.md`. The original name and
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

That `artifact.md` is the sole durable owner of those README bytes in this
repository. Intake manifests, provenance events, occurrences, evidence, and
reports point to its record ID and digest; none embeds or snapshots the body.

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
popular repository is a quality exemplar. It is appropriate for third-party or
restricted content, not as a substitute for landing an internally owned
completed README.

The only durable copy exception is an explicitly classified generated product
adapter. Its `UPSTREAM.json` must map an exact canonical source tree to an exact
generated destination at a full source revision and digest. That mechanically
identical delivery copy has no independent authoring authority and does not
authorize any additional unclassified copy.

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
corpus-wide run or replacing its execution context. Neither the projection nor
the durable run log may embed the complete subject README. They retain record
IDs, content hashes, measurements, diagnostics, bounded excerpts when needed,
and sanitized command metadata. Raw command output that contains the full body
is execution state and must be discarded rather than checked in.

Evidence has one of two scopes:

- **Artifact scope** observes only the immutable bytes. Static Markdown analysis
  uses this scope.
- **Occurrence scope** observes the artifact in a repository placement. A role
  annotation, repository-contextual soft review, or user-response trial uses
  this scope.

When occurrence-scoped evaluation needs real root placement or relative-link
behavior, the runner copies `artifact.md` to `README.md` inside a disposable
repository. That context copy exists only for execution and is removed after
the run; durable evidence binds back to the final artifact by identity.

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

SQLite is a disposable, rebuildable query projection, not primary storage or a
source of truth. Git-managed Markdown owns embedded README bodies and canonical
JSON owns their metadata. The catalog contains normalized tables for artifacts,
provenance, occurrences, memberships, lineage, evidence, evidence sources, and
diagnostics. It can support corpus queries or a future local visualization
without introducing binary merge state into Git.

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

Capture a completed generated README from an external or otherwise non-durable
authoring workspace after authoring ends:

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

For a completed README already inside a managed ingestion checkout, use
`ingest select` and `ingest admit` instead. That route moves the body directly
into this registry and emits a landed intake manifest; it does not call the
copying capture command or create an intake snapshot. See
[`repository-ingestion.md`](repository-ingestion.md#landing-selected-readme-artifacts).

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

Run a repository-contextual review from the final body without creating a
durable root copy. The base repository must be clean; the runner makes a
no-hardlink clone, commits the body at the requested path, records the context
binding, and removes the clone after execution:

```console
uv run readme-lab agent-eval run \
  experiments/evaluators/<evaluator>/evaluator.json \
  --repository /path/to/clean/base-repository \
  --readme README.md \
  --readme-record readmes/records/<record> \
  --run-dir experiments/runs/<run> \
  --run-id <run> \
  --candidate-id <candidate> \
  --model <model>
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
