# README anatomy, version 1

Research snapshot: 2026-08-29

## Executive conclusion

A root `README.md` is the reader-facing landing page for a repository or
published component. Its most recognizable shape is:

> identity and purpose -> first successful use -> deeper guidance ->
> participation, support, and ownership

The headings do not have to be identical, and inapplicable sections should not
be added. The sequence should nevertheless feel familiar. A reader or agent
should be able to answer, with little inference:

1. What is this, and is it the thing I meant to find?
2. Why or when would I use it?
3. What is the shortest supported path to a useful result?
4. Where is the detailed or specialized documentation?
5. What constraints, compatibility boundaries, or failure modes matter?
6. How do I get help or contribute?
7. Who owns it, and under what legal or project terms?

The strongest cross-source evidence is for **what** and **how** information.
Conventional headings such as `Installation`, `Usage`, `Examples`,
`Documentation`, `Contributing`, and `License` are common enough to be useful
retrieval labels for humans and agents. Familiarity is better pursued at this
category level than by copying the exact README of one famous project.

No public evidence supports a defensible ranking of individual READMEs by
frequency in the training data of current proprietary agents. Repository age,
stars, forks, mirrors, package-registry rendering, and web visibility are useful
exposure proxies, but they are not training counts. Deduplication also weakens
the intuition that a heavily forked file must occur many times in a training
set.

## Method and confidence

This synthesis uses four evidence layers:

1. Current, official documentation from GitHub and package ecosystems for the
   behavior and publication role of README files.
2. Primary empirical studies over random or ecosystem-scale README samples for
   category prevalence.
3. Current default-branch READMEs from a purposive sample of established public
   software repositories for recognizable real-world shapes.
4. Public code-corpus papers and dataset cards for the narrow question of
   whether Markdown repository files occur in documented model-training data.

Repository metadata and preferred README contents were retrieved through the
[GitHub REST API][github-readme-api] on 2026-08-29. The audit favors active,
long-lived software repositories created by 2018 with at least 50,000 stars,
then stratifies across component roles. It excludes list and curriculum
repositories even when they have more stars. It is intentionally qualitative:
the sample is too small and too selected to estimate GitHub-wide frequencies.

Confidence is high for the category-level core, moderate for the role-specific
ordering, and low for any inference about a named proprietary model's exposure
to an individual file. Current README contents can be newer than a model's
training cutoff, and exact corpora, sampling weights, and deduplication policies
are generally unavailable.

## What a README does

A README has six jobs. The emphasis changes with the component, but the jobs
are stable:

| Job | Reader question | Typical content |
| --- | --- | --- |
| Identify | What is this? | Name, one-sentence definition, repository/package relationship |
| Qualify | Is it for me? | Purpose, differentiators, status, supported use cases |
| Launch | How do I reach one useful result? | Prerequisites, install or download, smallest working example |
| Route | Where is the rest? | Documentation, API/reference, examples, support links |
| Bound | What must I not assume? | Compatibility, supported modes, important caveats, security boundary |
| Invite | How do I participate or attribute it? | Contributing, development, governance, maintainers, license, citation |

GitHub describes nearly the same core in reader language: what a project does,
why it is useful, how to get started, where to get help, and who maintains and
contributes to it. GitHub also says a README should contain what developers need
to start using and contributing, with longer documentation living elsewhere.
See [About the repository README file][github-readme].

A README is normally not:

- An agent-policy file. Behavioral instructions belong in the repository's
  agent-guidance surface.
- A complete changelog, roadmap, issue tracker, or design-history archive.
- A prose rendering of the directory tree, manifest, configuration schema, or
  command help.
- A substitute for full tutorials, API reference, operations manuals, or
  contributor documentation when those deserve maintained documents of their
  own.
- A badge wall, sponsor wall, or contributor roll with a small amount of project
  documentation attached.

## The default, non-surprising anatomy

The following is a semantic spine, not a mandatory template. Omit a section
when its question is irrelevant or another canonical surface answers it better.

