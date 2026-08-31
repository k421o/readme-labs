# Module: LLM Documentation Index Pointer

| Field | Value |
| --- | --- |
| Output | A short link to an AI-readable documentation index |
| Default placement | Near documentation or contributing; never after license |
| Applicability | Optional |
| Reader question | “Is there a curated machine-readable route through the documentation?” |

## Purpose

Expose a maintained `llms.txt`-style index without mixing retrieval metadata into the human onboarding path. Include this only when the repository actually maintains such an artifact.

## Inputs

- `{{LLMS_INDEX_PATH}}`: typically `llms.txt`.
- A current index pointing to canonical project documentation.
- Optional full-context file or hosted machine-readable documentation URL.

## Template

```markdown
## Machine-readable documentation

For a curated index of canonical project documentation, see [`{{LLMS_INDEX_PATH}}`]({{LLMS_INDEX_PATH}}).
```

## Compact documentation variant

Add this to an existing documentation paragraph instead of creating a section:

```markdown
Machine-readable documentation is indexed in [`llms.txt`](llms.txt).
```

## Rules

- Do not add the pointer before the index exists and is maintained.
- Keep the human README understandable without machine-facing files.
- Route only to canonical, current documentation.
- Avoid duplicating the entire README or source tree in the pointer text.
- Treat the format as an optional ecosystem convention, not a universal GitHub requirement.
- Update the index when public APIs, configuration, or canonical documentation routes change.

## Validation

- [ ] The index resolves from the README.
- [ ] Every indexed document is current and accessible to the intended audience.
- [ ] The index does not expose private material.
- [ ] Human and machine-facing descriptions do not contradict each other.
- [ ] Maintenance ownership is clear.

## Assembly note

Prefer the compact variant. If included as a full section, place it before license and add it to the table of contents.
