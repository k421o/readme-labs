# README review interface, version 1

## Named user job

Given a repository checkout and one or more README files in scope, identify
only reader-facing problems that can materially change understanding, correct
use, navigation, or contribution. Support each finding with repository
evidence, or return an explicit no-material-findings conclusion with residual
verification limits.

## Inputs

- A repository checkout containing the README and relevant local evidence.
- A review request; scope defaults to the repository's primary README when the
  request does not name files.
- Optional authority to execute bounded verification commands.

## Output contract

- Establish the README's evidenced role before applying role-specific needs.
- Return ranked material findings with tight locations, repository evidence,
  reader impact, and the smallest correction direction.
- When there are no material findings, say so and report unverified commands,
  links, rendered surfaces, and role assumptions.
- Separate verified facts from semantic judgments.
- Tie every command-execution claim to the current task's actual tool record.

The evaluation runner uses `evals/review-response-v1.schema.json` as a
machine-checkable projection of this contract. That schema is an evaluation
adapter; this document and `SKILL.md` own the human-facing interface.

## Exclusions

This interface does not promise a generic documentation audit, a complete
README rewrite, a universal section template, package publication checks
without evidence, or automatic quality scoring from structural observations.

## Compatibility

Version 1 freezes the named job and finding/no-finding behavior for the first
factory release. Wording and internal workflow may improve without an
interface-version change when those two observable behaviors remain compatible.
