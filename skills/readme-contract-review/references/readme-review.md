# Reviewing README files

Review each README as an interface, not as a repository artifact that earns
preservation by default. Identify the delivery contract before judging its
contents. A repository host landing page, package registry description,
distribution metadata input, component onboarding page, fixture explanation,
and experiment record make different claims necessary and different claims
harmful.

## Establish the contract

Look for concrete consumers: package metadata such as `project.readme`, package
publication settings, documentation-site configuration, repository-host
rendering, direct links, installer output, or a defined component entry point.
Classify the evidence and its consequence:

- A registry or package build consumes the README: changes affect a published
  product surface.
- A repository host surfaces it: it is a visitor-facing landing page.
- A local component points to it: it may provide targeted orientation.
- No consumer or role is evidenced: its existence alone does not establish a
  contract.

An inbound link establishes a dependency to inspect, not that the linked text
is true, useful, or indispensable. Repair, redirect, or deliberately retire a
link only when the user's scope authorizes that interface change.

## Review claims independently

Apply this test to a complete claim, section, or command:

> What concrete reader, tool, or agent decision does this change, and what
> current evidence supports it?

Remove or correct claims that lack a supported decision boundary, including
directory inventories, generic project descriptions, agent policy, stale
commands, speculative status, historical cleanup rationale, and instructions
that paraphrase a manifest or source tree without adding use context. A short
README can still be harmful if it asserts authority without evidence; a long
README can be appropriate when its interface requires a working manual.

Give particular scrutiny to commands, compatibility claims, support statements,
and security or privacy assertions. Verify them against the relevant current
implementation or external contract when practical. Do not convert an agent's
inference into README authority merely because agents are likely to read it.

## Make scoped changes

Keep only content that is supported and useful for the established contract.
If a claim belongs in a reference, command help, package metadata, or a focused
topic document, move it only when that destination is itself maintained and the
user asked for that interface work. Otherwise remove the unsupported residue or
report the gap.

Before completing an authorized change, inspect the resulting public or package
surface for broken links, stale paths, misleading commands, and new unsupported
claims. This is a check on the proposed interface, not a requirement to retain
the old document's semantics.
