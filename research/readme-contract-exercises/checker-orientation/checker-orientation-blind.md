# Measurement checkers

This directory contains text-in/evidence-out adapters used by Humanizer's
prose-review workflows. They produce signals to investigate, not proof of
authorship, quality, or intent. Preserve the source text and its requirements;
use results to decide what to reread in context, not what to optimize for.

## Choose a checker

| Checker | Best for | Runtime | Entry point |
| --- | --- | --- | --- |
| [`signal/`](signal/) | Offline phrase localization and optional relative reference-model metrics | Python 3; `uv`, Torch, and Transformers only for model-backed mode | `checkers/signal/signal` |
| [`binoculars/`](binoculars/) | A local Binoculars instrument reading using a pinned sibling checkout | Separate Binoculars checkout, virtual environment, and large model downloads | `checkers/binoculars/binocs` |
| [`grammarly/`](grammarly/) | A recorded estimate from Grammarly's free AI detector | Node, Playwright, Chrome, and network access | `python3 checkers/grammarly/run.py` |

Each subdirectory is the authoritative operating guide for its checker. It
documents setup, input limits, output fields, calibration context, and known
limitations.

## Quick start

Run the dependency-free localizer first when all that is needed is concrete
places to inspect. It works offline and does not download a model:

```sh
checkers/signal/signal draft.md --localize --json
```

For the optional GPT-2 reference-model report, create the checker environment
once. The first model-backed run downloads the model into the Hugging Face
cache:

```sh
cd checkers/signal
uv venv --python 3.12
uv pip install torch transformers
cd ../..
checkers/signal/signal draft.md --json
```

To run the repository's deterministic tests, from the repository root:

```sh
npm test
```

Live Grammarly checks and Binoculars scoring are optional; follow their
dedicated guides before running them.

## Operating principles

- Treat all output as noisy evidence. A low, high, or changing score does not
  establish who wrote a passage, whether it is acceptable, or whether it has
  been improved.
- Prefer localized evidence over document-level scores. Read the reported span
  with its claims, citations, audience, and surrounding structure before
  editing.
- Do not add randomness, filler, or distortion to move a metric. Make changes
  only when they serve the writer's stated purpose.
- Keep inputs and receipts appropriately scoped. The Binoculars runtime and
  model cache are regenerable local state; Grammarly receipts are local run
  artifacts and should not be treated as source material.
- Separate repeatable offline checks from live services. Grammarly uses an
  undocumented anonymous endpoint with a browser fallback, has minimum input
  and rate limits, and can vary across sessions.

## Reading results responsibly

`signal` is primarily a navigation tool: its deterministic surface-tell spans
and optional GPT-2 predictability measures help prioritize a review. Its values
are relative reference-model measures, so compare revisions cautiously and do
not apply a pass/fail threshold.

Binoculars returns a score and verdict under an upstream model-pair threshold.
That threshold is only calibrated for its default Falcon model pair and
precision. In particular, use `--fp32` when you need a meaningful numerical
comparison; changing models or precision invalidates the default calibration.

The Grammarly wrapper saves a structured receipt with the input hash, checker
version, timing, raw per-chunk response, aggregate score, and character
coverage. For multi-chunk text, `coverage` describes the locally reconstructed
submitted chunks; its aggregate and Grammarly's web-editor display may differ.

## Adding or changing a checker

Keep adapters narrow and reproducible. Document the checker’s source,
dependencies, exact input/output contract, local-state boundary, and limits.
Do not silently patch a third-party checkout, embed credentials, or represent a
proprietary or reference-model signal as a factual verdict. Add deterministic
tests for parsing, chunking, aggregation, and failure behavior; keep live
network probes bounded and separate from the standard test suite.
