# Module: Repository-Slug Alias

| Field | Value |
| --- | --- |
| Output | Optional parenthesized alias inside the `H1` |
| Default placement | Appended to the project title |
| Applicability | Only when display name and repository slug differ |
| Reader question | “How does this project name map to the repository or package?” |

## Purpose

Reconcile a branded display name with the technical name readers see in clone URLs, package managers, CI logs, or local directories.

## Inputs

- `{{PROJECT_NAME}}`: human-facing display name.
- `{{REPOSITORY_SLUG}}`: exact repository or package slug.

## Template

```markdown
# {{PROJECT_NAME}} _({{REPOSITORY_SLUG}})_
```

## Use this module when

- branding adds spaces or punctuation absent from the slug;
- the package name differs from the product name;
- readers must search for or install the project under another identifier.

Do not add an alias merely to repeat the same name in lowercase.

## Validation

- [ ] The alias exactly matches the technical identifier it represents.
- [ ] The relationship is useful rather than decorative.
- [ ] The README still contains only one `H1`.
- [ ] Install and clone examples use the same slug.

## Assembly note

Replace the plain title fragment from [Project title](01-project-title-h1.md) with this variant. Never include both versions.
