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
