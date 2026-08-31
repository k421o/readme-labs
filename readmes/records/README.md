# Recorded README artifacts

This directory contains content-addressed document packages rather than active
repository READMEs. The package name is derived from the full artifact digest;
the complete digest remains in `record.json`.

The first two records deliberately exercise different provenance and custody
paths:

- [`rm-f96b8e9d6c94dee9`](rm-f96b8e9d6c94dee9/report.md) embeds a generated,
  owned README after its authoring run completed. Its document-centered evidence
  joins a structural observation, static diagnostics, and a repository-contextual
  soft maintainer review.
- [`rm-1f2de14735b1ee9d`](rm-1f2de14735b1ee9d/report.md) references the pinned
  public Flask README without committing the third-party body. It joins the
  existing corpus observation and corpus-calibration static result.

The contrast is intentional: both are Markdown artifacts that can use common
analysis machinery, while their origin, purpose, repository context, custody,
and available evidence remain independently represented.
