# Module: License

| Field | Value |
| --- | --- |
| Output | A concise license declaration linked to the complete terms |
| Default placement | Final README section |
| Applicability | Required when the project is licensed for use or distribution |
| Reader question | “Under which terms may I use, modify, and distribute this?” |

## Purpose

State the actual license using its recognized identifier and route readers to the authoritative license text.

## Inputs

- `{{SPDX_IDENTIFIER}}`: exact identifier, such as `MIT` or `Apache-2.0`.
- `{{LICENSE_NAME}}`: human-readable name.
- `{{LICENSE_PATH}}`: usually `LICENSE` or `LICENSE.md`.
- Any notices or multi-license selection rules.

## Template

```markdown
## License

Licensed under the [{{LICENSE_NAME}}]({{LICENSE_PATH}}) (`{{SPDX_IDENTIFIER}}`).
```

## Multi-license variant

Use legal language already approved for the project:

```markdown
## License

This project is available under either the [{{LICENSE_A_NAME}}]({{LICENSE_A_PATH}}) (`{{LICENSE_A_SPDX}}`) or the [{{LICENSE_B_NAME}}]({{LICENSE_B_PATH}}) (`{{LICENSE_B_SPDX}}`), at your option. See [NOTICE]({{NOTICE_PATH}}) for required attributions.
```

## Rules

- Copy the identifier and license choice from the repository's authoritative legal files.
- Do not infer a license from a badge, package manifest, or dependency licenses.
- Use a relative link to the complete terms.
- Include notice or exception links when legally applicable.
- Do not paraphrase license permissions or offer legal interpretation in the README.
- Keep this as the final section in the assembled README, following the recovered standard-readme guidance.

## Validation

- [ ] The license file exists and contains the intended full text.
- [ ] The SPDX identifier is exact, including `-only`, `-or-later`, or exception syntax when applicable.
- [ ] Repository, package, and badge metadata agree.
- [ ] Required notices and attribution files are linked.
- [ ] No README section follows license.

## Assembly note

This module terminates the README. Legal choices must be confirmed by the project owner or qualified counsel; the template only documents the selected terms.
