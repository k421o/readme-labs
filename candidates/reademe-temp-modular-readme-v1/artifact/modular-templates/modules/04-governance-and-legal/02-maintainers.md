# Module: Maintainers

| Field | Value |
| --- | --- |
| Output | A current ownership and contact map |
| Default placement | After security |
| Applicability | Optional |
| Reader question | “Who is responsible for this project?” |

## Purpose

Make active stewardship visible without turning the README into an organizational directory. Identify roles readers need for contribution, escalation, or continuity.

## Inputs

- Current maintainer display names or team names.
- Public GitHub handles or durable team links.
- Relevant roles or areas of responsibility.
- Optional canonical ownership file such as `CODEOWNERS` or a governance guide.

## Template

```markdown
## Maintainers

- **{{MAINTAINER_OR_TEAM}}** ([@{{GITHUB_HANDLE}}](https://github.com/{{GITHUB_HANDLE}})) — {{RESPONSIBILITY}}
- **{{MAINTAINER_OR_TEAM}}** ([@{{GITHUB_HANDLE}}](https://github.com/{{GITHUB_HANDLE}})) — {{RESPONSIBILITY}}

Ownership and escalation details are maintained in [the governance guide]({{GOVERNANCE_PATH}}).
```

## Rules

- List active maintainers or durable teams, not every past contributor.
- Use public professional contact points rather than private personal information.
- Keep role labels short and current.
- Prefer a team or governance link when individual churn is high.
- Use the acknowledgments module for historical credit.
- Do not imply support guarantees from a name alone.

## Validation

- [ ] Every listed person or team is currently active in the stated role.
- [ ] Handles and team links resolve.
- [ ] Public contact information is included with consent.
- [ ] Ownership agrees with repository governance and `CODEOWNERS`.
- [ ] Former maintainers are moved to acknowledgments when appropriate.

## Assembly note

Omit this module when governance is already clear and a duplicate list would drift. It precedes contributing so readers know who stewards the process.
