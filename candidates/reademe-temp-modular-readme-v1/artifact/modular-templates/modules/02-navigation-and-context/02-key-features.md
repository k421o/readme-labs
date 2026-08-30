# Module: Key Features

| Field | Value |
| --- | --- |
| Output | A short outcome-oriented capability list |
| Default placement | After the TOC, or after the description when no TOC exists |
| Applicability | Recommended |
| Reader question | “What can this project do for me?” |

## Purpose

Convert the high-level value proposition into concrete, scannable capabilities without reproducing the full usage or API reference.

## Inputs

- Three to seven current capabilities.
- The user outcome associated with each capability.
- Any boundary or maturity label readers need to interpret a feature accurately.

## Template

```markdown
## Key features

- **{{FEATURE_NAME}}** — {{USER_OUTCOME}}.
- **{{FEATURE_NAME}}** — {{USER_OUTCOME}}.
- **{{FEATURE_NAME}}** — {{USER_OUTCOME}}.
```

## Rules

- Lead with the capability name and end with its practical outcome.
- Keep items parallel in grammar and detail.
- Describe shipped behavior, not roadmap promises.
- Avoid duplicating installation steps or full API signatures.
- Link a feature to deeper documentation only when the destination adds useful detail.
- Order items by reader value, not internal component order.

## Validation

- [ ] Every bullet maps to a current, testable capability.
- [ ] The list distinguishes this project from its category description.
- [ ] Bullets use parallel phrasing.
- [ ] Experimental behavior is labeled.
- [ ] The list remains brief enough to scan in a few seconds.

## Assembly note

Use this module instead of loading the long description with a capability catalog. A demo or architecture module can follow when the features benefit from visual evidence.
