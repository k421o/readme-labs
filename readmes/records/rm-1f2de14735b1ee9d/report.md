---
schema: readme-artifact-report-v1
record_id: rm-1f2de14735b1ee9d
artifact_id: sha256:1f2de14735b1ee9d3a342fa7c5d5e87b95727276c0a56c8a9d77221f37880602
---

# README artifact `rm-1f2de14735b1ee9d`

This report is a generated projection over the canonical JSON record and attached evidence. It is not the README under review and does not carry a combined quality score.

## Artifact

| Field | Value |
| --- | --- |
| Subject | [external source](https://raw.githubusercontent.com/pallets/flask/d318b683471101618febed18996405ad26462110/README.md) |
| Content SHA-256 | `1f2de14735b1ee9d3a342fa7c5d5e87b95727276c0a56c8a9d77221f37880602` |
| Original name | `README.md` |
| Storage | `external_reference` |
| Capture boundary | `observed_source_snapshot` |
| Pre-capture editability | `not_applicable` |
| Ownership | `third_party` |
| Visibility | `public` |

## Provenance

| Event | Kind | Source | Producer |
| --- | --- | --- | --- |
| `prov-dd754af43416ac10` | `retrieved` | pallets/flask/d318b683471101618febed18996405ad26462110/README.md | — |

## Repository occurrences

| Occurrence | Repository | Revision/tree | Path | Role |
| --- | --- | --- | --- | --- |
| `occ-816fff1bb4d0defe` | pallets/flask | `d318b683471101618febed18996405ad26462110` | `README.md` | `framework_or_platform` |

## Collection memberships

| Collection | Purpose | Recorded at |
| --- | --- | --- |
| `pilot-high-exposure-v1` | `reference_sample` | 2026-08-30T02:10:00Z |

## Evidence

### `static_analysis` — `ev-3dcb3926080b584b`

0 diagnostics from markdown-structure-v1 using the all profile.

Result: `completed`. Subject scope: `artifact`. Sources: [static_analysis_run](../../../experiments/runs/pilot-high-exposure-markdown-structure-v1/run.json), [analyzer_spec](../../../experiments/analyzers/markdown-structure-v1/analyzer.json).

Profile: `all`. Enabled rules: `duplicate-heading-text`, `empty-heading`, `heading-level-jump`, `image-missing-alt`.

No enabled rule emitted a diagnostic. This is not a quality or merge verdict.

Limitations:

- The analyzer reads CommonMark tokens and does not reproduce every hosting platform's Markdown extensions.
- Diagnostics identify inspectable properties; they do not measure README usefulness, correctness, or fitness for a specific audience.
- Repository links, rendered HTML, and prose semantics are outside this first analyzer.
- Corpus diagnostics describe this pinned sample and do not estimate population prevalence or README quality.

### `structural_observation` — `ev-b6dc435cdbefd9d6`

53 lines, 241 words, 4 headings, and 5 links observed.

Result: `completed`. Subject scope: `occurrence`. Sources: [observation_collection](../../../corpus/observations/pilot-high-exposure-v1.jsonl).

| Metric | Value |
| --- | ---: |
| Lines | 53 |
| Words | 241 |
| Headings | 4 |
| Links | 5 |
| Code blocks | 2 |

Observed category signals: `development_participation`, `identity`. These are structural signals, not semantic-coverage or quality judgments.

Limitations:

- Category signals use exact normalized heading aliases and do not infer semantic coverage from prose.
- This structural observation is not a README quality score.

## Authority boundary

All attached automated and advisory results remain evidence only. Zero diagnostics is not approval, an evaluator recommendation is not a promotion decision, and this report does not determine experiment disposition.
