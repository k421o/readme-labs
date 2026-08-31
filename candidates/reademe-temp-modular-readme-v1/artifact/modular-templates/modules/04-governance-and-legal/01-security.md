# Module: Security

| Field | Value |
| --- | --- |
| Output | A private vulnerability-reporting route |
| Default placement | Near the start of the governance tail |
| Applicability | Recommended for public projects |
| Reader question | “How can I report a vulnerability without exposing it?” |

## Purpose

Direct security researchers and users away from public issues and toward the project's maintained disclosure policy.

## Inputs

- `{{SECURITY_POLICY_PATH}}`: usually `SECURITY.md`.
- `{{PRIVATE_REPORTING_CHANNEL}}`: private advisory form, monitored email, or security portal.
- Optional response expectations already defined in the policy.

## Template

```markdown
## Security

Please do not report vulnerabilities through public issues. Review the [security policy]({{SECURITY_POLICY_PATH}}) and submit the report through {{PRIVATE_REPORTING_CHANNEL}}.
```

## GitHub private-advisory variant

```markdown
## Security

Please do not report vulnerabilities through public issues. Review the [security policy](SECURITY.md), then [report a vulnerability privately](../../security/advisories/new).
```

Confirm that the relative advisory route works for the repository before using it; otherwise use the repository's full security URL.

## Rules

- Make the prohibition on public vulnerability reports explicit.
- Link to a policy that defines scope, supported versions, report contents, and response expectations.
- Publish only a channel that is actively monitored.
- Avoid promising a response or remediation timeline the maintainers cannot meet.
- Keep encryption keys or sensitive handling details in the security policy.
- Separate ordinary support and bug reports from vulnerabilities.

## Validation

- [ ] The private channel is reachable by the intended audience.
- [ ] The policy exists and identifies supported versions.
- [ ] Maintainers have tested receipt and triage.
- [ ] Public issue instructions do not conflict with this route.
- [ ] The wording does not expose private operational details.

## Assembly note

Place this after troubleshooting and before general contribution information. The README is a pointer; `SECURITY.md` is the canonical policy.
