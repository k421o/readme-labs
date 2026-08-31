# Markdown-structure corpus characterization

This run applies every `markdown-structure-v1` rule to the 16 pinned documents
in the high-exposure pilot corpus. It is measurement-method calibration, not a
ranking of the repositories or a claim about README quality.

The analyzer emitted 17 diagnostics: seven heading-level jumps and ten repeated
normalized heading labels. Ten repeated-label notices were concentrated in the
Axios API-reference README, where similar headings are plausibly an intentional
reference structure. That concentration is the reason the repeated-heading rule
remains available in the `all` profile but is excluded from default author
feedback.

No empty-heading or missing-alt diagnostic occurred in this small sample. That
absence does not validate or invalidate those rules; deterministic fixtures
exercise their behavior. The sample is purposive and too small for population
prevalence estimates.

[`run.json`](run.json) preserves every subject revision, path, content digest,
localized diagnostic, enabled rule, analyzer-spec digest, and limitation. Raw
third-party README bodies remain in the untracked corpus cache.
