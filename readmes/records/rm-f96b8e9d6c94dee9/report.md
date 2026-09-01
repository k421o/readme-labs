---
schema: readme-artifact-report-v1
record_id: rm-f96b8e9d6c94dee9
artifact_id: sha256:f96b8e9d6c94dee97c7c65c011d29d686be88e1edcfc7a588262d5db795720a0
---

# README artifact `rm-f96b8e9d6c94dee9`

This report is a generated projection over the canonical JSON record and attached evidence. It is not the README under review and does not carry a combined quality score.

## Artifact

| Field | Value |
| --- | --- |
| Subject | [`artifact.md`](artifact.md) |
| Content SHA-256 | `f96b8e9d6c94dee97c7c65c011d29d686be88e1edcfc7a588262d5db795720a0` |
| Original name | `README.md` |
| Storage | `embedded` |
| Capture boundary | `completed_generation` |
| Pre-capture editability | `mutable` |
| Ownership | `owned` |
| Visibility | `local_only` |

## Provenance

| Event | Kind | Source | Producer |
| --- | --- | --- | --- |
| `prov-73f766b72adbae0a` | `generated` | k421o/readme-labs/b10ff9c1ad032c6861b7d03463f52d9ac5d8e208/intake/snapshots/reademe-temp-forward-test/forward-test/assembled/README.md | candidate:reademe-temp-modular-readme-v1 |
| `prov-c252498fd71bb9a8` | `ingested` | local:reademe-temp/workspace@2026-08-30T22:02:58Z/.agents/skills/modular-readme/work/forward-test/assembled/README.md | — |

## Repository occurrences

| Occurrence | Repository | Revision/tree | Path | Role |
| --- | --- | --- | --- | --- |
| `occ-32fff3ea0f76b14f` | local:reademe-temp-evaluation | `e59a6bbb67f7e6d2f6182bed8c627f6ac9dcdb38 / c434456d4b0026722ea72fdcbfc55e3dafaa84b6` | `README.md` | `repository_root` |
| `occ-3bb7dbd8e9470ae5` | k421o/readme-labs | `b10ff9c1ad032c6861b7d03463f52d9ac5d8e208` | `intake/snapshots/reademe-temp-forward-test/forward-test/assembled/README.md` | `experiment` |
| `occ-57d63ad408b7be4c` | local:reademe-temp | `workspace@2026-08-30T22:02:58Z` | `.agents/skills/modular-readme/work/forward-test/assembled/README.md` | `experiment` |

## Collection memberships

| Collection | Purpose | Recorded at |
| --- | --- | --- |
| `reademe-temp-forward-test` | `generated_output` | 2026-08-31T04:08:31Z |
| `reademe-temp-modular-readme-v1` | `candidate_output` | 2026-08-31T04:08:31Z |
| `reademe-temp-static-diagnostics-v1` | `experiment_subject` | 2026-08-31T04:08:31Z |

## Evidence

### `soft_agent_review` — `ev-a2a9d3da5b659c58`

Request changes. The concise command is accurate and the linked generated outputs exist, but this README replacement removes the repository’s essential scope, provenance, privacy, and navigation information. That is too much loss of maintainer-facing context for a mature Linux-focused open-source project.

Result: `completed`. Subject scope: `occurrence`. Sources: [review_run](../../../experiments/runs/reademe-temp-forward-test-linux-maintainer-v1/run.json), [evaluator_spec](../../../experiments/evaluators/popular-linux-open-source-maintainer-v1/evaluator.json), [evaluator_instructions](../../../experiments/evaluators/popular-linux-open-source-maintainer-v1/instructions.md), [evaluator_response_schema](../../../experiments/schemas/soft-agent-review-response-v1.schema.json), [execution_response_schema](../../../experiments/runs/reademe-temp-forward-test-linux-maintainer-v1/response.schema.json), [events](../../../experiments/runs/reademe-temp-forward-test-linux-maintainer-v1/events.jsonl), [response](../../../experiments/runs/reademe-temp-forward-test-linux-maintainer-v1/response.json), [stderr](../../../experiments/runs/reademe-temp-forward-test-linux-maintainer-v1/stderr.log).

