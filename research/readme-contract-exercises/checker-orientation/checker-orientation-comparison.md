# Three-way comparison: checker orientation index

| Variant | What it gets right | Main limitation |
| --- | --- | --- |
| [Original](checker-orientation-original.md) | States the evidence-not-verdict boundary and identifies the available tools. | Its generic JSON example implies a shared schema that the real adapters do not share. |
| [Contract revision](checker-orientation-revised.md) | Makes the page a tool-selection index; the table points to each adapter's maintained runtime and interpretation contract. | It provides little immediate operational detail, by design. A reader must follow the selected link. |
| [Blind rebuild](checker-orientation-blind.md) | Supplies clear selection criteria, realistic runtimes, and useful cautions. | It reintroduces a large amount of operating policy and detailed measurement interpretation that belongs with individual adapters. It also calls each subdirectory “authoritative” and treats inferred maintenance practices as universal rules. |

## What the blind rebuild reveals

The agent correctly sees that this file can help a reader choose a checker.
However, it treats that role as permission to summarize every tool's setup,
limits, calibration, input handling, and future contributor policy. This is
the most important failure mode for README rebuilding: a model can reconstruct
accurate prose while still making the documentation topology worse.

The contract revision is intentionally an index rather than a second API and
policy manual. It avoids a shared output schema and sends the reader to the
specific interface where a command or interpretation rule is maintained.
