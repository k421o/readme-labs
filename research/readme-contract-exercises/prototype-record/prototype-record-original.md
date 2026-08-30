# Signal viewer prototypes

Same feature, two stacks, built side by side to compare the developer experience
and to see which produces more reusable parts. Both render a file's prose in the
terminal with each token background-colored by how predictable it is (hot = the
model's obvious next pick = predictable under the reference model; cool/green = surprising),
plus a metrics line (perplexity, top-10 fraction, surface-tell count).

Both shell out to `checkers/signal/signal` with `--raw --json`, so token
offsets line up with the file's exact bytes. Scoring engine = Python; the UIs just
render its output.

## ink/ — Ink (React, Node)

```sh
cd ink
npm install
npm start -- ../../../checkers/grammarly/samples/diary-style.txt
```

Keys: `q` quit · `r` re-score (after you or an agent edits the file).

Note on the "reusable for web" question: Ink uses React's component/hook model but
renders to the terminal, not the DOM — `<Box>`/`<Text>` don't drop into a webpage.
What *does* port is pure logic. So the color scale + segmentation live in
`src/perplexity.ts` with **no Ink imports** (it exposes `css*` fields alongside
`ink*`), and `src/app.tsx` is the only terminal-specific file. Mine `perplexity.ts`
for a web React version later.

## textual/ — Textual (Python)

```sh
cd textual
uv run python app.py ../../../checkers/grammarly/samples/diary-style.txt
```

Keys: `q` quit · `r` re-score.

Because the scorer is already Python, this prototype can later drop the subprocess
and call the scoring function in-process (Textual `@work(thread=True)` keeps the UI
responsive during inference). The MVP shells out for parity with Ink.

## What to compare

- How much code each took, and how it reads.
- Per-token coloring: Ink nested `<Text>` spans vs. Textual/Rich `Text.stylize`.
- Live re-render feel on `r`.
- Which one you'd rather extend into the patch-edit + live-rescore loop.

Neither does in-place editing yet — that's the next layer once a viewer wins.