Recommendation: `request_changes` with `high` confidence. This recommendation is advisory.

Request changes. The concise command is accurate and the linked generated outputs exist, but this README replacement removes the repository’s essential scope, provenance, privacy, and navigation information. That is too much loss of maintainer-facing context for a mature Linux-focused open-source project.

Strengths:

- The documented extraction command matches the executable interface.
- The README’s internal links point to present repository files.

Concerns:

- **The replacement removes essential project context and documentation navigation** (`blocking`): A root README in a long-lived project should preserve the basic map of what is in the repository and the operational/privacy constraints of its primary artifact. The new opening sentence says Studio metadata is documented, yet offers no route to that documentation. This is a substantive regression in discoverability and provenance, not a preference for a longer README. Suggested change: Keep the concise usage section, but restore a short repository overview and links to the overview/recovery limits, Studio inventory, related recovered documents, and template system. State clearly that the original saved HTML is intentionally untracked because it may contain private account/application data.
- **Linux support and dependency setup are underspecified** (`blocking`): For maintainers and users on Linux, the advertised command should have an actionable dependency path and a crisp statement of what succeeds without macOS-specific metadata. Otherwise a first run can fail before extraction due to a missing dependency, and users cannot tell whether incomplete URL recovery is expected. Suggested change: Add a supported way to obtain `lxml` (or link to the project’s dependency manifest if one is added) and state that source/chat extraction works from the saved HTML, while original-URL recovery is an optional macOS-only capability requiring the companion directory and its extended attributes.

Limitations:

- This is a simulated maintainer review based only on the checked-out repository and its Git history; no upstream issue, release policy, CI configuration, or real Linux user environment was available.
- The original saved NotebookLM HTML and macOS companion directory are intentionally absent, so end-to-end extraction and URL-recovery behavior could not be verified.
- No claim is made about whether the removed documentation was intentionally relocated outside this repository.

### `static_analysis` — `ev-b040e654700f9a52`

0 diagnostics from markdown-structure-v1 using the feedback profile.

Result: `completed`. Subject scope: `artifact`. Sources: [static_analysis_run](../../../experiments/runs/reademe-temp-forward-test-markdown-structure-v1/run.json), [analyzer_spec](../../../experiments/analyzers/markdown-structure-v1/analyzer.json).

Profile: `feedback`. Enabled rules: `empty-heading`, `heading-level-jump`, `image-missing-alt`.

No enabled rule emitted a diagnostic. This is not a quality or merge verdict.

Skipped rules: `duplicate-heading-text` (excluded_from_selected_profile).

Limitations:

- The analyzer reads CommonMark tokens and does not reproduce every hosting platform's Markdown extensions.
- Diagnostics identify inspectable properties; they do not measure README usefulness, correctness, or fitness for a specific audience.
- Repository links, rendered HTML, and prose semantics are outside this first analyzer.

### `structural_observation` — `ev-c25c6fd296560bab`

15 lines, 96 words, 2 headings, and 2 links observed.

Result: `completed`. Subject scope: `occurrence`. Sources: [artifact](artifact.md).

| Metric | Value |
| --- | ---: |
| Lines | 15 |
| Words | 96 |
| Headings | 2 |
| Links | 2 |
| Code blocks | 1 |

Observed category signals: `identity`, `minimal_use`. These are structural signals, not semantic-coverage or quality judgments.

Limitations:

- Category signals use exact normalized heading aliases and do not infer semantic coverage from prose.
- This structural observation is not a README quality score.

## Authority boundary

All attached automated and advisory results remain evidence only. Zero diagnostics is not approval, an evaluator recommendation is not a promotion decision, and this report does not determine experiment disposition.
