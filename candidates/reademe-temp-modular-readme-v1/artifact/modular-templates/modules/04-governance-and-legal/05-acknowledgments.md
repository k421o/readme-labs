# Module: Acknowledgments

| Field | Value |
| --- | --- |
| Output | Focused credit for people, projects, research, or sponsorship |
| Default placement | Immediately before license |
| Applicability | Optional |
| Reader question | “Whose work or support made this project possible?” |

## Purpose

Record meaningful credit without conflating active maintainership, dependency manifests, or the complete contributor history.

## Inputs

- People or teams whose specific contribution merits durable credit.
- Foundational projects, standards, research, datasets, or sponsors.
- Preferred public names and links.
- Any attribution language required by the underlying license or agreement.

## Template

```markdown
## Acknowledgments

- [{{NAME_OR_PROJECT}}]({{URL}}) — {{SPECIFIC_CONTRIBUTION_OR_INFLUENCE}}.
- [{{NAME_OR_PROJECT}}]({{URL}}) — {{SPECIFIC_CONTRIBUTION_OR_INFLUENCE}}.
```

## Rules

- Explain the basis for each acknowledgment.
- Use a contributor-history tool or `CONTRIBUTORS.md` for exhaustive lists.
- Keep active ownership in the maintainers module.
- Preserve legally required attribution exactly where its license requires it; this section may link to a dedicated notices file.
- Obtain consent before adding private individuals or personal links.
- Avoid promotional language unrelated to the project's creation.

## Validation

- [ ] Names, roles, and links are accurate.
- [ ] Required notices are not replaced by an informal thank-you.
- [ ] The list does not duplicate maintainers or package dependencies without reason.
- [ ] Credit language is specific and respectful.
- [ ] A generated contributor list, if linked, is current.

## Assembly note

Place acknowledgments near the end but before license. If no specific credit needs a README section, omit it.
