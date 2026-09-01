---
name: readme-prune
description: Prune an existing repository README by removing explicitly unwanted or repository-evidenced unsupported, stale, duplicative, or noisy content while preserving its evidenced reader contract. Use when asked to trim, declutter, shorten by subtraction, or remove specific README content. Use readme-review for findings without edits and readme-generate to create or replace a README. Do not use for a broad rewrite or to delete or move the README itself.
---

# README pruning

Remove the smallest authorized set of content from an existing README while
preserving the reader-facing contract that the repository supports. Brevity is
not the objective; evidenced subtraction is.

## Required review source

Before pruning, read the sibling [README review
skill](../readme-review/SKILL.md) completely and read every local reference
file shipped in [its references directory](../readme-review/references/). The
review skill and those references are the single source of role, evidence,
analysis, and finding behavior. Do not restate or fork their criteria here.

## Pruning modes

Establish which mode the request authorizes before editing:

- **Directed removal:** The user identifies exact content or a bounded category
  to remove. Treat that directive as the basis for its absence; do not invent a
  repository defect to justify it or silently restore it later. Review the
  resulting README and report any material reader regression caused by the
  requested removal.
- **Evidence-selected pruning:** The user asks for open-ended trimming,
  decluttering, shortening, or cleanup. Remove a complete unit only when the
  canonical review workflow and repository evidence establish that it is
  unsupported, stale, duplicative, or noisy and its absence does not impair the
  README's evidenced job.

A word, line, or section target does not make correct reader-critical signal
removable. When open-ended review finds no supported removal, leave the README
unchanged and say so.

## Scope boundary

- Resolve an existing target README and read the nearest applicable repository
  guidance before changing it. Preserve pre-existing changes and project voice.
- Use `readme-review` for findings without edits. Use `readme-generate` for a
  missing README, an explicit replacement, or a broad rewrite whose intended
  result is not semantically subtractive.
- Do not delete or move the README, relocate its content into another file,
  migrate a package or registry interface, or edit neighboring documents. Those
  operations require separately authorized scope.
- Make no new substantive claims, sections, commands, or links. Only local
  Markdown, grammar, heading, list, or link-reference repairs made necessary by
  a deletion are in scope.
- Do not capture the mutable result as a README artifact or assign lineage.
  Artifact capture remains a separate owner-selected boundary.

## Pruning workflow

1. Inspect the target README and enough repository evidence to establish its
   role, delivery surfaces, shortest useful reader path, and consequential
   boundaries. Apply the complete sibling `readme-review` workflow to the
   initial bytes. For directed removal, keep unrelated findings separate from
   the user's basis for subtraction.
2. Identify complete candidate units and classify each basis as
   `user_directed` or `review_evidenced`. For evidence-selected candidates,
   record the supporting repository evidence and the reader question that will
   remain answered after removal.
3. Protect correct component identity, project-specific facts, the shortest
   supported path to a useful result, necessary compatibility or security
   boundaries, canonical routes, fixture or experiment context, and content
   consumed by an evidenced delivery surface. Check links, Markdown reference
   definitions, heading fragments, and surrounding grammar that cross each
   proposed deletion boundary.
4. Apply only the smallest supported deletions. Remove dependent table-of-
   contents entries, orphaned reference definitions, empty headings, or local
   connective text only when the primary deletion makes them invalid. Do not
   replace removed prose with a generic summary or use pruning as a rewrite.
5. Apply the complete sibling `readme-review` workflow to the exact edited
   bytes. Compare the result with the initial reader contract, not with a
   universal template or a length target.
6. Restore any agent-selected deletion that creates a material reader-facing
   regression. Do not silently reverse a directed removal; keep it removed and
   report the attributable regression or external migration need as a residual
   limit. Do not repair unrelated pre-existing gaps by adding content.
7. Repeat only while another supported candidate remains and the latest full
   review shows no material regression attributable to agent-selected pruning.
   Stop on a clean attributable result or an explicit residual limit.
8. Validate changed relative links and consequential commands in proportion to
   risk. In the final response, name the target, each material unit removed and
   its basis, checks actually executed, the attributable-regression conclusion
   or residual limits, and any rendered or external surfaces not independently
   verified.
