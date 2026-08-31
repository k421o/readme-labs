# README Assembly Guide

The modules are composable fragments, not sections that must all be present. Start with the reader's shortest successful journey and add only the supporting information that project actually needs.

For one-agent-per-component authoring, follow [PARALLEL-ASSEMBLY.md](PARALLEL-ASSEMBLY.md). Parallel workers produce isolated fragments; the ordering and content rules below remain integration constraints owned by the parent agent.

## Default sequence

```text
H1 title
repository alias (inside the H1, only when needed)
banner or logo
badges
short description
long description
table of contents (when needed)
key features
visual demo
architecture overview
prerequisites
installation
configuration
usage / quickstart
CLI reference
API reference
troubleshooting
security
maintainers
contributing
code of conduct
acknowledgments
agent or LLM discovery pointers (only when useful to human contributors)
license (final section)
```

Relative-link and collapsible-detail modules are patterns applied wherever needed rather than positions in the sequence.

## Resolve the usage-versus-installation choice

The recovered material documents two valid orders:

- **Installation first** favors a procedural onboarding path: prepare, install, then run.
- **Usage first** favors rapid product evaluation: show a minimal example, then explain setup.

Use installation first by default. Move a five-to-ten-line usage preview before installation when the project's primary audience needs to evaluate API or CLI ergonomics before committing to setup. Do not duplicate the same long example in both places.

## Compose without heading collisions

Most modules emit an `H2`. If prerequisites belongs inside installation, change `## Prerequisites` to `### Prerequisites`. Apply the same one-level demotion to any section deliberately nested beneath another. Never introduce a second `H1`.

## Keep the README bounded

Use progressive disclosure:

- keep the happy path in the README;
- place exhaustive API material in `docs/API.md` or generated reference docs;
- place full contribution procedures in `CONTRIBUTING.md`;
- place private vulnerability instructions in `SECURITY.md`;
- place long configuration schemas inside `<details>` or a dedicated file;
- place machine execution rules in `AGENTS.md`;
- link every delegated document from the corresponding summary module.

## Finalize

1. Replace all placeholders.
2. Delete authoring comments and unused variants.
3. Confirm every command against the project.
4. Confirm internal links from the repository root.
5. Confirm the section order and single-H1 rule.
6. Confirm license is last when included.
7. Run [the assembled README checklist](checklists/assembled-readme.md).

In a parallel run, finalize only after every selected worker has a ready evidence report. Generate the table of contents from final headings, assemble a preview, and review cross-component terminology and factual consistency before replacing the target README.
