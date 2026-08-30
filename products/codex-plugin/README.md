# Codex plugin adapter

[`readme-labs/`](readme-labs/) is an installable experimental plugin produced
from the canonical [`readme-review`](../../capabilities/readme-review/) skill.
The packaged skill directory is generated and must not be edited directly.

Rebuild or check it with:

```console
uv run python scripts/build_plugin.py
uv run python scripts/build_plugin.py --check
```

The adapter intentionally has no marketplace entry. Installation and a public
release are separate product-maturity decisions; this directory currently
proves packaging validity and a reproducible source boundary only.
