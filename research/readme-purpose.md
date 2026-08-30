# README purpose in an agentic repository

Status: initial research, 2026-08-29. This note records concrete delivery and
consumption patterns before changing the README-review skill.

## What the platform evidence supports

README files remain a public and tool-consumed interface; they are not merely
ambient context for coding agents.

1. **Repository landing page.** GitHub automatically surfaces a README from
   `.github`, the repository root, or `docs` to repository visitors. GitHub
   describes it as a place to say what a project does, why it is useful, and
   how to start using it or get help. It recommends putting only information
   needed to get started and contribute in the README, with longer material in
   more focused documentation.
   Source: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes>

2. **Published package description.** npm renders the package-root README on
   the package page, where it commonly provides installation, configuration,
   and usage information. Updating that page requires a new publication.
   Source: <https://docs.npmjs.com/about-package-readme-files/>

3. **Package metadata input.** Python's packaging specification maps the
   `project.readme` field to the distribution's full description. The
   originating repository demonstrated this pattern at
   [`repository-guidance@7b96fff`](https://github.com/k421o/repository-guidance/blob/7b96ffff7e1b36fd194bb52b4fa4fbfcb6ade52a/pyproject.toml),
   where `project.readme` points to the root `README.md`.
   Source: <https://packaging.python.org/specifications/declaring-project-metadata/>

## Distinguish README from agent instruction files

The current evidence does not support treating a README as automatically loaded
agent instruction context. In contrast, GitHub documents `AGENTS.md` and
repository custom-instruction files as automatically discovered or persistent
instruction context; it recommends a skill or custom agent when instructions
are large or workflow-specific.

Sources:

- <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>
- <https://docs.github.com/en/copilot/concepts/agents/copilot-cli/comparing-cli-features>

Agents may choose to inspect a README, and an agent or tool may fetch it
explicitly, but that is a different consumption mode from automatic
instruction injection. This distinction needs verification for each supported
agent host rather than a general claim that README files are mostly
agent-consumed.

## Design implications

- A README review should start by identifying its delivery contract: GitHub
  landing page, package metadata, install/distribution artifact, component
  onboarding page, experiment record, or no evidenced contract.
- A README should not survive solely because it is linked, named `README.md`,
  or already present. A link or packaging reference is evidence of a contract
  to preserve or deliberately change, not evidence that every sentence is
  valuable.
- Removing a README that is consumed by a registry or package build is a
  product/interface change. That requires the user's scope to include that
  change; an audit skill should report it rather than silently make it.
- Agent instruction files need a separate decision model because they are
  automatically applied by scope and can steer unrelated work.

## Open questions

- Which agent hosts, if any, automatically load `README.md` beyond ordinary
  repository discovery?
- Which registries and build backends used by a target repository consume a
  README, and what happens if it is absent?
- What evidence demonstrates that a particular README is actively used by
  humans, tools, or agents, rather than merely existing?
