---
name: readme-review
description: Review repository README files for reader-facing signal, factual support, role-appropriate structure, and useful routing. Use when asked to audit, critique, compare, or improve a README; decide what belongs in one; find stale or missing README guidance; or verify that a README matches its repository. Do not use README conventions as a universal template or treat README prose as agent policy.
---

# README review

Review the README as an interface between a particular component and its
readers. Establish its role before judging its sections or length.

## Workflow

1. Read the README, the nearest applicable repository guidance, and enough of
   the surrounding repository to identify the component. Inspect manifests,
   entry points, canonical docs, contribution/security files, and commands that
   bear directly on README claims.
2. Assign the README's primary role using
   [roles and anatomy](references/roles-and-anatomy.md). State uncertainty when
   the repository/package/publication relationship is ambiguous.
3. Trace the opening reader path: identity, factual definition, intended use,
   and the shortest supported route to a useful result. Distinguish consuming
   the artifact from developing the repository.
4. Check routing and boundaries. Verify that links reach canonical maintained
   surfaces and that consequential compatibility, status, security, archive,
   or working-directory constraints are visible where a reader needs them.
5. Verify factual claims with repository evidence. Prefer executing safe,
   bounded commands when the task authorizes verification; otherwise report
   what was and was not checked. Follow
   [evidence and verification](references/evidence-and-verification.md).
6. Apply the [review criteria](references/review-criteria.md). Report only
   issues that can materially change understanding, correct use, navigation,
   or contribution. Do not demand empty conventional sections.

## Finding standard

For each finding, provide:

- the README path and tight line range;
- the unsupported, missing, stale, misplaced, or noisy signal;
- repository evidence that establishes the mismatch or need;
- the likely reader impact; and
- the smallest correction direction, without rewriting the whole README unless
  requested.

Rank findings by reader impact. Separate verified facts from interpretations.
Do not use stars, badges, length, heading order, or familiarity as a quality
score.

If no material issues remain, say so and name any commands, links, rendered
surfaces, or role assumptions that were not independently verified.

## Change requests

When asked to edit rather than review:

- preserve correct, component-specific content and existing project voice;
- remove or relocate content only when a clearer canonical surface exists;
- use conventional headings when they improve recognition, not to impose a
  template;
- validate changed relative links and commands in proportion to risk; and
- keep agent behavioral policy in the repository's agent-guidance surface
  unless it is also an authentic human-facing component contract.
