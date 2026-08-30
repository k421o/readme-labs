# Humanizer

Humanizer is a small prose-quality lab with two deliverables: self-contained agent
skills and the measurement tools used to evaluate them. It keeps detector output
in its proper role—as noisy evidence to inspect, not an authorship verdict or a
writing target.

The measurement adapters include the network-backed Grammarly checker and a
local MPS adapter for the sibling Binoculars checkout.

## Repository map

| Directory | Purpose |
| --- | --- |
| `skills/` | Installable, dependency-free agent skills. Each skill is self-contained. |
| `checkers/` | Text-in/evidence-out measurement adapters and their runtimes. |
| `experiments/` | Reproducible study code, calibration notes, and findings. |
| `prototypes/` | Exploratory interfaces that are not production tools. |
| `docs/` | Architecture, decisions, research, and explicitly historical material. |
| `tests/` | Package contracts and offline regression coverage. |

See [`docs/architecture.md`](docs/architecture.md) for the boundaries between
those areas and the source-of-truth rules for bundled skill resources.

## Quick start

Run the dependency-free test suite from the repository root:

```sh
npm test
```

The model-backed signal checker and the Grammarly adapter have separate,
optional environments; their setup instructions live in the corresponding
`checkers/` subdirectories.
