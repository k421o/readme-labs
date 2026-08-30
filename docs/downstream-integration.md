# Downstream integration

`readme-labs` is the upstream source of README domain knowledge and canonical
README capabilities. `repository-guidance` is a downstream bundle that owns
AGENTS.md guidance and cross-surface routing.

## Current state

`repository-guidance@v0.2.0` contains no editable README research or skill and
pins `readme-labs@v0.1.0` by release, commit, and tree hash. That immutable tag
exposes the earlier `readme-contract-review` skill and remains historical
compatibility evidence after the current source layout changes. It is not a
statement that the predecessor is actively supported.

The canonical source capability is `capabilities/readme-review`. A downstream
lock must never point to its moving branch or independently edit its generated
adapter. New README-domain work belongs here; a downstream migration selects an
intentional immutable release and evaluates the interface-name change.

## Allowed consumption models

In preferred order:

1. Add the repository-owned `readme-labs` Git marketplace at an immutable
   release or commit, install `readme-labs@readme-labs` through native Codex
   plugin discovery, and let the downstream bundle provide only its locally
   owned routing when composition supports that relationship.
2. Vendor a generated released capability with its upstream tag, commit, tree
   hash, and generator recorded, plus a CI synchronization check.
3. Use release automation to copy a capability into a distribution repository
   and verify that the released content is byte-identical to its source.

An independently edited copy is not an allowed model.

## Future upgrade checklist

1. Select a released README artifact and verify its signature or content hash.
2. Record the version, upstream revision, compatibility, and rollback version
   in `repository-guidance`.
3. Update installation or routing from the historical `readme-contract-review`
   interface to the released capability name; preserve AGENTS.md guidance
   locally.
4. Test discovery so README requests reach the released capability and
   AGENTS.md requests continue to reach their existing owner.
5. Replay downstream integration fixtures plus the upstream capability's
   published scenario set.
6. Confirm that no editable compatibility copy is reintroduced.
7. Document upgrade and rollback behavior in the downstream pull request.

## Dependency rule

```text
readme-labs domain and research
          ↓
released readme-review capability
          ↓
optional README plugin adapter
          ↓
repository-guidance bundle and routing
```

No arrow points back upward. Downstream needs can motivate an upstream issue or
change, but must not silently redefine the README taxonomy or skill.

Agent Labs and Agent Skills are not in this dependency chain. Any later Agent
Skills listing is an optional downstream consumer of an immutable README Labs
release, not a prerequisite for source development, discovery, installation,
or release.
