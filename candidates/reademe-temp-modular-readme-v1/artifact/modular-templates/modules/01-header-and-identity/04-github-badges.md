# Module: GitHub and Status Badges

| Field | Value |
| --- | --- |
| Output | A small stack of linked status badges |
| Default placement | Below the title or banner |
| Applicability | Optional |
| Reader question | “Is this project healthy, current, and licensed?” |

## Terminology

This module covers visible status **badges**. It does not create Git tags. Git tags are version-control references; the release badge below can surface a release derived from them.

## Purpose

Surface a small set of trustworthy project-health signals and link readers to the underlying evidence behind each status.

## Inputs

- `{{OWNER}}`: GitHub user or organization.
- `{{REPOSITORY}}`: repository slug.
- `{{WORKFLOW_FILE}}`: workflow filename under `.github/workflows/`.
- `{{DEFAULT_BRANCH}}`: normally `main` or `master`.
- `{{COVERAGE_URL}}`: the project's coverage dashboard, if any.

## Template

Keep only badges backed by a real source of truth:

```markdown
[![CI](https://github.com/{{OWNER}}/{{REPOSITORY}}/actions/workflows/{{WORKFLOW_FILE}}/badge.svg?branch={{DEFAULT_BRANCH}})](https://github.com/{{OWNER}}/{{REPOSITORY}}/actions/workflows/{{WORKFLOW_FILE}})
[![Coverage](https://img.shields.io/codecov/c/github/{{OWNER}}/{{REPOSITORY}})]({{COVERAGE_URL}})
[![Release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPOSITORY}})](https://github.com/{{OWNER}}/{{REPOSITORY}}/releases/latest)
[![License](https://img.shields.io/github/license/{{OWNER}}/{{REPOSITORY}})](LICENSE)
```

## Selection rules

- Prefer three to five high-value indicators.
- Common choices are CI, coverage, release/version, package registry, and license.
- Link each badge to the underlying report or workflow, not merely the badge image.
- Put one badge per source line to keep diffs maintainable.
- Do not display vanity metrics that do not help readers assess compatibility or health.
- Remove a badge when its backing integration is no longer maintained.

## Validation

- [ ] Every badge image resolves without authentication for the intended audience.
- [ ] Every badge link opens the corresponding status detail.
- [ ] Workflow filename and default branch are exact.
- [ ] The license badge matches the actual `LICENSE` file.
- [ ] The stack remains readable and is not noisy.

## Assembly note

Place badges after the banner, or immediately after the title when no banner exists. The full license declaration still belongs in the final [license module](../04-governance-and-legal/06-license.md).
