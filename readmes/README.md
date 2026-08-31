# README artifact records

This directory is the document-centered data plane for captured README
artifacts. A working `README.md` remains editable in its authoring workspace.
Only an explicitly selected output crosses the capture boundary and becomes an
immutable artifact package here.

Each package is named from the captured content digest and uses `artifact.md`
rather than `README.md` so agents and people can distinguish stored evidence
from a live repository entrypoint. When README Labs cannot or should not retain
the body, `artifact.ref.json` binds the source locator and exact content digest
without copying the document.

`record.json` is the canonical JSON metadata record. It keeps artifact identity,
capture state, custody, provenance, repository occurrences, collection purposes,
and lineage on separate axes. Analysis and review evidence is attached as
single-subject JSON records under the same package without turning any result
into a quality verdict.

[`records/`](records/) contains the exercised packages. Each `report.md` is a
generated human view. `readme-lab artifact catalog` rebuilds an ignored SQLite
query projection from the canonical JSON; the database is never the source of
truth. The full model and command workflow are in
[`docs/readme-artifact-records.md`](../docs/readme-artifact-records.md).

The versioned contracts are:

- [`artifact-record-v1.schema.json`](artifact-record-v1.schema.json)
- [`evidence-record-v1.schema.json`](evidence-record-v1.schema.json)
