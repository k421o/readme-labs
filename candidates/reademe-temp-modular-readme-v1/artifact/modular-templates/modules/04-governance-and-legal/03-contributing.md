# Module: Contributing

| Field | Value |
| --- | --- |
| Output | A concise invitation and route to contribution requirements |
| Default placement | In the governance tail |
| Applicability | Recommended for collaborative projects |
| Reader question | “Are contributions welcome, and how do I prepare one that can be accepted?” |

## Purpose

Set expectations without duplicating the full development workflow. Route contributors to the canonical guide, issue process, tests, and conduct policy.

## Inputs

- `{{CONTRIBUTING_PATH}}`: canonical contribution guide.
- `{{ISSUE_PATH}}`: issue templates, discussion area, or planning process.
- `{{TEST_COMMAND}}`: exact local verification command.
- Any sign-off, CLA, DCO, or review requirement defined in the guide.

## Template

````markdown
## Contributing

Contributions are welcome. Read [the contribution guide]({{CONTRIBUTING_PATH}}) before opening a pull request, and use {{ISSUE_PATH}} to discuss substantial changes first.

Run the required local checks before submitting:

```bash
{{TEST_COMMAND}}
```

Participation is governed by the [code of conduct]({{CODE_OF_CONDUCT_PATH}}).
````

Delete the final sentence when no code-of-conduct file applies.

## Rules

- State plainly whether external contributions are accepted.
- Keep environment setup, branch policy, commit rules, and review detail in `CONTRIBUTING.md`.
- Surface the one verification command every contributor must run.
- Disclose sign-off or agreement requirements before someone invests in a change.
- Route first-time or substantial proposals to the project's actual planning channel.
- Do not promise acceptance; explain the process.

## Validation

- [ ] The contribution guide exists and matches current development setup.
- [ ] The test command works from the documented directory.
- [ ] Issue, discussion, and conduct links resolve.
- [ ] Required legal or sign-off steps are discoverable.
- [ ] The invitation matches the project's actual contribution policy.

## Assembly note

Use the [code-of-conduct module](04-code-of-conduct.md) as a separate section only when more visibility is needed; otherwise the single link here is sufficient.
