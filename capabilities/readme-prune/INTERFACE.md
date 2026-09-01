# README pruning interface, version 1

## Named user job

Given an existing README and authorized subtractive scope, remove the smallest
set of content whose absence is explicitly requested or established by the
canonical README review workflow, make no new substantive claims, and review
the exact final bytes for material effects attributable to pruning.

## Inputs

- A repository checkout containing the existing README and relevant local
  evidence.
- Either exact user-directed removal scope or an open-ended request to trim,
  declutter, shorten by subtraction, or remove low-signal content.
- Optional authority to execute bounded verification commands.

## Output contract

- Distinguish `user_directed` removals from `review_evidenced` removals and
  report the basis for each material unit removed.
- For evidence-selected pruning, remove only repository-evidenced unsupported,
  stale, duplicative, or noisy units whose absence preserves the README's
  evidenced reader contract.
- Preserve correct component-specific content, project voice, pre-existing
  changes, the shortest useful reader path, consequential boundaries, and
  supported delivery surfaces.
- Make no new substantive claims, sections, commands, or links. Limit additions
  to local Markdown, grammar, or link repairs made necessary by deletion.
- Apply the complete sibling `readme-review` workflow and all of its local
  references to the initial and exact final bytes.
- Restore an agent-selected deletion that causes a material reader regression.
  Do not silently reverse an exact user-directed removal; report any resulting
  material regression as a residual limit.
- Finish with no material regression attributable to agent-selected pruning,
  or identify the exact evidence, authority, verification, migration, or scope
  limit that remains.
- Report only commands actually executed and name important links, rendered
  surfaces, or role assumptions that were not independently verified.

## Exclusions

This interface does not promise a findings-only audit, creation or replacement
of a README, broad rewriting, relocation, whole-file deletion or movement,
delivery-interface migration, a numeric shortening target, correction of
unrelated pre-existing gaps, or artifact capture during pruning.

## Compatibility

Version 1 freezes the directed-versus-evidenced removal modes, semantic
subtraction boundary, restoration rule for agent-selected over-deletion, and
no-attributable-material-regression-or-residual-limit completion behavior.
Wording and internal pruning guidance may improve without an interface-version
change when those observable behaviors remain compatible.
