# Module: Troubleshooting

| Field | Value |
| --- | --- |
| Output | A short set of high-frequency recovery paths |
| Default placement | After operational reference material |
| Applicability | Optional |
| Reader question | “What should I check when the documented path fails?” |

## Purpose

Resolve the few failures most likely to block first success, then route uncommon or environment-specific problems to maintained support material.

## Inputs

- Two to five observed high-frequency symptoms.
- A diagnostic command or check for each symptom.
- A safe corrective action.
- Support, issue, or full troubleshooting destination.

## Template

````markdown
## Troubleshooting

| Symptom | Check | Resolution |
| --- | --- | --- |
| {{OBSERVED_SYMPTOM}} | `{{DIAGNOSTIC_COMMAND}}` | {{SAFE_RESOLUTION}} |
| {{OBSERVED_SYMPTOM}} | {{DIAGNOSTIC_CHECK}} | {{SAFE_RESOLUTION}} |

If the problem persists, search [known issues]({{KNOWN_ISSUES_PATH}}) and open a report using the repository's issue template. Include the project version, platform, the smallest reproduction, and sanitized diagnostic output.
````

## Rules

- Describe symptoms in the words users will search for.
- Prefer diagnostic checks before destructive recovery commands.
- Never ask users to publish tokens, credentials, or private logs.
- Keep rare edge cases in a dedicated troubleshooting guide or issue tracker.
- Distinguish support questions from private vulnerability reports.
- Remove resolved entries when the underlying failure can no longer occur.

## Validation

- [ ] Every resolution is safe and current.
- [ ] Commands avoid data loss and disclose relevant side effects.
- [ ] Diagnostic output can be sanitized before sharing.
- [ ] Known-issues and reporting links resolve.
- [ ] Security-sensitive reports route through the security policy instead of public issues.

## Assembly note

Keep this after the normal operational path so failures do not interrupt successful readers. Link to the [security module](../04-governance-and-legal/01-security.md) for private disclosure routing.
