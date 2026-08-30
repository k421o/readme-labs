# Module: Agent Instructions Pointer

| Field | Value |
| --- | --- |
| Output | A short discovery link to `AGENTS.md` |
| Default placement | Near contributing; never after license |
| Applicability | Optional |
| Reader question | “Where are repository-specific instructions for coding agents and automated contributors?” |

## Purpose

Keep exact machine execution rules in a dedicated `AGENTS.md` while making that sidecar discoverable to human contributors who use coding agents.

## Inputs

- `{{AGENTS_PATH}}`: normally `AGENTS.md`.
- A maintained sidecar containing exact commands, repository layout, constraints, conventions, and definition of done.

## Template

```markdown
## Coding-agent instructions

Automated contributors and coding agents must follow [the repository instructions]({{AGENTS_PATH}}), including the required validation commands and definition of done.
```

## Compact contributing variant

When a dedicated section would be excessive, add this sentence to `## Contributing` instead:

```markdown
If you use a coding agent, also follow [AGENTS.md](AGENTS.md).
```

## Sidecar boundary

Keep these details in `AGENTS.md`, not in the README:

- exact build, test, lint, and formatting commands;
- directory-by-directory repository map;
- code-generation restrictions and project idioms;
- protected or generated paths;
- task-specific definition of done.

## Validation

- [ ] `AGENTS.md` exists at the linked path.
- [ ] Its commands match current tooling.
- [ ] Its scope and precedence are understandable.
- [ ] The README contains only the discovery pointer, not a duplicate instruction set.
- [ ] Human contribution requirements remain complete without agent tooling.

## Assembly note

Place the full section before license, usually near contributing. Prefer the compact variant when agent discovery does not warrant its own TOC entry.
