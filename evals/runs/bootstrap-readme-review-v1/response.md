# Bootstrap response

## Finding

**Material — the README has no consumer path.**

[`README.md` lines 5–10] contains only development installation and test
commands. The package manifest exposes an installable `pebble-count` console
entry point at [`pyproject.toml` lines 14–15], and that entry point executed
successfully against the README during verification. A reader can learn what
the package counts but cannot learn how to install it for use, invoke it, or
interpret its output without inspecting repository internals.

Restore a short consumer installation and one copyable invocation before the
Development section; keep contributor dependencies and `pytest` in
Development.

## Verification limits

The fixture's unit test passed and the declared console entry point ran. The
README mutation was evaluated in a local Git repository. No package-registry
rendering or external links were involved.
