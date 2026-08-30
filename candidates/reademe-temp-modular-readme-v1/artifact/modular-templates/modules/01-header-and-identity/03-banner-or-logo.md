# Module: Banner or Logo

| Field | Value |
| --- | --- |
| Output | One project-identifying image |
| Default placement | Directly below the `H1` |
| Applicability | Optional |
| Reader question | “Can I recognize this project and its purpose at a glance?” |

## Purpose

Provide fast visual identity or show the project's primary output. Prefer a maintained repository asset so the visual survives renames, forks, and external hosting changes.

## Inputs

- `{{PROJECT_NAME}}`: used in accessible alternative text.
- `{{BANNER_PATH}}`: path from the root README, such as `docs/assets/banner.png`.
- `{{VISUAL_SUMMARY}}`: short description of what the image conveys.

## Template

```markdown
![{{PROJECT_NAME}} — {{VISUAL_SUMMARY}}]({{BANNER_PATH}})
```

## Centered variant

Use only if the repository's Markdown rules allow raw HTML:

```html
<p align="center">
  <img src="{{BANNER_PATH}}" alt="{{PROJECT_NAME}} — {{VISUAL_SUMMARY}}">
</p>
```

## Rules

- Use a logo for identity, a screenshot for an application, or a simple diagram for a library or platform.
- Keep the source asset in the repository when practical.
- Write alt text that communicates meaning rather than “banner image.”
- Optimize dimensions and file size before committing.
- Do not rely on the image to communicate information absent from text.
- Omit the module when no visual adds real context.

## Validation

- [ ] The image renders from the target branch and in a fork.
- [ ] Alt text remains useful when the image is unavailable.
- [ ] The asset is legible in light and dark viewing contexts, or variants are provided.
- [ ] Raw HTML, if used, passes the repository's Markdown rules.

## Assembly note

Place this after the title and before badges. A later product demo belongs in the separate [visual demo module](../02-navigation-and-context/03-visual-demo.md).
