# Signal viewer prototypes

Two exploratory terminal interfaces for inspecting the local signal checker's
per-token predictability data. They render the original file with a continuous
negative-log-likelihood (NLL) color ramp and overlay deterministic surface tells.

These are prototypes, not production tooling. The display is a navigation aid for
reviewing prose in context; it is not an authorship, quality, or acceptance
assessment. Do not optimize writing merely to change the displayed metrics.

## Choose an implementation

| Implementation | Location | Runtime |
| --- | --- | --- |
| Ink | [`ink/`](ink/) | Node.js, React, and Ink |
| Textual | [`textual/`](textual/) | Python and Textual |

Both implementations run `checkers/signal/signal` from this repository with
`--raw --json --map`. Model-backed scoring therefore needs the signal checker's
optional environment and model cache; see the [signal checker setup](../../checkers/signal/README.md#setup).

## Run

From the repository root, provide a UTF-8 text or Markdown file to inspect.

### Ink

```sh
cd prototypes/signal-viewer/ink
npm ci
npm start -- ../../../path/to/draft.md
```

### Textual

```sh
cd prototypes/signal-viewer/textual
uv sync
uv run python app.py ../../../path/to/draft.md
```

Press `r` to score the file again or `q` to quit. The first model-backed run may
take longer while the signal checker creates its environment and downloads GPT-2.

## Reading the display

The header reports document perplexity, the fraction of tokens in the model's
top-10 predictions, and the number of surface tells. Text color represents NLL:

- Red: predictable under the reference model.
- Light gray: neutral.
- Blue: comparatively surprising under the reference model.
- Bold text on amber: a deterministic surface-tell match.

The ramp is deliberately foreground-only so the terminal's background remains
readable. Amber overlays retain the underlying NLL color while drawing attention
to the exact tell span.

All color thresholds and RGB values live in [`palette.json`](palette.json). It
is the shared source of truth: changing it updates both prototypes. The Ink
implementation keeps its scoring and segmentation logic in
[`ink/src/perplexity.ts`](ink/src/perplexity.ts), which is intentionally separate
from rendering so it can be reused elsewhere.

## Notes and limits

- The file is passed with `--raw`, so displayed token offsets align with its
  unmodified source rather than a Markdown-stripped representation.
- Perplexity and rank-based values are relative GPT-2 reference-model signals.
  They are most useful for comparing revisions and choosing spans to read, not
  as thresholds or verdicts.
- Surface tells are deterministic pattern matches. Treat them as prompts to
  inspect the surrounding prose and source, not automatic defects.

For the scorer's full CLI options, metric definitions, and environment details,
refer to [`checkers/signal/README.md`](../../checkers/signal/README.md).
