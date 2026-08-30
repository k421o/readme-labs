# Review: checker orientation page

Contract evidence: `docs/architecture.md` says checkers own their optional
dependencies and do not own writing policy. The linked checker READMEs define
different commands, runtimes, and output contracts. This document is an index
for choosing a measurement tool, not a shared API specification.

Changes made:

- Removed the invented, generic JSON example. The actual adapters have
  different schemas, so a shared sample carries unsupported authority.
- Replaced the flat tool list with a decision table that points to each
  tool’s maintained contract.
- Separated the `human-voice` skill from the checker runtimes, matching its
  actual packaging location.
- Made the non-authorship boundary a concise, shared interpretation limit
  instead of repeating each tool’s deeper caveats.
