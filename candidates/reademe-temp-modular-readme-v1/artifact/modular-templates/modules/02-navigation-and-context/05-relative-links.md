# Module: Relative Links

| Field | Value |
| --- | --- |
| Output | A repository-wide linking pattern, not a section |
| Default placement | Applied wherever internal content is referenced |
| Applicability | Required pattern |
| Reader question | “Will this link keep working in a branch, tag, fork, clone, or mirror?” |

## Purpose

Keep repository-internal navigation bound to the current repository context. Relative paths follow the branch, tag, fork, and local checkout instead of redirecting readers to a hard-coded host or default branch.

## Inputs

- The target path relative to the root `README.md`.
- Optional heading anchor within the target document.
- Descriptive link text.

## Templates

```markdown
[Installation details](docs/installation.md)
[Configuration reference](docs/configuration.md#environment-variables)
[Contribution guide](CONTRIBUTING.md)
![Architecture diagram](docs/assets/architecture.svg)
[Usage in this README](#usage)
```

## Avoid for internal content

```markdown
[Contribution guide](https://github.com/{{OWNER}}/{{REPOSITORY}}/blob/main/CONTRIBUTING.md)
```

That absolute link can leave the reader's current branch, tag, fork, mirror, or offline checkout.

## Rules

- Resolve paths from the target root README.
- Preserve filename capitalization for case-sensitive environments.
- URL-encode spaces when filenames cannot be renamed, though simple filenames are preferable.
- Add anchors only after verifying the target renderer's slug behavior.
- Use absolute HTTPS URLs for genuinely external destinations.
- Prefer a repository file over an external duplicate when the repository file is canonical.

## Validation

- [ ] The link opens from the rendered root README.
- [ ] The same path exists on supported branches or tags.
- [ ] Anchor fragments reach the intended heading.
- [ ] Link text explains the destination.
- [ ] No internal link unnecessarily hard-codes an owner, branch, or host.

## Assembly note

Apply this pattern to every selected module. It has no heading and does not receive a table-of-contents entry.
