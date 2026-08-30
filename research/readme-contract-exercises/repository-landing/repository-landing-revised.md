# Humanizer

Humanizer is a private, dependency-free Pi package with three installable prose
skills and the local tools used to measure and study them. Measurement results
are evidence to inspect; they are not authorship verdicts or writing targets.

## Start here

| Need | Location |
| --- | --- |
| Install or inspect an agent skill | `skills/` |
| Run a measurement adapter | `checkers/` |
| Reproduce or interpret a study | `experiments/` |
| Inspect an unfinished terminal UI comparison | `prototypes/` |
| Understand repository boundaries | [`docs/architecture.md`](docs/architecture.md) |

Run the repository's dependency-free regression suite from the root:

```sh
npm test
```

Checker environments are intentionally local to each adapter. Follow the setup
and usage instructions for [Grammarly](checkers/grammarly/README.md),
[Binoculars](checkers/binoculars/README.md), or
[signal](checkers/signal/README.md) rather than assuming the root package
installs their optional runtimes.
