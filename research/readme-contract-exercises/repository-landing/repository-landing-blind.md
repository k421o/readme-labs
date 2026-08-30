# Humanizer

Humanizer is a source-preserving prose-quality toolkit for agent harnesses. It
packages three reusable skills, plus local checkers and experiments for
reviewing writing with care for the writer's facts, citations, structure, and
intended register.

The project is designed for human review, not authorship judgments. Its
localizers identify passages worth rereading; they do not determine who wrote
text, certify quality, or guarantee an external checker outcome.

## What's included

- **`human-voice`** — drafts, audits, or narrowly revises prose while keeping
  its meaning and constraints intact.
- **`de-slop`** — finds repetition, template-like structure, vague wording, and
  register mismatches for a targeted review.
- **`detector-gate`** — supports a conservative final pass using concrete,
  source-anchored review locations.
- **`signal`** — a bundled localizer with a dependency-free `--localize` mode;
  model-backed analysis is optional.
- **Research and checkers** — reproducible experiments and measurement tools,
  including a receipt-producing Grammarly wrapper.

The installable surface is declared in [`package.json`](package.json):

```text
skills/
├── human-voice/
├── de-slop/
└── detector-gate/
```

Each skill is self-contained so a consumer can copy it without the rest of the
repository.

## Quick start

The core package has no root dependencies. You need Python 3 and Node.js to run
the full test suite.

```sh
git clone <repository-url>
cd humanizer
npm test
```

To locate deterministic surface patterns in a document without downloads,
model libraries, or network access:

```sh
skills/de-slop/scripts/signal path/to/draft.md --localize --json
```

The JSON reports matched spans and their source offsets, lines, and columns.
Read each match in context: it is a prompt for review, not an error or a
rewrite instruction.

## Using the skills

Point a compatible agent harness at the skill directories listed in the
`pi.skills` field of [`package.json`](package.json). Start with the appropriate
skill file:

- [`skills/human-voice/SKILL.md`](skills/human-voice/SKILL.md) for drafting,
  revising, or auditing prose for an audience and register.
- [`skills/de-slop/SKILL.md`](skills/de-slop/SKILL.md) for an audit or a narrow,
  source-preserving revision.
- [`skills/detector-gate/SKILL.md`](skills/detector-gate/SKILL.md) for a
  cautious final review.

The skills distinguish audits from edits. They preserve claims, links,
citations, code, defined terms, and required structure; edits happen only when
requested.

## Checkers and experiments

`checkers/` contains measurement utilities, not writing policy. The
repository-facing `checkers/signal/` adapter exposes the implementation bundled
with `de-slop`; keep the skill copy canonical.

The optional model-backed `signal` mode uses `uv`, Python 3.11–3.12, PyTorch,
and Transformers. See [`checkers/signal/pyproject.toml`](checkers/signal/pyproject.toml).
The dependency-free `--localize` mode does not need those dependencies.

`checkers/grammarly/` wraps a Grammarly AI-check run in a JSON receipt that
records the input identity, checker version, duration, upstream payload, and
failures. It requires Node.js, Playwright, a Chrome channel, and network access:

```sh
cd checkers/grammarly
npm install
python3 run.py path/to/draft.md --pretty
```

Treat any external-checker output as limited measurement evidence, never as a
quality, authorship, or pass/fail verdict. The wrapper emits an error receipt
instead of inventing a score when its upstream check fails.

`experiments/` holds runnable studies and their findings; `docs/` records
architecture and long-lived decisions. Generated candidates and checker
receipts are intentionally excluded from version control.

## Development

Run all repository tests with:

```sh
npm test
```

The suite checks the dependency-free package contract, skill resources and
links, localizer behavior, and the Grammarly wrapper's offline receipt
handling. It does not invoke a live Grammarly scan.

When changing a skill, retain its self-contained resources and resolve paths
relative to that skill's `SKILL.md`. Keep root dependencies out of
[`package.json`](package.json); optional runtimes belong beside the checker or
prototype that uses them. See [`docs/architecture.md`](docs/architecture.md)
for the repository layout and conventions.

## Third-party notices

`human-voice` is derived from Stephen Offer's MIT-licensed
[`human-voice`](https://github.com/stephenoffer/human-voice) project. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
[`skills/human-voice/LICENSE`](skills/human-voice/LICENSE) for attribution and
license details.
