# Three-way comparison: prototype record

| Variant | What it gets right | Main limitation |
| --- | --- | --- |
| [Original](prototype-record-original.md) | Documents both runnable stacks and enough implementation context to understand the comparison. | It contains future-facing directions such as a web port, a patch-edit loop, and choosing a winner. Those plans receive too much authority in a commonly consulted file. |
| [Contract revision](prototype-record-revised.md) | Keeps the prototype boundary, working-directory-sensitive commands, shared scorer, and implementation differences while removing roadmap pressure. | It leaves out some useful metric interpretation that could be appropriate if this README is the primary user interface. |
| [Blind rebuild](prototype-record-blind.md) | Produces a clear and mostly well-scoped runnable prototype README. It makes the experiment boundary explicit and links the signal checker for deeper details. | It adds many presentation and model-interpretation details that duplicate the signal checker, and it promotes implementation intent (“so it can be reused elsewhere”) into a durable direction. |

## What the blind rebuild reveals

This is the strongest blind result because the repository itself makes the
prototype's purpose, entry points, and dependencies relatively easy to infer.
Even here, however, the blind approach expands the README into a metric guide
and a design rationale that overlap with the scorer documentation.

The useful synthesis is not “always delete and rebuild.” It is that a blind
rebuild can expose a document's likely interface, while a second contract pass
is still needed to remove duplicated authority, unsupported inferences, and
roadmap pull.