| Order | Information category | Default treatment | Common headings |
| --- | --- | --- | --- |
| 1 | Identity | Always present. Match the repository or published component name, or explain the relationship immediately. | Project name; usually no `Overview` heading |
| 2 | Definition and purpose | One sentence saying what it is, followed when useful by audience, motivation, differentiators, or scope. | About, Overview, Why, Features |
| 3 | Status metadata | Keep only decision-relevant, current signals. Badges are metadata, not a substitute for prose. | Status, Compatibility, Platform support |
| 4 | First successful path | Give the shortest supported route to a useful result. Separate consumer setup from contributor setup. | Quick start, Getting started, Installation, Download |
| 5 | Minimal use | Prefer one copyable example with expected behavior over a catalog of features. | Usage, Example, Your first program |
| 6 | Depth and choices | Route to detailed docs or explain the choices necessary for correct use. | Documentation, API, Configuration, Options, Examples |
| 7 | Boundaries | Include only consequential constraints that are not obvious from the interface. | Requirements, Compatibility, Security, Troubleshooting, Limitations |
| 8 | Development and participation | Explain local build/test only for contributors, then link the full contribution process if one exists. | Development, Building, Testing, Contributing |
| 9 | Help and project structure | Supply the correct help channel and, for community projects, governance or maintainer information. | Support, Community, Governance, Maintainers |
| 10 | Legal and provenance | Link the license; add citation, acknowledgements, or trademarks when the component requires them. | License, Citation, Credits, Trademark |

This order has a practical logic: a reader should not have to cross governance,
sponsor, or contributor material before learning what the software is and how
to try it. A long README can reorder later sections for its audience, but its
opening should still establish identity, orientation, and the first route to
success.

### Minimal skeleton

```markdown
# Project name

One sentence that identifies the component and its purpose.

Optional short context: intended audience, important differentiator, or a
non-obvious repository/package relationship.

## Getting started

Only the prerequisites and commands needed for the shortest supported path.

## Usage

One minimal example and the result or behavior a reader should expect.

## Documentation

Links or concise guidance for API details, configuration, examples, and
advanced use.

## Development

Contributor-only setup, build, and test commands, if this repository needs
them.

## Support

The appropriate place for questions, bugs, and security reports, when these
channels are not already obvious and distinct.

## Contributing

A short invitation and a link to the maintained contribution guide.

## License

The license identifier and a link to the license file.
```

The skeleton is deliberately conventional and deliberately incomplete. It
should not produce empty headings, duplicate a package manifest, or force
support, contribution, or license prose into a private component where those
questions do not arise.

GitHub generates an outline from Markdown headings, so a manual table of
contents is normally unnecessary for a short or medium README. Add one only
when the document is long enough that inline navigation materially helps.

## Anatomy varies by repository role

| Repository or component role | Expected emphasis | Legitimate deviation from the default |
| --- | --- | --- |
| Published library or package | Definition, install, smallest import/use example, API/configuration route, compatibility, license | The README may be the package-registry landing page and therefore contain more consumer documentation than the repository itself needs. |
| CLI tool | Definition, why/why not, installation choices, command examples, configuration, exit or filtering behavior | Benchmarks, comparison tables, shell completions, and platform packages can be central rather than decorative. |
| End-user application | Product/repository relationship, download or run path, screenshots where behavior is visual, support | Installation may mean downloading a release rather than building the source. |
| Framework or platform | Scope and mental model, start using, start developing, supported components, community/governance | User and developer paths often need visibly separate sections. |
| Source distribution or language runtime | Canonical docs, supported releases, build, security, contribution, governance | A small root README can act as a router because ordinary usage is documented outside the source repository. |
| Monorepo root | System identity, how packages relate, root-level bootstrap, canonical routing | A categorized component map can help; a raw directory listing usually cannot. Package READMEs should describe their own published or operational contracts. |
| Experiment or research artifact | Question, data/input provenance, method, exact reproduction, outputs, dated limitations, citation | Results and interpretation boundaries can be more important than installation. |
| Fixture, example, or unusual subtree | Why the files are deliberately unusual and how the parent test or tool consumes them | A very short README is sufficient when it resolves the otherwise misleading local context. |
| Archived or superseded project | Status first, replacement or migration route, security/maintenance boundary | Historical context is useful only insofar as it changes the reader's next action. |

