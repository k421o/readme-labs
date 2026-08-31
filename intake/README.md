# Evidence intake

Intake records outside README work without making it canonical. An intake may
reference or snapshot README files, repositories, articles, research results,
research methods, evaluation machinery, skills, bundles, agent responses, or
user-response evidence.

Each manifest separates:

- the source repository or publication identity;
- the exact revision, path, object identity, and content digest when available;
- the role an item may play in the domain;
- whether its bytes are referenced or preserved as a checked-in snapshot; and
- limitations such as local-only provenance, licensing, missing source bodies,
  or uncommitted workspace state.

Admission means “available for inquiry.” It does not mean correct, preferred,
compatible, or authoritative.

Checked-in snapshots live under `snapshots/`. Large, restricted, or
third-party bodies should remain in external storage with immutable references
and permitted derived observations in Git.
