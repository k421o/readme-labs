# Modular README Templates

Build a repository README from small, independent Markdown modules. Each module explains one information element, supplies a copy-ready fragment, identifies the inputs it needs, and includes a focused validation checklist.

This kit is derived from the recovered NotebookLM chat, its source list, the exported Google Docs, and the downloaded header guide. It turns the four-zone model in those materials into files that can be selected, customized, and assembled without copying an entire monolithic template.

## Start here

1. Choose a profile from [Assembly profiles](#assembly-profiles).
2. Read [CONVENTIONS.md](CONVENTIONS.md) before replacing placeholders.
3. Open only the modules selected by the profile.
4. Copy each module's `Template` fragment into the target `README.md` in the order shown below.
5. Remove optional text that does not apply; never leave placeholder tokens behind.
6. Run the checks in [checklists/assembled-readme.md](checklists/assembled-readme.md).

See [ASSEMBLY.md](ASSEMBLY.md) for composition rules and [PROVENANCE.md](PROVENANCE.md) for the local evidence behind the kit.

For multi-section work in Codex, use the repository-local [`$modular-readme` skill](../.agents/skills/modular-readme/SKILL.md) and its [parallel assembly workflow](PARALLEL-ASSEMBLY.md). It preserves these module guides as the source of truth while assigning every independently authorable component to an isolated subagent output.

## Module catalog

### Zone 1: Header and project identity

| Order | Element | Default | Module |
| ---: | --- | --- | --- |
| 1 | Project title (`H1`) | Required | [Project title](modules/01-header-and-identity/01-project-title-h1.md) |
| 1a | Repository-slug alias | Only when names differ | [Repository alias](modules/01-header-and-identity/02-repository-alias.md) |
| 2 | Banner or logo | Optional | [Banner or logo](modules/01-header-and-identity/03-banner-or-logo.md) |
| 3 | GitHub/status badges | Optional | [Badges](modules/01-header-and-identity/04-github-badges.md) |
| 4 | Short description | Required | [Short description](modules/01-header-and-identity/05-short-description.md) |
| 5 | Long description | Optional | [Long description](modules/01-header-and-identity/06-long-description.md) |

### Zone 2: Navigation and context

| Order | Element | Default | Module |
| ---: | --- | --- | --- |
| 6 | Table of contents | Conditional | [Table of contents](modules/02-navigation-and-context/01-table-of-contents.md) |
| 7 | Key features | Recommended | [Key features](modules/02-navigation-and-context/02-key-features.md) |
| 8 | Visual demo | Optional | [Visual demo](modules/02-navigation-and-context/03-visual-demo.md) |
| 9 | Architecture overview | Conditional | [Architecture overview](modules/02-navigation-and-context/04-architecture-overview.md) |
| Applied throughout | Relative links | Required pattern | [Relative links](modules/02-navigation-and-context/05-relative-links.md) |
| Applied where needed | Collapsible details | Optional pattern | [Collapsible details](modules/02-navigation-and-context/06-collapsible-details.md) |

### Zone 3: Operational walkthroughs

| Order | Element | Default | Module |
| ---: | --- | --- | --- |
| 10 | Prerequisites | Conditional | [Prerequisites](modules/03-operational-walkthroughs/01-prerequisites.md) |
| 11 | Installation | Required for installable projects | [Installation](modules/03-operational-walkthroughs/02-installation.md) |
| 12 | Configuration | Conditional | [Configuration](modules/03-operational-walkthroughs/03-configuration.md) |
| 13 | Usage / quickstart | Required | [Usage](modules/03-operational-walkthroughs/04-usage-quickstart.md) |
| 14 | CLI reference | Conditional | [CLI reference](modules/03-operational-walkthroughs/05-cli-reference.md) |
| 15 | API reference | Conditional | [API reference](modules/03-operational-walkthroughs/06-api-reference.md) |
| 16 | Troubleshooting | Optional | [Troubleshooting](modules/03-operational-walkthroughs/07-troubleshooting.md) |

### Zone 4: Governance and legal metadata

| Order | Element | Default | Module |
| ---: | --- | --- | --- |
| 17 | Security reporting | Recommended for public projects | [Security](modules/04-governance-and-legal/01-security.md) |
| 18 | Maintainers | Optional | [Maintainers](modules/04-governance-and-legal/02-maintainers.md) |
| 19 | Contributing | Recommended for collaborative projects | [Contributing](modules/04-governance-and-legal/03-contributing.md) |
| 20 | Code of conduct | Conditional | [Code of conduct](modules/04-governance-and-legal/04-code-of-conduct.md) |
| 21 | Acknowledgments | Optional | [Acknowledgments](modules/04-governance-and-legal/05-acknowledgments.md) |
| Last | License | Required when licensed; always final | [License](modules/04-governance-and-legal/06-license.md) |

### Optional machine-facing companions

These modules keep detailed machine instructions outside the human-facing README.

| Element | Default | Module |
| --- | --- | --- |
| `AGENTS.md` discovery pointer | Optional | [Agent instructions pointer](modules/05-agent-readiness/01-agents-sidecar-pointer.md) |
| `llms.txt` discovery pointer | Optional | [LLM documentation index pointer](modules/05-agent-readiness/02-llms-index-pointer.md) |

## Assembly profiles

Profiles are starting points, not compliance labels.

| Profile | Select these modules first |
| --- | --- |
| Minimal project | Title, short description, usage, license when applicable |
| Reusable library | Minimal + badges, key features, installation, API, contributing |
| CLI tool | Minimal + badges, prerequisites, installation, configuration, CLI, troubleshooting |
| Application | Minimal + banner, key features, visual demo, installation, configuration, security |
| Service or platform | Minimal + badges, architecture, prerequisites, configuration, API, security, contributing |

Add a table of contents when the result is long enough that scanning becomes difficult. The gathered source material uses 100 lines as its house threshold; treat that as a practical trigger, not a universal GitHub platform requirement.

The Codex workflow materializes a profile as a run manifest. It intentionally leaves license, table of contents, repository alias, and other conditional elements for evidence-based selection rather than assuming they apply.

## Terminology note

The visible status chips commonly described as GitHub “tags” are treated here as **badges**. Git tags are version-control references; a release badge can display the latest release created from those tags, but the README does not create Git tags itself.
