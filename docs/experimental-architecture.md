# Adaptive domain laboratory

README Labs keeps research, intake, experimental evaluation, canonical
capabilities, and generated products in one repository while they share one
lifecycle. Colocation does not make every artifact authoritative. The artifact
class and its recorded state determine what it may influence.

## Artifact classes

| Class | Purpose | Authority |
| --- | --- | --- |
| Intake record | Preserve the identity, provenance, and limitations of outside work. | Evidence only. Admission does not endorse a claim or design. |
| Candidate | Make a skill, plugin, tool, automation, script, bundle, method, or other treatment reproducible and testable. | Experimental only. It may intentionally conflict with current contracts. |
| Experiment plan | State a question, planned trials, measurements, and completion policy. | Governs the run, not the answer. |
| Observation | Preserve agent behavior, user response, diagnostics, metrics, and failures. | Evidence for later interpretation. |
| README artifact record | Identify captured Markdown bytes, custody, provenance, occurrences, collection purposes, and lineage. | Artifact identity only. Capture does not establish quality or constrain pre-capture authoring. |
| Document evidence record | Project one observation or evaluation subject beside its README artifact while retaining hashes for the original run. | Evidence only; never a combined score or decision. |
| Canonical domain artifact | Record an owner-selected model, method, or capability. | Editable README-domain authority. |
| Regression contract | Protect an explicitly accepted property or compatibility promise. | May gate only the scope and release that claim the contract. |
| Product adapter | Deliver pinned canonical capabilities through a host-native surface. | Mechanical distribution, never independent behavioral authority. |

## Experimental flow

```text
outside work or current design
    -> provenance-bearing intake
    -> one or more isolated candidates
    -> complete experiment plan
    -> freely editable generated README work
    -> explicit capture of selected completed artifacts
    -> trials, analyzers, and advisory evaluators
    -> document-centered evidence records, including failures and surprises
    -> owner or designated-review synthesis
    -> iterate, retain, combine, reject, or promote
    -> redefine canonical artifacts and their declared compatibility
    -> regression and release gates
```

The current canonical capability set supplies baselines and comparators. It is
not an admission schema for candidates. A candidate may use a different `SKILL.md`,
multiple skills, a different progressive-disclosure structure, or no current
README Labs interface at all.

Embedded candidates that expose a `codex_skill` entrypoint can use the
candidate review executor against the same held-out repository capsules as the
canonical capability. The executor isolates one candidate treatment, supports
explicit invocation or discovery, and records automatic scores as evidence
without changing candidate or hypothesis authority. Other candidate forms use
experiment-specific execution until they earn a reusable adapter.

## Completion and automated evidence

An admitted hypothesis reaches the end of its declared run unless a recorded
safety or infrastructure stop makes execution impossible. A stop produces an
`incomplete` or `unsafe_to_execute` result; it does not falsify the hypothesis.

Automated checks may:

- measure a declared property;
- diagnose compatibility with a named released interface;
- validate provenance or execution integrity;
- report that an evaluator cannot score the candidate; or
- block promotion to a release that claims a contract the candidate violates.

They must not reject candidate admission, silently terminate the remaining
planned trials, or turn incompatibility with the present design into a semantic
judgment about usefulness.

Static analyzers follow the same boundary. Their complete rule surface should
first be characterized against an appropriate corpus; routine document
feedback then names an explicit calibrated rule profile. Zero diagnostics means
only that the enabled rules emitted no diagnostics. It is not a quality score,
merge recommendation, or substitute for contextual evaluation. See
[`static-analysis.md`](static-analysis.md).

Artifact capture is likewise outside the authoring agent's decision loop. The
working `README.md` remains editable until a selected completed output crosses
the explicit capture boundary. The captured bytes then receive a digest-derived
identity; later revision creates another artifact and optional lineage rather
than mutating prior evidence. See
[`readme-artifact-records.md`](readme-artifact-records.md).

## Soft evaluators

A soft evaluator is a versioned agent perspective that produces advisory
evidence. Its recommendation is never an automatic promotion or rejection
decision. Evaluators may be added for open-source maintainers, framework
maintainers, first-time users, documentation specialists, or other useful
perspectives without changing the candidate format.

The initial evaluator asks one agent whether it would accept the resulting
README in a pull request to a mature, popular open-source Linux repository. It
is intentionally a simple starting perspective, not a claim that those
projects share one policy.

## Human response

Human and user-response methods remain open-ended. README Labs records a small
provenance and privacy envelope around a method-defined payload rather than
fixing one survey, interview, telemetry, or usability schema. Raw identifiable
or sensitive data remains outside Git; checked-in records use pseudonymous or
aggregate evidence.

## Repository boundaries

Different responsibilities are directories and contracts inside this domain
repository. Extract another repository only when a persistent independent
authority, release lifecycle, consumer base, runtime, permission, licensing,
or storage boundary exists. Temporary repositories and worktrees are execution
or concurrency substrates, not automatically durable authorities.

Source acquisition uses a non-Git operational yard beside this repository.
The yard may contain disposable clones, local archives, and uncommitted job
logs, but it is not another domain authority. Only landed artifacts and
verified finalization or Git-migration receipts enter durable intake. See
[`repository-ingestion.md`](repository-ingestion.md).