The same filename can therefore serve as a package page, a source-tree entry
point, a component manual, an experiment record, or a fixture explanation.
Judging content without first identifying that role produces both bloated and
over-pruned READMEs.

## What large samples say is prevalent

Three empirical studies give a more reliable account of common information
categories than a hand-picked template:

| Study | Corpus and method | Most relevant result |
| --- | --- | --- |
| [Prana et al., *Categorizing the Content of GitHub README Files*][prana] | 4,226 manually annotated sections from 393 randomly sampled GitHub repositories | At least one **What** section occurred in 97.0% of files, **How** in 88.5%, **References** in 60.8%, **Who** in 52.9%, **Contribution** in 27.8%, **Why** in 25.7%, and **When/status** in 21.4%. |
| [Ikeda et al., *An Empirical Study on README Contents for JavaScript Packages*][ikeda] | 43,911 filtered npm/GitHub package READMEs; headline themes normalized and grouped | **Usage** appeared in 60.83%, **Install** in 59.43%, **License** in 36.22%, **API** in 24.27%, **Options** in 23.78%, **Release history** in 13.35%, **Contribute** in 11.23%, and **Test** in 9.94%. |
| [Venigalla and Chimalakonda, *Correlation between README Content and Project Popularity*][popularity] | 1,950 READMEs across ten programming languages, split into popular and non-popular groups | How-to-use content was widespread in both groups. References and contribution information, as well as links, lists, and images, were positively associated with popularity. The design establishes association, not causation. |

The studies use different units and taxonomies, so their percentages should not
be merged into one ranking. Ikeda et al. infer categories from headings; content
in an unheaded lead can therefore make a category look rarer than it is. Prana
et al. code full sections and use broader categories. The convergence is more
important than the numeric differences:

- **What + how** is the stable core.
- Installation and usage are the dominant concrete forms of **how** for
  reusable software.
- References commonly extend the README into canonical documentation rather
  than making the README exhaustive.
- Contribution, ownership, purpose, and status are familiar but conditional.
- Images, lists, tables, and badges are presentation devices, not information
  categories. Their presence cannot rescue missing identity or usage guidance.

## High-exposure repository audit

The following purposive sample examines long-lived, highly visible public
software repositories. It is not a statistically representative sample and
does not label popularity as quality. It was selected to expose agents to
recognizable shapes across libraries, frameworks, CLIs, applications,
platforms, and runtimes. Stars and forks are GitHub API snapshots from
2026-08-29, rounded below only for readability.

