# Module: Short Description

| Field | Value |
| --- | --- |
| Output | One high-density sentence or short paragraph |
| Default placement | Immediately below badges or the title visual |
| Applicability | Required |
| Reader question | “What does this do, for whom, and why should I care?” |

## Purpose

Give a scanning reader enough information to decide whether to continue. This text should align with repository and package metadata so search results, manifests, and the README describe the same product.

## Inputs

- `{{PROJECT_CATEGORY}}`: what the project is.
- `{{TARGET_USER}}`: who uses it.
- `{{PRIMARY_JOB}}`: the job it performs.
- `{{DISTINGUISHING_VALUE}}`: its most important benefit or constraint.

## Template

```markdown
{{PROJECT_CATEGORY}} for {{TARGET_USER}} that {{PRIMARY_JOB}}, with {{DISTINGUISHING_VALUE}}.
```

## Example shape

```markdown
A streaming data library for Python teams that validates event pipelines locally, with the same configuration used in production.
```

## Rules

- Lead with the project category and primary job, not company history.
- Name the audience only when it sharpens the value proposition.
- Prefer one sentence; the gathered header guide uses 120 characters as an ideal search-oriented target, not an absolute platform limit.
- Avoid “simple,” “easy,” “powerful,” and “best” unless the sentence provides evidence.
- Align the claim with `package.json`, `pyproject.toml`, `Cargo.toml`, repository description, or equivalent metadata.

## Validation

- [ ] A new reader can paraphrase what the project does.
- [ ] The sentence identifies concrete value rather than generic quality.
- [ ] Metadata surfaces do not contradict it.
- [ ] No setup detail or deep implementation explanation has leaked into it.

## Assembly note

This is the minimum prose beneath the identity block. Follow it with the optional long description or move directly to navigation and operational content.
