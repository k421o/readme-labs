# Managed repository ingestion

README Labs separates acquiring a source from admitting a durable domain
artifact. A clone, local copy, or job log is operational state. It becomes a
checked-in domain record only after a README artifact, skill, plugin, tool,
automation, script, research method, protocol, data item, candidate, trial
result, or settled Git migration lands.

## Three planes

```text
operational yard                  README Labs                    owned Git history
────────────────────────          ─────────────────────────      ─────────────────────
isolated checkout                 intake manifest               source deletion commit
local inventory                   candidate descriptor          destination addition
selection and action log   ───▶   experiment links       or     push / PR / merge refs
archive or cleanup state          finalization receipt          migration receipt
```

The operational yard does not confer authority on acquired work. Durable
intake records remain evidence, candidates remain experimental, and only an
explicit later decision may change a canonical capability.

## Container topology

The README domain container is deliberately not a Git repository. The
authoritative domain repository and operational yard are siblings:

```text
<readme-domain>/
├── readme-labs/
└── ingestion/
    ├── active/<job-id>/
    │   ├── control/
    │   │   ├── job.json
    │   │   ├── inventory.json
    │   │   ├── selections.json
    │   │   └── actions/
    │   ├── checkout/
    │   └── .readme-labs-ingestion-job
    ├── completed/
    ├── quarantine/
    └── archive/{owned,external}/
```

Initialize the yard with:

```console
uv run readme-lab ingest init --domain-root /path/to/readme-domain
```

The command refuses a domain root inside a Git working tree. Every managed
yard and job has a marker. Finalization will not delete a checkout outside the
matching marked job directory.

## Lifecycle

```text
acquired -> selected -> admitted -> verified -> finalized
    \                                      \
     └──────────────────────────────────────> quarantined
```

An inventory may be refreshed before verification. Selections become
immutable after admission. External and destructive actions cannot be planned
until the job verifies.

## Acquisition and isolation

`ingest begin` accepts:

- a Git or GitHub URL;
- a local Git repository, including staged, unstaged, and untracked state; or
- a non-Git local directory.

Local Git acquisition clones without hardlinks or shared worktree metadata,
then recreates staged and unstaged patches and copies untracked files. Ignored
files are excluded unless `--include-ignored` is explicit. A non-Git source is
copied without following symlinks.

```console
uv run readme-lab ingest begin /path/to/source \
  --domain-root /path/to/readme-domain \
  --job-id example-source \
  --repository-id local:example-source \
  --ownership owned \
  --remote-policy sever
```

Remote policies are structural:

- `sever` records sanitized remote identity and removes every actionable
  remote found in the checkout or initialized nested repository;
- `fetch_only` preserves a sanitized fetch URL and replaces each push URL with
  an inoperative `disabled://` target; and
- `preserve` retains sanitized fetch and push URLs only when explicitly
  selected.

Credentials, queries, and fragments are removed from recorded URLs. Analysis
agents receive the checkout, not GitHub execution credentials or authority.

`--lfs-policy pointers|fetch` and `--submodule-policy record|fetch` make
network and storage behavior explicit. Inventories record Git status,
untracked and ignored paths, submodule declarations, Git LFS availability and
tracked paths, symlinks, file count, byte count, and the post-isolation remote
state.

## Selection and preservation

One source may produce several independently typed selections. A selection
names one exact path, semantic role, content digest, and preservation policy.
Skills, plugins, tooling, automation, and scripts remain distinct selection
and candidate kinds; admission must not collapse them into `whole_solution` or
`other` merely because they came from the same repository.

```console
uv run readme-lab ingest select \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --selection-id readme-skill \
  --path .agents/skills/readme \
  --role skill \
  --preservation selected \
  --candidate-id readme-skill-candidate \
  --candidate-kind skill \
  --candidate-format codex_skill \
  --candidate-entrypoint .
```

