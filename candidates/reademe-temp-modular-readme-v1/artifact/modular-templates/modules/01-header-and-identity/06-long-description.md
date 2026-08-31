# Module: Long Description

| Field | Value |
| --- | --- |
| Output | One to three conceptual paragraphs |
| Default placement | After the short description and before navigation |
| Applicability | Optional |
| Reader question | “What problem does this solve, and how does its approach help?” |

## Purpose

Expand the value proposition without turning the header into implementation documentation. Explain the core problem, the project's approach, and its high-level capabilities.

## Inputs

- `{{CORE_PROBLEM}}`: specific friction or unmet need.
- `{{PRIMARY_SOLUTION}}`: the project's approach.
- `{{HIGH_LEVEL_CAPABILITIES}}`: the most important outcomes, summarized in prose.
- `{{BOUNDARY}}`: what the project deliberately does not attempt, when useful.

## Template

```markdown
{{CORE_PROBLEM}}

{{PROJECT_NAME}} addresses this by {{PRIMARY_SOLUTION}}. It supports {{HIGH_LEVEL_CAPABILITIES}}.

<!-- Optional boundary sentence. -->
It is designed for {{INTENDED_SCOPE}}; {{OUT_OF_SCOPE_CAPABILITY}} remains outside its scope.
```

## Rules

- Explain “what” and “why” before “how.”
- Keep history, design deliberations, and exhaustive architecture in dedicated documents.
- Avoid repeating the short description word for word.
- Use a [key-features module](../02-navigation-and-context/02-key-features.md) when capabilities scan better as a list.
- Introduce a formal `## Overview` heading only when the content is long enough to deserve a TOC entry.

## Validation

- [ ] The problem is specific enough to recognize.
- [ ] The solution describes the project's approach without unsupported superlatives.
- [ ] Capabilities match the current implementation.
- [ ] The block can be read without prior domain history.
- [ ] Deep background has been linked or removed.

## Assembly note

Keep this in the identity block when it is only a few paragraphs. For a formal overview section, add `## Overview` and include it in the table of contents.
