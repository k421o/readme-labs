# Provenance and Interpretation

This kit synthesizes information recovered from a saved Google NotebookLM page and its related documents. It does not claim that every recommendation is a universal GitHub rule; it distinguishes source-derived guidance from the assembly choices made for this kit.

## Local evidence

| Source | Contribution to the kit |
| --- | --- |
| [Saved chat transcript](../docs/chat-transcript.md) | Four-zone model, component order, examples, trade-offs, linting, progressive disclosure, and human-versus-agent separation |
| [Recovered source list](../docs/sources.md) | Inventory of the 136 sources visible in the saved notebook |
| [Notebook overview](../docs/notebook-overview.md) | Notebook identity, save metadata, extraction coverage, and limitations |
| [Downloaded header guide](../related-documents/downloads/readme-header-identity-guide.md) | Detailed title, banner, badge, short-description, and long-description requirements |
| [Comprehensive README export](../related-documents/drive/the-anatomy-of-a-high-quality-readme--1tTXD0q.docx) | Cross-zone synthesis, configuration, dual-audience guidance, and validation framing |
| [Operational walkthrough export](../related-documents/drive/architecting-the-operational-walkthrough--1PwZ6IED.docx) | Installation, prerequisites, usage, API boundaries, and placement trade-off |
| [Governance export A](../related-documents/drive/architectural-standards-for-repository-governance--1k3irUu1.docx) | Security, maintainers, contributing, acknowledgments, and license sequence |
| [Governance export B](../related-documents/drive/architectural-standards-for-repository-governance--1mhqN2Ql.docx) | A distinct Drive record with the same normalized governance body |
| [Zone 1 standards export](../related-documents/drive/modern-repository-standards-and-agentic-ai--1ewHgkai.docx) | Naming variance, local visuals, badge stack, metadata alignment, linting, and `llms.txt` discussion |
| [Zone 2 standards export](../related-documents/drive/modern-repository-standards-and-agentic-ai--11pXR-gY.docx) | TOC, anchor and relative-link rules, Mermaid, collapsible details, `AGENTS.md`, and CI validation |

The collection method, hashes, and known duplicate exports are recorded in [related-documents/README.md](../related-documents/README.md).

## Source-derived guidance retained

- one top-level project title;
- header order of title, optional visual, optional badges, short description, then longer context;
- a practical TOC trigger for READMEs over 100 lines;
- relative links for repository-internal destinations;
- concise, runnable operational examples;
- delegation of exhaustive reference material;
- a governance tail covering security, maintainers, contribution, acknowledgment, and license concerns;
- license as the final README section;
- separation of human onboarding from detailed machine-agent instructions.

## Kit-level decisions

The following choices make the recovered guidance modular and are not represented as universal external standards:

- every content section defaults to `H2` so it can stand alone;
- repository aliasing is split from the title as an optional modifier;
- architecture diagrams are separated from visual product demos;
- CLI and configuration are separated from general usage;
- code-of-conduct and troubleshooting pointers are given dedicated conditional modules;
- badge terminology is clarified separately from Git tags;
- the 100-line TOC threshold is labeled a house convention rather than a GitHub requirement.

## Evidence boundary

The saved notebook exposes source titles and many URLs, but the collection does not contain the full text of every source. The modular templates therefore rely primarily on the visible chat and the seven recovered related documents. Validate project-specific claims, commands, legal terms, and policy addresses against the target repository before publishing.
