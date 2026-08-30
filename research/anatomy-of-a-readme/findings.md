# Anatomy of a README: contract-specific findings

Status: initial research, 2026-08-29. A README is an interface whose useful
contents follow from its delivery contract; the evidence does not support a
single universal section checklist.

## 1. Repository landing page

**Contract.** The file is the first orientation page for repository visitors.
GitHub automatically surfaces a README from `.github`, the repository root, or
`docs` (in that order). GitHub says the common questions are what the project
does, why it is useful, how to start, where to get help, and who maintains or
contributes. Keep the fast path here; move longer material to focused docs.
[GitHub: About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)

**Useful components when applicable.** A one-sentence purpose and audience;
a minimal, runnable getting-started path; help/support and maintainer links;
and links to deeper documentation. Use relative links for repository-local
targets: GitHub recommends them because they continue to work in clones and
branches. Contribution process belongs in `CONTRIBUTING`, which GitHub surfaces
at issue/PR time, rather than being duplicated in full here.
[GitHub: Relative links](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
[GitHub: Contributor guidelines](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)

## 2. Published package page / distribution metadata

**Contract.** The README is rendered to prospective package users and/or
becomes package metadata, so accuracy under the registry renderer and released
artifact matters as much as repository readability.

**Useful components when applicable.** The exact install command, required
configuration, a smallest viable use example, compatibility/requirements, and
links to API/reference documentation. npm recommends install, configuration,
and use directions; it renders a package-root README on the package page, and
a README change reaches that page only through a new package version.
[npm: Package README files](https://docs.npmjs.com/about-package-readme-files/)

For Python projects, `project.readme` is the distribution's full description;
a `.md` filename selects `text/markdown`, so deleting or moving its source is a
packaging-interface change. Cargo likewise transfers the configured package
README to the registry and crates.io renders it as Markdown.
[PyPA: `pyproject.toml` `readme`](https://packaging.python.org/en/latest/specifications/pyproject-toml/#readme)
[Cargo: `readme` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-readme-field)

## 3. Component or subdirectory onboarding

**Contract.** A nearby README is a local handoff for someone about to change,
run, or integrate that component. It is not automatically equivalent to the
repository landing page: GitHub's documented automatic repository placement is
limited to `.github`, root, and `docs`.
[GitHub: README discovery locations](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)

**Useful components when applicable.** Scope/boundary (what this directory
owns), local prerequisites, exact commands and expected outcome, key inputs and
outputs, and a pointer to the parent or canonical design documentation. Include
only decisions a reader needs before acting; link to shared setup rather than
copying it. Treat this contract as evidenced by navigation links, local tools,
or an explicit project convention—not merely by the filename.

## 4. Experiment, prototype, or reproducibility record

**Contract.** The file preserves enough context to rerun, inspect, or correctly
interpret a bounded result—not to serve as a general product introduction.

**Useful components when applicable.** Question/hypothesis and status; dataset
or input identity and provenance; the exact environment, command, and fixed
configuration; result/metric plus where artifacts live; and limitations or
known deviations. This matches NIST's guidance to track and document
experiments and results, environment/dependencies, models/artifacts, parameters,
and data management; MLflow's experiment-tracking documentation independently
models a run with parameters, code versions, metrics, and output artifacts.
[NIST: Generative AI Profile (PDF)](https://airc.nist.gov/docs/NIST.AI.600-1.GenAI-Profile.ipd.pdf)
[MLflow: experiment tracking](https://mlflow.org/docs/latest/ml/tracking/)

## Review rule

First identify which contract has evidence in the repository or publishing
configuration. Then retain, add, or remove sections only when they help the
contract's reader complete a concrete next action. A README may satisfy more
than one contract, but package metadata, rendered-size limits, and registry
publication rules remain constraints; GitHub truncates rendered README content
beyond 500 KiB.
[GitHub: rendered README limit](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
