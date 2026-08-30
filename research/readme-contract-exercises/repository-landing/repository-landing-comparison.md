# Three-way comparison: repository landing page

| Variant | What it gets right | Main limitation |
| --- | --- | --- |
| [Original](repository-landing-original.md) | Gives a concise project identity, a directory map, and the root test command. | The map is organization-first rather than reader-task-first, and the opening description is vague. |
| [Contract revision](repository-landing-revised.md) | Routes a reader to the right surface, distinguishes the dependency-free package from optional checker runtimes, and keeps the verified root test path. | It deliberately omits detailed skill and checker instructions; that is appropriate only if the root README's job is orientation. |
| [Blind rebuild](repository-landing-blind.md) | Recovers many real package, skill, testing, and measurement details from source. | It turns a landing page into an operating manual: it duplicates skill contracts, checker setup, architecture rules, and policy that have more specific homes. Several claims become more categorical than their source evidence. |

## What the blind rebuild reveals

The blind agent inferred a coherent repository story, but filled its new
high-authority surface with material from `SKILL.md`, checker READMEs, tests,
and architecture notes. For example, it declares canonical implementations,
editing rules, dependency placement, and third-party details at the root. Much
of that is true in context, but it makes the root README a competing source of
authority and raises the cost of later change.

The contract revision favors a narrower role: answer where a visitor should go
next and provide only the command and boundary they need before doing so. The
result is shorter because the delivery contract is smaller, not because
shortness is inherently better.