| README | Exposure proxy | Recognizable shape or lesson |
| --- | ---: | --- |
| [React][react-readme] | 248k stars / 51k forks | Definition and benefits -> installation -> documentation -> example -> contributing -> license. A strong general-purpose library spine. |
| [TensorFlow][tensorflow-readme] | 198k / 76k | Ecosystem definition and API boundary -> install -> first program -> contribution/support -> build status/resources/license. |
| [Visual Studio Code][vscode-readme] | 190k / 42k | Explains the source-repository versus distributed-product boundary before contribution and feedback routes. |
| [Go][go-readme] | 137k / 19k | A compact source-tree router: language identity -> canonical docs -> download/install -> contribution. |
| [Kubernetes][kubernetes-readme] | 126k / 44k | Separates “start using” from “start developing” and states an unsupported library-consumption boundary. |
| [Electron][electron-readme] | 123k / 17k | Install/platform support -> learning resources -> programmatic use -> contributing/community/license. |
| [Node.js][node-readme] | 120k / 37k | Source-distribution and governance manual: support/releases/download/verification -> build/security/contribution -> teams/keys/license. |
| [Rust][rust-readme] | 117k / 15k | Why -> quick start -> source installation -> help -> contributing -> license/trademark. |
| [Axios][axios-readme] | 109k / 12k | README as an extensive package manual: install/example/API/configuration/errors and formats. Its large sponsor preface is high exposure but not a model opening. |
| [Deno][deno-readme] | 108k / 6k | Install -> first program -> resources -> contributing, with identity and product links in the lead. |
| [Redis][redis-readme] | 76k / 25k | What/why -> getting started and client paths -> capabilities -> community -> detailed source build -> contribution/trademarks. |
| [Flask][flask-readme] | 72k / 17k | Minimal landing page: definition and positioning -> runnable example -> project support -> contributing. |
| [Express][express-readme] | 69k / 25k | Working example before install -> features/docs -> quick start -> rationale/examples -> contribution/team/license. |
| [ripgrep][ripgrep-readme] | 68k / 2.7k | Definition -> docs and demonstrations -> why/why not -> evidence and comparison -> install/build/test/security. A strong CLI-specific anatomy. |
| [Git][git-readme] | 63k / 28k | A deliberately small source-tree orientation and documentation/build pointer rather than a modern package landing page. |
| [Rails][rails-readme] | 59k / 22k | Framework identity and layer model -> getting started -> contributing -> license. |
| [Requests][requests-readme] | 54k / 10k | Definition -> immediate code example and value statement -> installation/support boundary -> features -> unusual clone constraint. |

Several stable patterns emerge:

1. **The lead carries identity.** Most projects do not spend a heading on
   `Overview`; they place the definition directly below the title or brand.
2. **A successful action appears early.** Depending on role, it is an install,
   download, first program, canonical getting-started link, or source build.
3. **User and contributor setup are distinct.** Mature projects label or route
   these paths instead of mixing package installation with repository bootstrap.
4. **The README either routes or contains depth.** React, Go, Flask, and VS Code
   route aggressively; Axios, Redis, Node.js, and ripgrep keep substantially
   more detail locally. Length follows role, not maturity.
5. **Project-specific boundaries earn prominent space.** Examples include
   Kubernetes' unsupported module use, VS Code's product/source distinction,
   Node.js release and binary-verification information, and Requests' unusual
   clone requirement.
6. **Contribution and legal material tend to come after orientation and use.**
   Governance may grow large for mature foundations, but it is not the first
   question the README answers.
7. **High exposure does not imply ideal structure.** Sponsor blocks, exhaustive
   maintainer lists, giant API references, and legacy formatting all occur in
   famous repositories. They are evidence of real variation, not defaults to
   imitate.

### Particularly useful exemplars

There is no single best README. These are useful models for specific decisions:

- **React** for a conventional reusable-library landing page.
- **Flask** for the smallest README that still establishes identity and proves
  use with a runnable example.
- **ripgrep** for a CLI whose selection criteria, examples, configuration,
  installation, and performance claims are intrinsic to correct adoption.
- **Kubernetes** for separating user and developer paths and stating a
  non-obvious support boundary.
- **Visual Studio Code** for distinguishing a public source repository from the
  branded distributed product.
- **Requests** for a demonstration-first package README and a narrowly justified
  operational caveat.
- **Node.js** and **Redis** for mature projects whose README legitimately acts
  as a source-distribution or operations manual.

## What “training-data prevalence” can and cannot mean

Current proprietary model providers do not publish file-level training
inventories or occurrence counts. Current READMEs can also postdate a model's
training cutoff. A statement such as “React has the most prevalent README in
agent training” would therefore be unsupported.

