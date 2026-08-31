# Module: Architecture Overview

| Field | Value |
| --- | --- |
| Output | A bounded component-and-flow summary |
| Default placement | Before operational setup or after the first usage example |
| Applicability | Conditional |
| Reader question | “What are the major parts, and how does information move between them?” |

## Purpose

Give readers the smallest system model needed to understand setup, extension points, or deployment boundaries. Keep design history and exhaustive component detail in dedicated architecture documentation.

## Inputs

- `{{INPUT}}`: the initiating data, request, or event.
- `{{COMPONENT_A}}`, `{{COMPONENT_B}}`, `{{COMPONENT_C}}`: major responsibilities.
- `{{OUTPUT}}`: the observable result.
- `{{ARCHITECTURE_DOC_PATH}}`: optional deeper documentation path.

## Template

````markdown
## Architecture

```mermaid
flowchart LR
    INPUT[{{INPUT}}] --> A[{{COMPONENT_A}}]
    A --> B[{{COMPONENT_B}}]
    B --> C[{{COMPONENT_C}}]
    C --> OUTPUT[{{OUTPUT}}]
```

| Component | Responsibility |
| --- | --- |
| `{{COMPONENT_A}}` | {{RESPONSIBILITY}} |
| `{{COMPONENT_B}}` | {{RESPONSIBILITY}} |
| `{{COMPONENT_C}}` | {{RESPONSIBILITY}} |

For boundaries, deployment decisions, and failure modes, see [the architecture guide]({{ARCHITECTURE_DOC_PATH}}).
````

## Rules

- Show only components necessary to understand the primary path.
- Label edges when the transferred data or protocol is not obvious.
- Keep the prose and responsibility table consistent with the diagram.
- Use stable conceptual names rather than transient instance identifiers.
- Delegate architecture decisions and historical rationale to ADRs or a deeper guide.
- Provide a textual explanation because not every renderer or assistive tool will interpret Mermaid.

## Validation

- [ ] Mermaid syntax renders in the target host.
- [ ] Every node corresponds to a current responsibility.
- [ ] Direction and boundaries match the implementation.
- [ ] The textual table makes the core model understandable without the diagram.
- [ ] The deeper link resolves when retained.

## Assembly note

Place architecture before installation when it changes setup choices. Otherwise, a short usage example can come first so readers see value before internal structure.
