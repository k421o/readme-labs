# Measurement adapters

Choose a tool by the evidence you need. These adapters return measurements or
localizations to inspect; none establishes authorship or prose quality.

| Need | Tool | Contract and setup |
| --- | --- | --- |
| A live external AI-score estimate with a reproducible run receipt | [Grammarly](grammarly/README.md) | Network-backed; its README covers setup, receipts, and calibration. |
| A local Falcon-model ratio using the pinned sibling checkout | [Binoculars](binoculars/README.md) | The source checkout, model weights, and virtual environment are external to this repository. |
| Local perplexity, burstiness, and deterministic source spans | [signal](signal/README.md) | `--localize` works without the model-backed runtime. |
| A deterministic lexical and structural floor | [`human-voice`](../skills/human-voice/SKILL.md) | Installed as a skill rather than a checker runtime. |

Each tool owns its dependencies, command interface, samples, and run-output
handling. Use its own README or skill instructions for commands; do not infer a
shared JSON schema, environment, or interpretation rule from this index.
