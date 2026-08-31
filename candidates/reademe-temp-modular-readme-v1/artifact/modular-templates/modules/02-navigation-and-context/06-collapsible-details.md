# Module: Collapsible Details

| Field | Value |
| --- | --- |
| Output | A disclosure widget for secondary detail |
| Default placement | Inside the section whose detail it extends |
| Applicability | Optional pattern |
| Reader question | “Can I inspect the full detail without making the main path harder to scan?” |

## Purpose

Apply progressive disclosure to long schemas, logs, platform variants, or exhaustive examples. The summary must tell readers exactly what is hidden.

## Inputs

- `{{SUMMARY_LABEL}}`: a specific action-oriented label.
- `{{DETAIL_CONTENT}}`: supporting information that is useful but not essential to the primary path.

## Template

````markdown
<details>
<summary>{{SUMMARY_LABEL}}</summary>

{{DETAIL_CONTENT}}

</details>
````

## Configuration example

````markdown
<details>
<summary>View the complete JSON configuration</summary>

```json
{
  "retries": 5,
  "logging": "verbose"
}
```

</details>
````

## Rules

- Keep the primary happy path outside the disclosure.
- Use a summary label such as “View Windows setup” rather than “More.”
- Preserve blank lines around Markdown nested inside HTML tags.
- Do not hide safety warnings, prerequisites, or the only usable example.
- Use dedicated documentation instead when the hidden block remains very long or needs its own navigation.
- Confirm that the target renderer supports `<details>` and `<summary>`.

## Validation

- [ ] The widget expands and collapses in the target renderer.
- [ ] Nested Markdown and code fences render correctly.
- [ ] The summary accurately describes the hidden content.
- [ ] The README remains useful without opening the block.
- [ ] The detail is maintained with the surrounding section.

## Assembly note

This is a pattern, not a standalone README section. Apply it within configuration, troubleshooting, API, or platform-specific setup modules as needed.
