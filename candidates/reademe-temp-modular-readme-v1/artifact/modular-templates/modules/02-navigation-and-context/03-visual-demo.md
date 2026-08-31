# Module: Visual Demo

| Field | Value |
| --- | --- |
| Output | A screenshot, animated demo, or terminal recording |
| Default placement | After key features and before setup |
| Applicability | Optional |
| Reader question | “What does success look like before I install this?” |

## Purpose

Show the project performing its primary job. A useful demo provides proof and orientation; it is distinct from the identity banner and from an architecture diagram.

## Inputs

- `{{DEMO_PATH}}`: durable local screenshot or animation path.
- `{{DEMO_ALT_TEXT}}`: content and outcome visible in the demo.
- `{{DEMO_CAPTION}}`: one sentence explaining the scenario.
- `{{FULL_DEMO_URL}}`: optional accessible video or terminal-session link.

## Template

```markdown
## Demo

![{{DEMO_ALT_TEXT}}]({{DEMO_PATH}})

{{DEMO_CAPTION}}

<!-- Optional: link when an accessible full recording exists. -->
[View the full demonstration]({{FULL_DEMO_URL}}).
```

## Rules

- Demonstrate the primary path, not an edge case.
- Remove secrets, personal data, internal hostnames, and unstable timestamps before capture.
- Prefer a concise loop for animation; provide a static alternative or textual explanation for accessibility.
- Store durable media in the repository when size and policy permit.
- Optimize assets so the README remains responsive.
- Explain what readers should notice rather than relying on motion alone.

## Validation

- [ ] The demo represents the current interface and command syntax.
- [ ] The asset renders in the target host and a fork.
- [ ] Alt text conveys the result.
- [ ] The caption supplies context absent from the image.
- [ ] No sensitive information is visible.

## Assembly note

Place this before installation when visual confirmation helps readers decide to proceed. Use the [banner module](../01-header-and-identity/03-banner-or-logo.md) for branding and the [architecture module](04-architecture-overview.md) for system relationships.
