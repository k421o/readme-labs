# Bootstrap role annotation, version 1

This protocol records the provenance of the role labels in the
`pilot-high-exposure-v1` manifest. It does not claim that the labels were
declared by the source repositories.

## Procedure

The bootstrap corpus author assigned one primary role to each pinned README
after inspecting the document path and the repository's apparent distribution
model. The vocabulary comes from `domain/readme-role-v1.json`.

The original labels are preserved as historical annotations. They were not
produced by multiple independent annotators, no agreement statistic was
calculated, and no adjudication record exists. They therefore support
descriptive grouping in this pilot only; they are not ground truth for model
evaluation or population inference.

Every manifest item records:

- `protocol`: `bootstrap-role-annotation`
- `protocol_version`: `1.0.0`
- `annotator`: `bootstrap-corpus-author`

Future annotation rounds must use a prospective protocol, blinded labels where
appropriate, independent annotators, and an explicit adjudication record.
