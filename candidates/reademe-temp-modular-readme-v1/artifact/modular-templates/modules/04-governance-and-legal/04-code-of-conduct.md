# Module: Code of Conduct

| Field | Value |
| --- | --- |
| Output | A conduct-policy and enforcement pointer |
| Default placement | Immediately after contributing |
| Applicability | Conditional |
| Reader question | “Which behavior standard applies, and where are incidents reported?” |

## Purpose

Make community expectations and the authoritative enforcement process easy to find without copying the policy into the README.

## Inputs

- `{{CODE_OF_CONDUCT_PATH}}`: usually `CODE_OF_CONDUCT.md`.
- `{{ENFORCEMENT_CHANNEL}}`: private channel defined by that policy.
- The scope of spaces and events covered by the policy.

## Template

```markdown
## Code of conduct

Participation in this project is governed by the [code of conduct]({{CODE_OF_CONDUCT_PATH}}). Report conduct incidents through {{ENFORCEMENT_CHANNEL}} rather than a public issue.
```

## Rules

- Link one canonical policy rather than restating it.
- Ensure the policy identifies scope, enforcement responsibilities, and a private report route.
- Use a monitored channel distinct from ordinary issue reporting.
- Avoid naming individual enforcement contacts in the README when a durable team channel exists.
- Do not add this section when a clear link in contributing already provides sufficient visibility.

## Validation

- [ ] The policy link resolves.
- [ ] The enforcement channel is private and monitored.
- [ ] Scope and repository settings agree with the policy.
- [ ] The README wording does not conflict with the full text.
- [ ] Maintainers know how reports are handled.

## Assembly note

This module follows contributing. When only a compact pointer is needed, keep the code-of-conduct sentence inside the contributing module and omit this section.
