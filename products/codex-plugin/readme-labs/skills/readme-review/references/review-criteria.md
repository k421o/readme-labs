# Review criteria

## Decision table

| Information | Expected when | Surprising or noisy when |
| --- | --- | --- |
| Title and definition | Always | It repeats a name without saying what the component is. |
| Purpose or differentiators | Choice or scope is not obvious | Promotional, generic, or unsupported claims replace facts. |
| Install or download | The artifact is consumed or run | The repository is documentation-only, or a volatile canonical installer is duplicated without context. |
| Usage or example | Readers can exercise an interface | The example is an untested tutorial, generated output, or pseudocode. |
| Documentation or API route | Depth lives elsewhere or the interface is broad | An unclassified link list duplicates visible structure. |
| Compatibility or status | A reader decision depends on it | An undated or unsupported quality/status claim appears. |
| Build, test, or development | Contributors need repository-specific steps | Generic commands merely restate an obvious manifest. |
| Support or security | Channels or disclosure paths differ | Every request is sent to one ambiguous place. |
| Contribution or governance | External participation is supported | Long policy duplicates canonical maintained documents. |
| License, citation, or credit | Distribution or attribution requires it | Long legal text duplicates the canonical file. |
| Roadmap or history | Current use requires lifecycle context | Plans and abandoned ideas appear as current documentation. |
| Directory map | Categorization reveals architecture or ownership | Self-explanatory names are paraphrased and likely to drift. |

Ask both:

> If this unit disappeared, would a capable reader be more likely to
> misunderstand, misuse, or fail to adopt this component?

> If a conventional category is absent, is its question inapplicable, clearly
> routed to a canonical surface, or actually unanswered?

## Common low-signal content

- Directory listings whose names are self-explanatory.
- Conversation or implementation residue such as “formerly,” “we removed,” or
  defenses of the current repository shape.
- Agent policy disguised as reader documentation.
- Plans, open questions, future intentions, or abandoned design discussions
  presented as current behavior.
- Generic recommendations unrelated to the component.
- Badge, sponsor, contributor, or governance walls before project identity and
  the first reader path.
- Unsupported “canonical,” “safe,” “production-ready,” or compatibility claims.
- Prose that merely paraphrases a manifest, configuration schema, command help,
  or visible layout without adding usage context.
- Manual tables of contents that do not materially help a long document.

## High-value exceptions

Keep content when it explains a non-obvious interface, input/output contract,
working-directory assumption, failure mode, fixture irregularity, experimental
method, dated result, security/privacy boundary, package-rendering surface, or
current design constraint that a capable maintainer would otherwise reverse.
