# Template Conventions

Use these rules across every module so fragments can be combined without cleanup surprises.

## Placeholder syntax

Replace tokens written as `{{UPPER_SNAKE_CASE}}`.

| Token shape | Meaning | Example replacement |
| --- | --- | --- |
| `{{PROJECT_NAME}}` | Human-facing display name | `FastData Engine` |
| `{{REPOSITORY}}` | Repository slug | `fastdata-engine` |
| `{{OWNER}}` | GitHub user or organization | `example-org` |
| `{{COMMAND}}` | Exact executable command | `fastdata run` |
| `{{RELATIVE_PATH}}` | Path from the repository-root README | `docs/setup.md` |

Placeholder text is an authoring aid, not valid final content. A completed README contains no `{{...}}` tokens.

## Optional blocks

Instructions inside Markdown comments are for the template author and should be deleted with any unused block:

```markdown
<!-- Optional: keep this sentence only when the project has hosted documentation. -->
```

Do not ship instructional comments unless they provide ongoing maintenance value.

## Heading contract

- The project-title module owns the only `H1` (`#`) in the assembled README.
- Standalone section modules default to `H2` (`##`).
- A fragment nested inside another section may be demoted one level, but heading levels must not skip.
- Keep the license section last when it is present.
- Pattern modules such as relative links and collapsible details do not create required sections.

## Link contract

- Interpret relative paths from the target repository's root `README.md`, not from this template kit.
- Prefer relative links for files stored in the same repository.
- Use absolute HTTPS links for external sites and hosted services.
- Link text should describe the destination; avoid bare URLs and “click here.”
- Test anchors in the renderer that will publish the README.

## Code and command contract

- Use a language identifier on every fenced code block, such as `bash`, `python`, `json`, or `yaml`.
- Commands must be copy-pasteable from the directory stated in the surrounding text.
- Keep prompts such as `$` out of command blocks so readers can copy them.
- Prefer a minimal verified path over a list of speculative alternatives.
- Include expected output only when it helps the reader recognize success.

## Content contract

Each selected module should answer one reader question and earn its place in the README. Delegate exhaustive material to a repository document or docs site, then link to it with a concise summary.

Module labels have these meanings:

- **Required**: the kit expects the element in every profile where its condition applies.
- **Recommended**: normally valuable, but project context can justify omission.
- **Conditional**: include only when the project exposes the corresponding capability or constraint.
- **Optional**: include when it materially improves understanding.

## Module document contract

Every atomic guide contains:

1. a module card describing placement and applicability;
2. a purpose statement;
3. required author inputs;
4. one copy-ready template;
5. focused rules and variants;
6. a validation checklist;
7. an assembly note.

Use [checklists/module-authoring.md](checklists/module-authoring.md) when adding another module to this kit.
