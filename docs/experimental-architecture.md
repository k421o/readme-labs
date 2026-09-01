# Adaptive domain laboratory

README Labs keeps research, intake, experimental evaluation, canonical
capabilities, and generated products in one repository while they share one
lifecycle. Colocation does not make every artifact authoritative. The artifact
class and its recorded state determine what it may influence.

## Artifact classes

| Class | Purpose | Authority |
| --- | --- | --- |
| Intake record | Carry identity, provenance, limitations, and verified custody transitions for outside work. | Evidence only. It is transactional transport, not durable completed-README storage, and admission does not endorse a claim or design. |
| Candidate | Make a skill, plugin, tool, automation, script, bundle, method, or other treatment reproducible and testable. | Experimental only. It may intentionally conflict with current contracts. |
| Experiment plan | State a question, planned trials, measurements, and completion policy. | Governs the run, not the answer. |
| Observation | Preserve agent behavior, user response, diagnostics, metrics, and failures without embedding the complete subject README. | Evidence for later interpretation. |
| README artifact record | Own one completed Markdown body, or pin one non-retained external body, with custody, provenance, occurrences, collection purposes, and lineage. | Artifact identity only. Admission does not establish quality or constrain prior authoring. |
| Document evidence record | Project one observation or evaluation subject beside its README artifact while retaining hashes for the original run, not another body copy. | Evidence only; never a combined score or decision. |
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
    -> explicit selection of completed README bytes
    -> final artifact landing, with no intake body snapshot
    -> trials, analyzers, and advisory evaluators
    -> document-centered evidence records, including failures and surprises
    -> owner or designated-review synthesis
    -> iterate, retain, combine, reject, or promote
    -> redefine canonical artifacts and their declared compatibility
    -> regression and release gates
```

The current canonical capabilities are baselines and comparators. They are not
admission schemas for candidates. A candidate may use a different `SKILL.md`,
multiple skills, a different progressive-disclosure structure, or no current
README Labs interface at all.

Embedded candidates that expose a `codex_skill` entrypoint can use the
candidate review executor against the same held-out repository capsules as the
canonical `readme-review` capability. The executor isolates one candidate
treatment, supports explicit invocation or discovery, and records automatic
scores as evidence without changing candidate or hypothesis authority. Other
candidate forms use experiment-specific execution until they earn a reusable
adapter.

The canonical `readme-generate` capability composes the complete sibling review
workflow during ordinary owner-authorized repository work; it is not a
write-producing candidate executor. Candidate generation remains deferred
until an isolation backend owns the treatment's full process lifetime and can
prove the mutable workspace is quiescent before capture. Prompt constraints,
process-group cleanup, and final-state scans are not sufficient evidence when
a detached descendant can retain an open write handle.

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

Artifact admission is likewise outside the authoring agent's decision loop. The
working `README.md` remains editable until an owner selects a completed output.
A managed ingestion checkout transfers that file directly into its
digest-derived final record; an external or otherwise non-durable authoring
workspace may use explicit capture. At `HEAD`, the result has one durable
body-owning path. Git preserves superseded versions and provides rollback rather
than parallel live copies. See
[`readme-artifact-records.md`](readme-artifact-records.md).

Contextual trials may copy the final body into a disposable repository as root
`README.md`, mutate it, exercise relative links, and then remove the workspace.
Durable evidence and event logs retain identity, measurements, and sanitized
execution metadata, never the complete subject body. The local SQLite catalog
is a rebuildable index over Git-managed Markdown and JSON, not another storage
authority.

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
logs, but it is not another domain authority. A completed README moves from the
yard directly into its final artifact record; only landing metadata and verified
finalization or Git-migration receipts remain in durable intake. See
[`repository-ingestion.md`](repository-ingestion.md).
