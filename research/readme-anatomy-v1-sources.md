# README anatomy, version 1: source list

Research snapshot: 2026-08-29

This is the expanded source companion to
[`readme-anatomy-v1.md`](readme-anatomy-v1.md). It separates normative
standards, platform behavior, empirical research, public training-corpus
evidence, and repository examples so that each kind of source is used only for
the claims it can support.

The standards and platform documents below are authoritative for their own
ecosystems. Repository READMEs are primary examples of maintained practice, not
universal requirements. Popularity, age, stars, forks, mirrors, and registry
publication are exposure proxies; they are not file-level model-training
counts.

## Repository and hosting platforms

- [GitHub: About the repository README file](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
  — Defines the familiar reader questions: what the project does, why it is
  useful, how to get started, where to get help, and who maintains or
  contributes. Also documents automatic repository-page display, generated
  outlines, relative links, and the recommendation to move longer material to
  dedicated documentation.
- [GitHub REST API: Get a repository README](https://docs.github.com/en/rest/repos/contents#get-a-repository-readme)
  — Documents how the preferred README and its raw or rendered contents were
  retrieved for the repository audit.
- [GitLab: Manage projects](https://docs.gitlab.com/user/project/working_with_projects/)
  — Confirms that a README or index file is part of the project overview.
- [GitLab: README and index files](https://docs.gitlab.com/user/project/repository/files/#readme-and-index-files)
  — Documents automatic rendering in repository directories and the precedence
  of previewable markup files such as `README.md` over plain text.

## Long-standing distribution and foundation conventions

- [GNU Coding Standards: Making Releases](https://www.gnu.org/prep/standards/standards.html#Making-Releases)
  — The strongest traditional normative anatomy found. A distribution README
  should give the package name and version, a general description, an
  installation reference, only unusual top-level orientation, and a reference
  to copying conditions.
- [GNU Automake manual: Strictness](https://www.gnu.org/software/automake/manual/html_node/Strictness.html)
  — Treats `README` as one of the standard top-level files required under GNU
  strictness.
- [GNU Automake manual: What Goes in a Distribution](https://www.gnu.org/software/automake/manual/html_node/Basics-of-Distribution.html)
  — Documents automatic distribution of `README` and `README.md`, reinforcing
  that the README is part of a release artifact rather than only a web page.
- [CNCF project README template](https://github.com/cncf/project-template/blob/main/README-template.md)
  — A foundation-maintained template for mature community projects. Its
  categories are identity and value, getting started, contributing, scope,
  communications, resources, license, and conduct.
- [CNCF project templates and resources](https://contribute.cncf.io/projects/best-practices/templates/)
  — Establishes the template's role in CNCF project setup and places the README
  alongside dedicated contribution, governance, maintainer, review, security,
  and conduct documents.
- [CNCF project guideposts](https://github.com/cncf/toc/blob/main/resources/project_guideposts.md)
  — Connects mature project documentation with getting started, operations,
  administration, security call-outs, and discoverable community information.
- [Apache Software Foundation release policy](https://www.apache.org/legal/release-policy.html)
  — Useful boundary evidence: a source release must be sufficient to build and
  test, while license and notice documents remain distinct required artifacts.
- [Apache release distribution policy](https://infra.apache.org/release-distribution.html)
  — Recognizes README and change documents as material that may describe
  distributed release content without replacing the formal release artifacts.

## Python standards and maintained guidance

- [PEP 621: `readme` project metadata](https://peps.python.org/pep-0621/#readme)
  — Defines the README as the project's full package description and specifies
  how `.md` and `.rst` paths imply their content types. It does not prescribe
  README headings or section order.
- [Python Packaging User Guide: `pyproject.toml` `readme`](https://packaging.python.org/en/latest/specifications/pyproject-toml/#readme)
  — The current packaging specification corresponding to PEP 621.
- [PEP 566: Metadata for Python Software Packages 2.1](https://peps.python.org/pep-0566/)
  — Introduced `Description-Content-Type`, allowing package indexes to render
  Markdown descriptions intentionally rather than treating them as malformed
  reStructuredText.
- [Python core metadata: `Summary`, `Description`, and `Description-Content-Type`](https://packaging.python.org/en/latest/specifications/core-metadata/)
  — The current canonical specification. It distinguishes a one-line summary
  from a longer description, recognizes GFM and CommonMark, and cautions that
  the description should not become the complete instruction manual.
- [PyPA: Making a PyPI-friendly README](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/)
  — Documents conventional root placement, supported renderers, use of the
  README as the PyPI description, and built-distribution validation with
  `twine check`.
- [CPython `README.rst`](https://github.com/python/cpython/blob/main/README.rst)
  — A maintained source-distribution example organized around general
  information, contributing, ordinary use, source building, release changes,
  documentation, testing, multiple-version installation, schedule, and legal
  information.
- [Python Developer's Guide: Setup and building](https://devguide.python.org/setup/)
  — The canonical deeper contributor surface to which CPython can route detailed
  checkout, build, and environment instructions.

## Package registry conventions

- [npm: About package README files](https://docs.npmjs.com/about-package-readme-files/)
  — Recommends a package-root `README.md`, identifies installation,
  configuration, and usage as normal contents, and renders it on the npm
  package page.
- [npm: `package.json` files](https://docs.npmjs.com/cli/latest/configuring-npm/package-json#files)
  — Documents that README and license files are included in published packages
  regardless of the package's `files` selection.
- [Cargo Book: The `readme` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-readme-field)
  — Transfers the package-root README to the registry and renders it on
  crates.io; also documents automatic discovery of common README filenames.
- [NuGet: Package README on NuGet.org](https://learn.microsoft.com/en-us/nuget/nuget-org/package-readme-on-nuget-org)
  — Provides the clearest official modern content template found: package
  introduction and problem, getting started, conditional prerequisites, usage
  examples, additional documentation, feedback, and contribution.
- [NuGet package authoring best practices](https://learn.microsoft.com/en-us/nuget/create-packages/package-authoring-best-practices#readme)
  — Recommends an embedded Markdown README that explains what a package does
  and how to get started.

## Community README specification

- [Standard Readme specification](https://github.com/RichardLitt/standard-readme/blob/main/spec.md)
  — A detailed community convention for open-source libraries. It supplies a
  useful conventional sequence—title, description, install, usage, optional
  API and project sections, contribution, and license—but is not authoritative
  across every repository role.

## Empirical README research

- [Prana et al., *Categorizing the Content of GitHub README Files*](https://arxiv.org/abs/1802.06997)
  — Manual annotation of 4,226 sections from 393 randomly sampled GitHub
  READMEs. Provides file-level prevalence for What, How, References, Who,
  Contribution, Why, and When/status categories.
- [Ikeda et al., *An Empirical Study on README Contents for JavaScript Packages*](https://arxiv.org/abs/1802.08391)
  — Analysis of 43,911 filtered JavaScript package READMEs. Provides prevalence
  for heading-derived themes including Usage, Install, License, API, Options,
  Release history, Contribute, and Test.
- [Venigalla and Chimalakonda, *An Empirical Study on Correlation between README Content and Project Popularity*](https://arxiv.org/abs/2206.10772)
  — Study of 1,950 READMEs across ten programming languages. Supports
  association—not causation—between repository popularity and references,
  contribution information, links, lists, and images.

## Public code-training corpus evidence

- [The Stack dataset card](https://huggingface.co/datasets/bigcode/the-stack/blob/main/README.md)
  — Explicitly lists Markdown among the included languages and represents
  content as individual repository files.
- [Kocetkov et al., *The Stack: 3 TB of Permissively Licensed Source Code*](https://arxiv.org/abs/2211.15533)
  — Describes the GitHub-derived corpus and reports the use and effect of
  near-deduplication.
- [The Stack v2 dataset card](https://huggingface.co/datasets/bigcode/the-stack-v2-train-full-ids/blob/main/README.md)
  — Reports 3.28 billion unique files from 104.2 million repositories and that
  roughly 40 percent of permissively licensed files were exact or near
  duplicates during preprocessing.

These sources establish that Markdown repository files can occur in documented
code-model corpora. They do not identify the training inventory or sampling
weight of a current proprietary model and do not support ranking individual
READMEs by training frequency.

## Established system and source-distribution examples

- [Linux kernel top-level `README`](https://github.com/torvalds/linux/blob/master/README)
  — A long-lived source-distribution entry point rather than a package-registry
  landing page.
- [Linux kernel development HOWTO](https://kernel.org/doc/html/next/process/howto.html)
  — Explicitly identifies `Documentation/admin-guide/README.rst` as the starting
  point for background, configuration, and building, while routing patch,
  style, dependency, and security work to dedicated documents.
- [Linux kernel administrator README](https://github.com/torvalds/linux/blob/master/Documentation/admin-guide/README.rst)
  — Detailed requirements, configuration, compilation, and installation for a
  complex source tree.
- [systemd repository landing README](https://github.com/systemd/systemd/blob/main/README.md)
  — A concise routing surface for documentation, code map, hacking,
  contribution, support, stable branches, and security.
- [systemd build and runtime README](https://github.com/systemd/systemd/blob/main/README)
  — Complements the web-facing README with detailed build requirements and
  operating-system integration constraints.
- [curl top-level README](https://github.com/curl/curl/blob/master/README)
  — A compact router that distinguishes the CLI and library, then points to
  their manuals, installation, FAQ, license, contact, website, source, and
  private security reporting.
- [curl installation guide](https://github.com/curl/curl/blob/master/docs/INSTALL.md)
  — Demonstrates how build-system and platform detail can remain canonical
  outside the root README.
- [PostgreSQL `README.md`](https://github.com/postgres/postgres/blob/master/README.md)
  — A very short source-distribution README: identity, capability summary,
  copyright, canonical documentation, source-build instructions, downloads,
  and website.
- [LLVM project README](https://github.com/llvm/llvm-project/blob/main/README.md)
  — A monorepo landing page that explains the system and major components, then
  routes build and contribution work to maintained guides.
- [Rust compiler and standard library README](https://github.com/rust-lang/rust/blob/main/README.md)
  — Repository identity, Why Rust, quick start, explicit source-install
  distinction, help, contribution, license, and trademark boundaries.
- [Git source README](https://github.com/git/git/blob/master/README.md)
  — A historically prominent source-tree README whose role and style differ
  markedly from a modern package page.

## High-exposure application, framework, library, and CLI examples

- [React](https://github.com/react/react/blob/main/README.md)
- [TensorFlow](https://github.com/tensorflow/tensorflow/blob/master/README.md)
- [Visual Studio Code](https://github.com/microsoft/vscode/blob/main/README.md)
- [Go](https://github.com/golang/go/blob/master/README.md)
- [Kubernetes](https://github.com/kubernetes/kubernetes/blob/master/README.md)
- [Electron](https://github.com/electron/electron/blob/main/README.md)
- [Node.js](https://github.com/nodejs/node/blob/main/README.md)
- [Axios](https://github.com/axios/axios/blob/v1.x/README.md)
- [Deno](https://github.com/denoland/deno/blob/main/README.md)
- [Redis](https://github.com/redis/redis/blob/unstable/README.md)
- [Flask](https://github.com/pallets/flask/blob/main/README.md)
- [Express](https://github.com/expressjs/express/blob/master/Readme.md)
- [ripgrep](https://github.com/BurntSushi/ripgrep/blob/master/README.md)
- [Rails](https://github.com/rails/rails/blob/main/README.md)
- [Requests](https://github.com/psf/requests/blob/main/README.md)

This last group is evidence of recognizable real-world shapes and variation,
not an endorsement of every section or ordering choice in every current file.