| Policy | Durable content | Valid cleanup basis |
| --- | --- | --- |
| `reference` | Source locator, Git identity, and digest | No. It does not prove bytes landed elsewhere. |
| `selected` | Exact selected bytes | Yes, after snapshot verification. |
| `replayable` | Exact selected bytes plus explicitly named context paths | Yes, after snapshot verification. |
| `archive` | Operational checkout and Git bundle outside domain Git | Requires local archive finalization; source cleanup is separate. |
| `git_migration` | Linked owned source and destination Git history; no duplicate snapshot | Yes, after destination identity and equal content verify. |

Replay context is never inferred. Every context path is separately recorded,
snapshotted, and related to its primary selection. Agents may recommend a
larger selection, but they cannot silently shrink the declared preservation
surface.

Symlinks are inventoried but cannot currently be selection roots or occur in
a snapshotted tree. This is a deliberate v1 stop rather than an implicit
dereference that could ingest bytes outside the selected tree.

## Admission and verification

Generated admission creates an intake manifest and optional embedded candidate:

```console
uv run readme-lab ingest admit \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --domain-repository /path/to/readme-domain/readme-labs \
  --manifest-id example-source-v1 \
  --title "Example source intake"
```

When the selected material already landed, link its existing records instead
of copying it again:

```console
uv run readme-lab ingest admit \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --domain-repository /path/to/readme-domain/readme-labs \
  --link-target intake_manifest=intake/manifests/example-v1.json \
  --link-target candidate=candidates/example/candidate.json
```

Linking a record does not by itself authorize source deletion. Physical source
cleanup independently proves that the selected digest exists in a generated
snapshot, an explicit landing proof, or an owned Git migration destination.

Verify before any finalization:

```console
uv run readme-lab ingest verify \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --domain-repository /path/to/readme-domain/readme-labs
```

Verification recomputes selection digests, target file hashes, intake source
and snapshot bindings, candidate contracts, experiment plans, and migration
receipts as applicable.

### Landing selected README artifacts

Selecting or admitting a README does not silently freeze it. When the intended
result is a completed document artifact, a separate explicit capture uses the
verified selection and records `ingestion_selection` as its boundary:

```console
uv run readme-lab artifact capture /path/to/selected/README.md \
  --registry readmes/records \
  --provenance-kind ingested \
  --boundary ingestion_selection \
  --pre-capture-editability not_applicable \
  --ownership owned \
  --visibility local_only \
  --repository <source-id> \
  --revision <verified-revision> \
  --recorded-path README.md
```

A third-party selection may instead use `artifact reference` with its verified
content digest and immutable locator. The artifact record complements rather
than replaces the intake manifest: intake owns acquisition and admission;
`readmes/records/` owns the selected README's document identity and attached
evidence. See
[`readme-artifact-records.md`](readme-artifact-records.md).

### Recorded controller exercise

The checked-in
[`reademe-temp-controller-v1` receipt](../intake/receipts/reademe-temp-controller-v1.json)
records the first complete run of this controller against the local
`reademe-temp` repository. The acquisition cloned its current `main` branch and
Git history, captured its untracked forward-test evidence, excluded ignored
caches, and severed actionable remotes. The job selected current-branch
research and methods plus the workspace trial, then linked and verified the
already-landed intake manifest, modular-skill candidate, experiment plan, and
soft agent-review run.

The source's experimental skill commit was reachable in cloned Git history but
was not the current source branch. The existing intake manifest independently
verified that historical commit and the captured workspace trial. Finalization
then removed only the managed checkout, retained the local control record, and
exported the receipt because durable domain targets already existed. It did not
modify, archive, publish, or delete the original source repository.

## Workspace disposition

Finalize with one independent workspace disposition:

```console
uv run readme-lab ingest finalize \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --domain-repository /path/to/readme-domain/readme-labs \
  --workspace-disposition delete
```

- `delete` removes only the verified managed checkout, retains the control log
  under `completed/`, and does not touch the original source;