Public code corpora show why README familiarity is nevertheless plausible. The
[Stack dataset card][stack-card] explicitly includes Markdown as a language and
represents content as individual files. [The Stack paper][stack-paper]
describes a permissively licensed GitHub corpus and reports that
near-deduplication improves training. [The Stack v2 dataset card][stack-v2]
reports 3.28 billion unique files from 104.2 million repositories and says
roughly 40% of permissively licensed files were exact or near duplicates during
preprocessing. These sources establish that Markdown repository documentation
can appear in code-model corpora; they do not establish that a particular
README was used by a particular model.

The defensible prevalence hierarchy is therefore:

1. **Directly measured category prevalence:** what, how, usage, installation,
   license, API/options, references, and contribution from the empirical README
   studies.
2. **Observed ecosystem prevalence:** GitHub automatically surfaces a preferred
   README, npm renders a package-root `README.md`, PyPI can use it as the project
   page's long description, and crates.io transfers and renders the package
   README. Package-facing READMEs consequently appear on more than one major
   surface. See the [GitHub][github-readme], [npm][npm-readme],
   [Python packaging][python-readme], and [Cargo][cargo-readme] documentation.
3. **Exposure proxies for individual examples:** long public history, stars,
   forks, dependents, mirrors, registry use, documentation links, and web
   indexing. The audit above uses only some of these and does not convert them
   into a fabricated score.
4. **Unknown:** the file-level contents and sampling weights of a current
   proprietary agent's training set.

For agent familiarity, the practical implication is to prefer literal,
high-prevalence category labels over clever headings. `Installation`, `Usage`,
`Examples`, `Documentation`, `Contributing`, `Security`, and `License` are
easier to recognize and retrieve than project-themed synonyms. The content may
still be project-specific; familiarity should come from the information
architecture, not generic prose.

## Agent-oriented authoring rules

Use these rules when creating or reviewing a README:

1. Identify the README's actual role before evaluating its length or sections.
2. Put the component name and factual definition before promotional, sponsor,
   governance, or historical material.
3. Put the smallest supported success path near the top. If the real path lives
   elsewhere, link directly to it and say what the reader will find there.
4. Use conventional headings and one heading per semantic category. Do not hide
   installation under `Hacking` or support under `Community vibes`.
5. Distinguish **using the artifact** from **developing the repository**.
   Commands should state non-obvious prerequisites and working-directory
   assumptions.
6. Prefer a minimal executable example over an unprioritized feature list. Give
   expected output or behavior when it prevents ambiguity.
7. State surprising boundaries early: package versus monorepo, product versus
   source distribution, supported versus internal APIs, maintained versus
   archived status, or safe versus unsafe modes.
8. Route depth to the canonical maintained surface. Keep enough local context
   that the link has meaning; do not turn the README into a bare index.
9. Keep changing facts verifiable. Prefer a release, compatibility, status, or
   security source over unsupported “production-ready” prose.
10. Do not add empty conventional sections. Familiar structure is a default,
    not a demand for boilerplate.
11. Keep agent policy out of the README unless it is also an authentic part of
    the human-facing component contract.
12. Validate commands, relative links, package rendering, and examples. A
    familiar heading containing stale instructions is worse than an omitted
    heading.

## Review decision table

| Information | Expected when | Surprising or noisy when |
| --- | --- | --- |
| Title and definition | Always | It merely repeats a directory name without saying what the component is. |
| Purpose or differentiators | Choice of tool or scope is not obvious | It is promotional, generic, or unsupported. |
| Install/download | The artifact is consumed or run | The repository is documentation-only or the command duplicates a canonical, version-sensitive installer without useful context. |
| Usage/example | Readers can exercise an interface | The “example” is a full tutorial, generated output, or untested pseudocode. |
| Documentation/API route | Depth lives elsewhere or the interface is broad | It is an unclassified list of links visible from the tree. |
| Compatibility/status | The reader's decision depends on it | It is an undated or unsupported quality claim. |
| Build/test/development | Contributors need repository-specific steps | It restates standard tool commands that the manifest or command help makes sufficient. |
| Support/security | Channels or disclosure paths differ | It repeats generic security warnings or sends every request to the same place. |
| Contributing/governance | External participation is supported | It embeds a long policy already maintained in `CONTRIBUTING.md` or governance docs. |
| License/citation/credit | Distribution, attribution, or research use requires it | It reproduces long legal text better kept in the canonical file. |
| Roadmap/history | Current use requires lifecycle context | It records plans, abandoned ideas, or implementation residue as current documentation. |
| Directory map | Categorization reveals architecture or ownership | It paraphrases self-explanatory names or will immediately drift. |

