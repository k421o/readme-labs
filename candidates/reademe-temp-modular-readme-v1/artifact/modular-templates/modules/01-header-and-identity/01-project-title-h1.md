# Module: Project Title (`H1`)

| Field | Value |
| --- | --- |
| Output | One top-level heading |
| Default placement | First substantive line |
| Applicability | Required |
| Reader question | “What project am I looking at?” |

## Purpose

Give the repository one unambiguous human-facing identity. The title is the document's sole `H1` and the anchor for every section that follows.

## Inputs

- `{{PROJECT_NAME}}`: the official display name, with stable capitalization.

## Template

```markdown
# {{PROJECT_NAME}}
```

## Rules

- Use exactly one `H1` in the README.
- Place it before banners, badges, descriptions, and section headings.
- Use a concise name, not a slogan or full sentence.
- Keep spelling and capitalization consistent with the product and package metadata.
- When the display name differs materially from the repository slug, apply the [repository alias module](02-repository-alias.md).

## Validation

- [ ] The rendered title immediately identifies the project.
- [ ] The file contains no other line beginning with a single `#`.
- [ ] The title is not duplicated by a logo-only heading.
- [ ] The display name matches the project's canonical naming.

## Assembly note

This module always comes first. The optional alias modifies this line; it does not add another heading.
