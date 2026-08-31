# Component contract

Use this contract for multi-component runs. The source module guides remain under `modular-templates/modules/`; the catalog classifies how each guide participates in a parallel run.

## Execution modes

| Mode | Ownership | Result |
| --- | --- | --- |
| `worker` | One subagent | One Markdown fragment and one evidence report |
| `owner-extension` | The named worker | Extra rules folded into its owner's fragment |
| `policy` | Parent and all relevant workers | A cross-cutting rule, never a standalone fragment |
| `derived` | Parent assembly step | Content computed only after worker headings exist |

This avoids false parallelism. A repository alias cannot safely compete with the title that contains it, relative-link rules apply across sections, and a table of contents cannot be finalized before headings exist.

## Run topology

```text
work/<run-id>/
|-- manifest.json
|-- shared-context.md
|-- briefs/
|   `-- <component-id>.md
|-- components/
|   `-- <component-id>.md
|-- reports/
|   `-- <component-id>.json
`-- assembled/
    `-- README.md
```

The parent may write `manifest.json`, `shared-context.md`, and `assembled/README.md`. Each worker may write only its matching file in `components/` and `reports/`.

## Fragment contract

- Emit final README Markdown only, without an outer code fence or authoring commentary.
- Follow the heading contract in the work packet. Only `project-title` may emit an `H1`.
- Do not leave `{{PLACEHOLDER}}`, TODO, or template-selection comments.
- Ground commands, paths, versions, capabilities, contacts, and legal statements in the target repository.
- Use repository-root-relative links for repository files.
- Do not rely on phrases such as "above" or "below" to make the fragment understandable.
- Do not change another component to resolve a mismatch; report the mismatch to the parent.

## Evidence report contract

Write a JSON object with this shape:

```json
{
  "component_id": "installation",
  "status": "ready",
  "source_files": [
    "pyproject.toml",
    "docs/install.md"
  ],
  "verified": [
    "The documented install command matches the package metadata."
  ],
  "unverified": [],
  "notes": "Optional integration note for the parent."
}
```

`source_files` are paths relative to the target repository. Use `status: "blocked"` and explain the gap in `unverified` when the repository does not establish a required fact. A blocked report must not be assembled.

## Integration gates

The run validator requires completed shared context, every worker fragment and report, a `ready` status, at least one evidence source and verified statement, no unverified claims, valid heading ownership, labeled code fences, and no unresolved template tokens. The parent must still check factual agreement between components, target-renderer anchors, link resolution, command execution, and repository-specific linting.
