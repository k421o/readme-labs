# Experiments

Experiments ask questions about README artifacts, methods, skills, bundles,
agent behavior, and user response. The hypothesis is the unit of inquiry; a
candidate skill or bundle is a treatment; a trial is one execution; and an
observation is evidence.

## Two testing roles

- **Experimental evaluation** gathers diagnostics, metrics, traces, soft agent
  reviews, human response, and unexpected outcomes. Failures remain evidence
  and do not automatically reject a candidate.
- **Regression and release evaluation** protects an accepted property or
  compatibility promise. It may block only promotion or release under that
  declared contract.

Plans under `plans/` declare completion behavior and identify every planned
trial before interpretation. Evaluators under `evaluators/` contribute
versioned advisory perspectives. Selected run evidence may be checked in under
`runs/`; raw, sensitive, or unusually large artifacts remain in external
storage behind immutable hashes.

User-response protocols live under `user-response/`. Their method payload is
intentionally extensible so the domain can learn better ways to study readers.

## Static analysis

Static analyzers under [`analyzers/`](analyzers/) produce deterministic or
tool-backed diagnostics beside soft reviews. They first run in corpus
characterization mode, then may expose a calibrated document-feedback profile
for generated, ingested, candidate, or local READMEs. The common run envelope
preserves subject identity and authority while adapter-specific native output
keeps its own contract. See the
[static-analysis architecture](../docs/static-analysis.md).
