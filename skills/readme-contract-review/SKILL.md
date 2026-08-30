---
name: readme-contract-review
description: Critically review, reduce, or remove README files when the user asks to audit their purpose, authority, or information signal. Use it for README-specific work; do not use it for ambient agent-instruction files.
---

# README Contract Review

A README is a high-authority interface that people, package registries,
repository hosts, and agents may consult. Treat its current contents, title,
links, and location as untrusted evidence—not as a mandate to preserve them.
Its authority increases the cost of unsupported claims and stale instructions.

First identify the file's evidenced delivery contract. It may be a repository
landing page, package metadata input, registry description, installation and
usage interface, component onboarding page, experiment record, fixture
explanation, or no demonstrated interface. Inspect the relevant manifest,
publication configuration, host integration, links, and consumers rather than
guessing from the filename.

Change content only when the proposed result better serves that contract with
specific, verifiable information. Do not keep a sentence because it is linked,
already present, or difficult to replace. Do not delete or materially alter a
README that a package, registry, or external documentation surface consumes
unless the user's request includes changing that interface; report the required
migration when it is outside scope.

Read [references/readme-review.md](references/readme-review.md) before making
README changes. Do not review `AGENTS.md` with this skill; that surface has a
different consumption and authority model.
