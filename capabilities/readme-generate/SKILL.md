---
name: readme-generate
description: Generate a repository README from repository evidence, then revise the draft through the canonical README review workflow. Use when asked to create, draft, bootstrap, or explicitly replace a README. Do not use for an audit, critique, or focused improvement of an existing README; use readme-review for those requests.
---

# README generation

Create a README as a reader-facing interface for the evidenced component, not
as a generic section template. Keep the draft mutable until the requested
authoring work is complete.

## Required review source

Before authoring, read the sibling [README review
skill](../readme-review/SKILL.md) completely and read every local reference
file shipped in [its references directory](../readme-review/references/). The
review skill and those references are the single source of role, evidence,
analysis, and finding behavior. Do not restate or fork their criteria in this
skill.

## Scope and overwrite boundary

- Resolve the target README path and read the nearest applicable repository
  guidance before changing files.
- Create a missing target when the request identifies its component. A request
  to create a README does not by itself authorize replacing a target that
  already exists.
- Replace an existing README only when the user explicitly asks for a rewrite,
  replacement, or overwrite. Otherwise preserve it and route audit or focused
  improvement work through `readme-review`.
- For an authorized rewrite, preserve correct component-specific content,
  project voice, and pre-existing changes. Do not delete or move a README used
  by packaging, a registry, or another delivery surface unless the requested
  scope includes migrating that interface.

## Authoring workflow

1. Inspect enough of the repository to identify the component, its intended
   readers, and the README's evidenced role and delivery surfaces. Prefer
   implementation, manifests, entry points, tests, canonical project
   documents, and verified behavior over conventions or guesses.
2. Establish the shortest supported reader path: identity, factual purpose,
   intended use, one useful result, necessary boundaries, and routes to
   maintained detail. Distinguish consuming the artifact from developing the
   repository.
3. Plan only the content that the component earns. Use recognizable headings
   when they help readers, but do not impose a universal section order, badges,
   a directory map, or empty conventional sections.
4. Write the draft at the exact target path so relative links and delivery
   assumptions can be reviewed in their real context. Do not leave
   placeholders or invent commands, compatibility, status, support, security,
   performance, or publication claims. Keep uncertainty visible or omit a
   claim that repository evidence cannot support.
5. Apply the complete sibling `readme-review` workflow to the exact written
   draft, including its finding standard, execution-claim audit, change
   safeguards, and every local reference. Treat material findings as internal
   revision input.
6. Apply the smallest supported corrections, then run the complete review
   workflow again against the revised bytes. Repeat while a review pass finds
   a material, in-scope issue that repository evidence can correct.
7. Stop when the latest complete pass reaches a no-material-findings
   conclusion. If a remaining correction requires unsupported facts, external
   verification, new authority, an interface migration, or work outside the
   requested scope, keep the best factual draft and report the residual finding
   and its exact limit instead of inventing a resolution.
8. Validate changed relative links and consequential commands in proportion to
   risk. In the final response, name the target, the evidenced role, checks
   actually executed, the no-material-findings conclusion or residual limits,
   and any rendered or external surfaces not independently verified.

## Authoring boundary

Do not capture the mutable draft as a README artifact, create a content-addressed
record, attach evaluation evidence, or assign lineage during the generation and
review loop. Artifact capture is a separate, explicit boundary after an owner
selects a completed output; this skill does not cross it automatically.
