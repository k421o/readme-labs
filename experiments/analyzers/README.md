# Static analysis adapters

Static analyzers inspect README artifacts without executing their subject.
Their diagnostics are measurements to investigate, not quality verdicts,
candidate-admission gates, or instructions to optimize a document for a score.

README Labs standardizes the run envelope: analyzer identity, subject hashes,
coverage, localized diagnostics, raw-artifact references, and authority. It
does not claim that every underlying linter or checker has the same native
command, runtime, output schema, or interpretation. An external adapter must
preserve its native output and name its native contract; the adapter owns any
explicit mapping into the common diagnostic envelope.

Two modes use the same analyzer:

- `corpus_characterization` runs against pinned corpus documents to observe
  rule behavior, prevalence, and likely false-positive surfaces before relying
  on it in a workflow.
- `document_diagnostic` runs against a generated, ingested, candidate, or local
  README and returns feedback beside other experimental evidence such as a
  soft agent review.

Neither mode contains a pass/fail field. A later regression contract may gate
a release on a specifically accepted property, but that is a separate decision
and cannot retroactively turn analyzer output into hypothesis authority.
