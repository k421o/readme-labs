# README generation interface, version 1

## Named user job

Given a repository checkout and an authorized target path, create an evidenced
README for that component, pass the exact written draft through the canonical
`readme-review` analysis, and apply supported material corrections until the
latest review reaches no material findings or an explicit residual limit.

## Inputs

- A repository checkout containing the component and relevant local evidence.
- A generation request and optional target path; scope defaults to the
  repository's primary missing README when the request does not name a target.
- Explicit rewrite, replacement, or overwrite scope when the target already
  exists.
- Optional authority to execute bounded verification commands.

## Output contract

- Write the README at the authorized target path and preserve correct project
  voice and component-specific facts during an explicit rewrite.
- Establish its evidenced role, reader, delivery surface, shortest useful path,
  boundaries, and canonical routes without imposing a universal template.
- Ground consequential claims in repository evidence and leave no authoring
  placeholders.
- Apply the complete sibling `readme-review` workflow and all of its local
  references to the exact target bytes after drafting and after each material
  revision.
- Finish with a no-material-findings conclusion from the latest complete review
  pass, or identify each residual material finding and the evidence, authority,
  verification, migration, or scope limit that prevents correction.
- Report only commands actually executed and name important links, rendered
  surfaces, or role assumptions that were not independently verified.

## Exclusions

This interface does not promise silent replacement of an existing README, a
generic documentation audit, universal section-template compliance, invented
project facts, independent publication verification without evidence, or
artifact capture during the authoring loop. Capture and lineage remain a
separate owner-selected operation after generation completes. Managed admission
likewise remains outside that loop and moves a completed README directly to its
sole final body-owning path; intake,
evidence, logs, and evaluation context do not become additional durable body
owners.

## Compatibility

Version 1 freezes the named create-review-revise job, explicit overwrite
boundary, and no-material-findings-or-residual-limit completion behavior.
Wording and internal authoring guidance may improve without an
interface-version change when those observable behaviors remain compatible.
