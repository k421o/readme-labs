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

When a run concerns a captured README, a single-subject projection may also
live beside that artifact under `readmes/records/<record>/evidence/`. This is a
document-centered index over the original run, not a replacement execution
record. Source paths and hashes keep both representations verifiable.

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

## Candidate review execution

`readme-lab candidate review-trial` is the reusable execution path for an
embedded Codex review-skill candidate. The same held-out capsules can exercise
different candidates through explicit invocation or normal discovery without
installing them as canonical products. Run records preserve candidate,
entrypoint, subject, prompt, executor, and score evidence. A score diagnoses
the declared capsule only; it neither decides the hypothesis nor prevents its
remaining planned trials.

Review trials are read-only with respect to the subject repository. A
write-producing candidate trial remains deferred to
[issue #14](https://github.com/k421o/readme-labs/issues/14) until a VM,
container, cgroup, or equivalent isolation backend owns the treatment's full
process lifetime and proves the workspace quiescent before any privileged
capture. Process-group cleanup and final-state scanning alone do not establish
that boundary.
