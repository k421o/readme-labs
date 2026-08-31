# Module: Table of Contents

| Field | Value |
| --- | --- |
| Output | An internal navigation list |
| Default placement | After the identity block |
| Applicability | Conditional; recommended for long READMEs |
| Reader question | “Where is the information I need?” |

## Purpose

Turn a long README into a scannable interface. The recovered guidance uses 100 lines as the trigger for adding a table of contents; this kit treats that as a practical house threshold rather than a GitHub requirement.

## Inputs

- The final ordered list of `H2` sections.
- Important `H3` subsections that readers must reach directly.
- The anchor behavior of the target Markdown renderer.

## Template

```markdown
## Table of contents

- [Key features](#key-features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Configuration](#configuration)
- [API](#api)
- [Contributing](#contributing)
- [License](#license)
```

Replace the example entries with the sections actually present.

## Rules

- Omit the project `H1` and the table-of-contents heading from its own list.
- Include all major `H2` sections in document order.
- Include only high-value `H3` destinations; mirroring every deep heading creates noise.
- Indent nested entries consistently.
- Derive anchors from the final heading text, including punctuation and repeated headings.
- Prefer generated navigation when the repository already has a trusted TOC tool; otherwise maintain the list with the section changes.

## Anchor examples

| Heading | Typical GitHub-style anchor |
| --- | --- |
| `## Key features` | `#key-features` |
| `## Usage & FAQ` | `#usage--faq` |
| `## API reference` | `#api-reference` |

Do not assume these examples apply identically to every renderer; verify them where the README will be published.

## Validation

- [ ] Every included entry matches a current heading.
- [ ] Every anchor navigates to the intended section.
- [ ] Entry order matches document order.
- [ ] Duplicate headings resolve to the correct generated suffix.
- [ ] The TOC improves scanning rather than dominating the page.

## Assembly note

Finalize the TOC after all other modules are assembled. It appears near the top but should be one of the last fragments edited.