- `archive_local` creates a Git bundle when applicable and moves the complete
  job under the owned or external archive; and
- `retain` keeps the finalized job and checkout in place.

An unfinished job may move to `quarantine/`. Quarantine means incomplete or
unsafe to continue, not that its hypothesis was rejected.

Finalization exports `intake/receipts/<job-id>.json` only after at least one
durable target has landed and verified. Use `--no-export-receipt` when the
local job log is sufficient.

## Owned Git migration without duplicate bytes

When both repositories are Git tracked and owned, Git history is the content
record. A migration receipt is valid only when:

1. the source path exists at the declared source revision;
2. the destination path exists at its declared revision;
3. both content digests are equal;
4. the source deletion revision descends from the source revision; and
5. the source path is absent from that deletion revision.

The receipt records `duplicate_snapshot_retained: false`, explicit ownership
bases, local/pushed/PR/merged settlement states, and optional GitHub references.

An already-completed migration can be recorded directly with
`ingest migration-receipt`. During a managed migration,
`execute-source-cleanup` creates the receipt after the deletion commit.

“Clean source” is exact: the executor requires an unchanged expected HEAD, a
clean working tree, tracked and non-overlapping selected paths, equal landing
bytes, physical absence after `git rm`, and a successful commit. It rejects
repository-root cleanup, `git rm --cached`, ignore-only cleanup, dirty source
content, and unmatched paths. If the commit hook fails, it restores the
physically removed paths from the verified clean HEAD.

Remote settlement may stop at a local commit or explicitly push, open a pull
request, or merge it. A push/PR failure leaves a local deletion commit and an
`incomplete` action result so settlement can be recovered; it does not claim
the requested remote outcome completed.

A selected or replayable cleanup plan names the exact landed bytes rather than
treating an intake reference as preservation:

```json
{
  "source_repository": "/path/to/owned-source",
  "expected_head": "0123456789abcdef0123456789abcdef01234567",
  "paths": [
    {
      "path": "skills/example",
      "artifact_type": "tree",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
  ],
  "commit_message": "Remove migrated example skill",
  "settlement": "local_commit",
  "landing_proofs": [
    {
      "selection_id": "example-skill",
      "path": "candidates/example/artifact",
      "artifact_type": "tree",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
  ]
}
```

After `plan-action`, run `execute-source-cleanup` once without `--execute` to
inspect the resolved source, paths, and settlement, then repeat it with
`--execute`. The explicit `--authorized-source` must equal both the plan and
the original local source recorded by the ingestion job.

## Guarded GitHub actions

GitHub mutations use a local JSON action plan and are dry runs unless
`--execute` is supplied. Executors accept only the registered plan inside the
verified job.

Private publication parameters:

```json
{
  "owner": "k421o",
  "repository": "imported-project",
  "history": "snapshot"
}
```

Owned archival parameters:

```json
{
  "owner": "k421o",
  "repository": "old-project"
}
```

Create and inspect the plan before execution:

```console
uv run readme-lab ingest plan-action \
  --yard /path/to/readme-domain/ingestion \
  --job-id example-source \
  --action-id publish-private \
  --action publish_private \
  --parameters /path/to/private-publication.json

uv run readme-lab ingest execute-github \
  --yard /path/to/readme-domain/ingestion \
  --plan /path/to/readme-domain/ingestion/active/example-source/control/actions/publish-private.json
```

Run the same command with `--execute` only after reviewing the dry run. Private
publication refuses an existing target and verifies the resulting repository
is private and administered by the declared owner. Archival verifies current
administrator permission and the final archived state.

## Boundary for future reuse

Acquisition, Git isolation, inventories, and disposition are intentionally
separable from README roles and admission. They remain implemented here while
README Labs is the only demonstrated consumer. A second real consumer such as
Agent Skills is the signal to extract the generic controller into Agent Ops or
a dedicated source-ingestion project; README-specific interpretation remains
owned by README Labs.
