# Signal-viewer comparison prototypes

This directory records an exploratory comparison of two terminal UIs over the
same `checkers/signal/signal --raw --json` output. It is not a supported
application, editing interface, or product roadmap.

Both prototypes render source-token predictability colors plus perplexity,
top-10 fraction, and surface-tell counts. The scorer remains the Python signal
tool; these UIs only render its output.

## ink/ — Ink (React, Node)

```sh
cd ink
npm install
npm start -- ../../../checkers/grammarly/samples/diary-style.txt
```

Keys: `q` quits; `r` re-scores the input file.

Ink uses React's component model for terminal output, not the DOM. Its color
scale and segmentation live in `src/perplexity.ts` without Ink imports; terminal
rendering is isolated in `src/app.tsx`.

## textual/ — Textual (Python)

```sh
cd textual
uv run python app.py ../../../checkers/grammarly/samples/diary-style.txt
```

Keys: `q` quits; `r` re-scores the input file.

The Textual prototype also shells out to the scorer so that both stacks consume
the same interface. It uses Textual/Rich `Text.stylize` for token coloring.
