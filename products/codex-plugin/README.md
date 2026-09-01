# Codex plugin adapter

[`readme-labs/`](readme-labs/) is an installable experimental plugin produced
from the canonical [`readme-review`](../../capabilities/readme-review/) and
[`readme-generate`](../../capabilities/readme-generate/) skills. The packaged
skill directories are generated and must not be edited directly.

Rebuild or check it with:

```console
uv run python scripts/build_plugin.py
uv run python scripts/build_plugin.py --check
```

The repository exposes the adapter through its own local/Git marketplace so
Codex can discover and install it through the native plugin flow. That
mechanical installation channel is not a public or verified marketplace
listing, and it does not transfer source authority away from `readme-labs`.
