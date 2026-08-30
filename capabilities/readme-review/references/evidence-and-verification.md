# Evidence and verification

Match the evidence to the claim under review.

## Preferred evidence

1. Repository implementation, manifests, tests, configuration, and executable
   behavior for claims about this component.
2. Canonical project documents for contribution, security, support, lifecycle,
   and governance routes.
3. Official platform or ecosystem documentation for rendering, publication,
   installation, or package behavior.
4. Pinned repository history when the review depends on when a claim became
   stale or why a compatibility route exists.

Popularity and familiarity demonstrate exposure, not correctness.

## Verification moves

- Resolve relative links from the README's directory and check fragment targets
  when practical.
- Compare install, run, build, and test commands with manifests, entry points,
  CI, and working-directory assumptions.
- Execute the smallest safe command that can disprove a consequential claim
  when mutation is in scope and dependencies are available.
- Check whether a linked canonical document actually answers the question the
  README delegates to it.
- Distinguish package installation from contributor bootstrap, and product
  downloads from source builds.
- Date status, compatibility, performance, or support evidence when it can
  change.

Do not infer that a command works because it is conventional. Do not infer that
a section is missing merely because its common heading is absent; prose or a
canonical route may answer the question.

## Reporting confidence

Use direct language for verified mismatches. Label semantic interpretation,
role assignment, and likely reader impact as judgments. State unrun commands,
unopened external links, unavailable registry rendering, or missing toolchains
as residual verification limits.
