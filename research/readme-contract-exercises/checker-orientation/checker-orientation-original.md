# Checkers

This directory holds measurement adapters that take text in and return
structured evidence. Their output is noisy evidence, not an authorship verdict
or a writing target.

## Contract

A checker is a small executable that accepts a file or stdin and emits JSON:

```json
{
  "checker": "grammarly",
  "version": "0.1.0",
  "checked_at": "2026-08-15T00:00:00Z",
  "input": {
    "path": "text.md",
    "sha256": "abc123..."
  },
  "score": {
    "overall": 42,
    "unit": "percent-ai",
    "chunks": [{ "words": 1188, "score": 40 }]
  },
  "localizations": [],
  "note": "External measurement; score is an estimate and varies by session/text."
}
```

The important property is that a checker preserves input identity, run context,
and any available localization instead of returning an unexplained number.

## Available tools

- **Grammarly AI check** (`grammarly/`) emits a score plus a run receipt with
  the input hash, timestamp, checker version, and chunk evidence. Its endpoint
  is undocumented and anonymous, so batch usage stays small and polite.
- **Binoculars** (`binoculars/`) points to a pinned, external
  [`ahans30/Binoculars`](https://github.com/ahans30/Binoculars) sibling
  checkout and provides the local MPS launcher. Upstream source, model weights,
  and its virtual environment are not vendored here. Its Falcon-model ratio is
  a research measurement, not an authorship verdict, and it does not reproduce
  Grammarly's signal.
- **`signal`** (`signal/`) is the local
  navigation aid. It provides perplexity, burstiness, and deterministic
  surface-tell spans but no authorship claim.
- **`human-voice` linter** (`../skills/human-voice/scripts`)
  is a cheap deterministic floor for lexical/structural tells.
