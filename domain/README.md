# Domain contracts

This directory contains the versioned interchange contracts at the center of
`readme-labs`.

- [`repository-roles.md`](repository-roles.md) defines the context that must be
  established before judging a README.
- [`taxonomy-v1.json`](taxonomy-v1.json) defines stable jobs, information
  categories, conventional headings, and applicability hints.
- [`readme-observation-v1.schema.json`](readme-observation-v1.schema.json)
  defines the structural record passed between collection, annotation,
  analysis, evaluation, and capability code.

The taxonomy is descriptive, not a required template. A category can be
inapplicable, locally present, or deliberately routed to another canonical
surface. `READMEObservation` records what was found and how; it does not emit a
quality score.

Breaking changes receive a new major-version file. Additive changes may update
the `version` field when existing observations retain their meaning.
