# README static analysis

“Static analysis” is the broad category for inspecting an artifact without
executing it. A linter is one kind of static analyzer. README Labs keeps these
measurements beside soft agent reviews because the two answer different
questions.

```text
generated, ingested, or candidate README
                 │
        ┌────────┴────────┐
        │                 │
 deterministic       soft agent
 static analyzers    evaluators
        │                 │
 localized property  contextual perspective
 diagnostics         and recommendation
        └────────┬────────┘
                 │
       evidence bundle for owner or
       designated-review synthesis
```

Neither branch decides whether a hypothesis is true, whether a candidate is
admitted, or whether a README should be promoted. A later regression contract
may gate a release on one explicitly accepted property, but that authority
belongs to that named contract rather than to static analysis in general.

## Two modes

The same analyzer runs in two modes:

1. `corpus_characterization` evaluates its full rule surface on pinned corpus
   documents. This reveals signal distribution, concentration, blind spots, and
   likely false-positive surfaces before the analyzer is used for feedback.
2. `document_diagnostic` evaluates a generated, ingested, candidate, or local
   README. It can run during iteration as feedback or after generation beside
   a soft review. The output is the same evidence type in either position; its
   timing does not grant it more authority.

The default document profile contains only rules selected for feedback after
calibration. The `all` profile remains available for investigation. Every run
records the exact enabled rules so a result cannot be mistaken for coverage the
analyzer did not perform.

## Adapter and output boundary

README Labs standardizes a run envelope, not every tool's native interface. The
envelope records:

- analyzer ID, version, adapter kind, and spec digest;
- subject identity, source revision, path, and content digest;
- selected profile and enabled rule IDs;
- localized diagnostics, metrics, skipped rules, and incomplete states;
- references and hashes for preserved native output when an external adapter
  has its own contract; and
- `automated_authority: evidence_only` plus
  `hypothesis_disposition: not_decided`.

It deliberately has no quality score, pass/fail result, merge verdict, or
candidate-admission decision. External tools may expose those concepts in their
native output; an adapter preserves that output and explicitly maps only the
fields README Labs knows how to interpret.

## Initial analyzer and calibration

[`markdown-structure-v1`](../experiments/analyzers/markdown-structure-v1/analyzer.json)
is a dependency-free built-in adapter over the repository's CommonMark parser.
It measures heading-level jumps, empty headings, repeated normalized heading
labels, and Markdown images with empty alternative text. It does not require a
section catalog, template, skill layout, or progressive-disclosure design.

The first [corpus characterization](../experiments/runs/pilot-high-exposure-markdown-structure-v1/README.md)
completed on all 16 pinned high-exposure documents. It found 17 signals. Ten
repeated-heading notices were concentrated in Axios's large API reference, so
that rule remains useful for characterization but is not in the default
feedback profile.

The paired [generated-README run](../experiments/runs/reademe-temp-forward-test-markdown-structure-v1/README.md)
emitted no default-profile diagnostics. The soft maintainer review still found
semantic blockers, demonstrating why a zero-diagnostic static result cannot be
read as approval.

## Commands

Run feedback against a generated README:

```console
uv run readme-lab static-analysis run \
  experiments/analyzers/markdown-structure-v1/analyzer.json \
  /path/to/generated/README.md \
  --output /path/to/run.json \
  --run-id generated-readme-static-v1 \
  --subject-id generated-readme \
  --source-kind generated \
  --recorded-path README.md
```

Use `--source-kind ingested` for a README inside a managed ingestion checkout,
or `candidate` for a materialized candidate artifact. The analyzer reads the
file and writes its run elsewhere; it does not edit the subject.

Characterize the full rule surface against a pinned corpus:

```console
uv run readme-lab static-analysis corpus \
  experiments/analyzers/markdown-structure-v1/analyzer.json \
  corpus/manifests/pilot-high-exposure-v1.jsonl \
  --cache /tmp/readme-labs-pilot-cache \
  --output /tmp/markdown-structure-corpus-run.json \
  --run-id pilot-high-exposure-markdown-structure-v1
```

The corpus command verifies each fetched body against its declared Git blob
before analysis. Raw bodies stay in the untracked cache; derived run evidence
contains identities, hashes, metrics, and diagnostics.

Validate a preserved run against the exact analyzer spec and recompute its
summary with:

```console
uv run readme-lab static-analysis verify \
  experiments/analyzers/markdown-structure-v1/analyzer.json \
  experiments/runs/pilot-high-exposure-markdown-structure-v1/run.json
```

## Growing the checker set

Future analyzers can cover Markdown syntax/style, prose terminology, link and
reference integrity, accessibility, or declared project-specific contracts.
Add them one at a time:

1. define the adapter and its native-output boundary;
2. add deterministic positive, negative, and failure fixtures;
3. run the full rule surface on an appropriate pinned corpus;
4. inspect concentration and contextual false positives;
5. choose an explicit default feedback profile; and
6. only then place its diagnostics in routine generation or ingestion flows.

Network services, heavyweight models, and third-party command runtimes remain
adapter-owned dependencies. Their failures produce incomplete evidence rather
than silently changing a README or ending a hypothesis.