The governing test remains:

> If this unit disappeared, would a capable reader or agent be materially more
> likely to misunderstand, misuse, or fail to adopt this specific component?

The anatomy adds a complementary test:

> If this README is missing a conventional category, is the question
> inapplicable, answered by a clearly routed canonical surface, or simply
> unanswered?

## Sources

### Platform and ecosystem conventions

- [GitHub: About the repository README file][github-readme]
- [npm: About package README files][npm-readme]
- [Python Packaging User Guide: Writing `pyproject.toml`][python-readme]
- [Cargo Book: The `readme` field][cargo-readme]
- [Standard Readme specification][standard-readme] (a community convention for
  open-source libraries, not a universal standard)

### Empirical and training-corpus research

- [Prana et al., *Categorizing the Content of GitHub README Files*][prana]
- [Ikeda et al., *An Empirical Study on README Contents for JavaScript
  Packages*][ikeda]
- [Venigalla and Chimalakonda, *An Empirical Study on Correlation between
  README Content and Project Popularity*][popularity]
- [The Stack dataset card][stack-card]
- [Kocetkov et al., *The Stack: 3 TB of Permissively Licensed Source
  Code*][stack-paper]
- [The Stack v2 dataset card][stack-v2]

[github-readme]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
[npm-readme]: https://docs.npmjs.com/about-package-readme-files/
[python-readme]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#readme
[cargo-readme]: https://doc.rust-lang.org/cargo/reference/manifest.html#the-readme-field
[standard-readme]: https://github.com/RichardLitt/standard-readme/blob/main/spec.md
[github-readme-api]: https://docs.github.com/en/rest/repos/contents#get-a-repository-readme
[prana]: https://arxiv.org/abs/1802.06997
[ikeda]: https://arxiv.org/abs/1802.08391
[popularity]: https://arxiv.org/abs/2206.10772
[stack-card]: https://huggingface.co/datasets/bigcode/the-stack/blob/main/README.md
[stack-paper]: https://arxiv.org/abs/2211.15533
[stack-v2]: https://huggingface.co/datasets/bigcode/the-stack-v2-train-full-ids/blob/main/README.md
[react-readme]: https://github.com/react/react/blob/main/README.md
[tensorflow-readme]: https://github.com/tensorflow/tensorflow/blob/master/README.md
[vscode-readme]: https://github.com/microsoft/vscode/blob/main/README.md
[go-readme]: https://github.com/golang/go/blob/master/README.md
[kubernetes-readme]: https://github.com/kubernetes/kubernetes/blob/master/README.md
[electron-readme]: https://github.com/electron/electron/blob/main/README.md
[node-readme]: https://github.com/nodejs/node/blob/main/README.md
[rust-readme]: https://github.com/rust-lang/rust/blob/main/README.md
[axios-readme]: https://github.com/axios/axios/blob/v1.x/README.md
[deno-readme]: https://github.com/denoland/deno/blob/main/README.md
[redis-readme]: https://github.com/redis/redis/blob/unstable/README.md
[flask-readme]: https://github.com/pallets/flask/blob/main/README.md
[express-readme]: https://github.com/expressjs/express/blob/master/Readme.md
[ripgrep-readme]: https://github.com/BurntSushi/ripgrep/blob/master/README.md
[git-readme]: https://github.com/git/git/blob/master/README.md
[rails-readme]: https://github.com/rails/rails/blob/main/README.md
[requests-readme]: https://github.com/psf/requests/blob/main/README.md
