# Downstream integration

`readme-labs` is the upstream source of README domain knowledge and canonical
README capabilities. `repository-guidance` is a downstream bundle that owns
AGENTS.md guidance and cross-surface routing.

## Current state

The experimental plugin adapter is valid and installable from the source tree,
but no evidence-backed README capability release has been cut. Therefore the
existing README material in `repository-guidance` remains a temporary
compatibility source. New README-domain research and editable capability work
belongs here.

Creating the new repository does not by itself authorize deletion or rewiring
in the downstream repository. Migration begins after an upstream artifact
passes the release gates in [`release-policy.md`](release-policy.md).

## Allowed consumption models

In preferred order:

1. Install the released README plugin alongside `repository-guidance` and let
   the downstream bundle provide discovery and routing, when plugin composition
   supports that relationship.
2. Vendor a generated released capability with its upstream tag, commit, tree
   hash, and generator recorded, plus a CI synchronization check.
3. Use release automation to copy a capability into a distribution repository
   and verify that the released content is byte-identical to its source.

An independently edited copy is not an allowed model.

## Migration checklist

1. Select a released README artifact and verify its signature or content hash.
2. Record the version, upstream revision, compatibility, and rollback version
   in `repository-guidance`.
3. Replace the old README review implementation with installation, generated
   vendoring, or a narrow router; preserve AGENTS.md guidance locally.
4. Test discovery so README requests reach the released capability and
   AGENTS.md requests continue to reach their existing owner.
5. Replay downstream integration fixtures plus the upstream capability's
   published scenario set.
6. Remove the temporary compatibility copy only after the replacement is
   available through the actual installation path.
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
