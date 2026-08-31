# Component work packet: Usage / quickstart

You own the `usage-quickstart` README component. Work independently and do not delegate further.

## Read

- Shared decisions: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/.agents/skills/modular-readme/work/forward-test/shared-context.md`
- Component contract: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/.agents/skills/modular-readme/references/component-contract.md`
- Template conventions: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/modular-templates/CONVENTIONS.md`
- `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/modular-templates/modules/03-operational-walkthroughs/04-usage-quickstart.md`
- `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/modular-templates/modules/02-navigation-and-context/05-relative-links.md`

Inspect `/Users/karltonsuits/Documents/ChatGPT/reademe-temp` only for evidence relevant to this component. Follow any applicable repository instructions.

## Write boundary

Write only these two files:

- Markdown fragment: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/.agents/skills/modular-readme/work/forward-test/components/usage-quickstart.md`
- Evidence report: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp/.agents/skills/modular-readme/work/forward-test/reports/usage-quickstart.json`

Do not edit the target README, manifest, shared context, another component, or another report. If another component appears inconsistent, record a note for the parent instead of editing it.

## Fragment requirements

- Start with one H2 (`## `). Subheadings may use H3 or deeper without skipping levels.
- Emit final README Markdown only, without an outer fence or authoring commentary.
- Remove template placeholders and optional-branch instructions.
- Include only claims, commands, paths, contacts, and legal statements supported by repository evidence.
- Keep the fragment independently understandable and avoid positional language such as "above" or "below".

## Evidence report

Use this JSON shape, replacing the example values:

```json
{
  "component_id": "usage-quickstart",
  "status": "ready",
  "source_files": [
    "path/relative/to/target-repository"
  ],
  "verified": [
    "A concise statement of what repository evidence established."
  ],
  "unverified": [],
  "notes": "Optional integration note for the parent."
}
```

Use repository-relative paths in `source_files`. If a required fact cannot be verified, set `status` to `blocked`, describe it in `unverified`, and tell the parent; do not fill the gap by inference.
