# README roles

A README's role is the relationship between the document, its enclosing
component, and its expected reader. It is not reliably determined by filename
alone.

| Role ID | Description | Expected emphasis |
| --- | --- | --- |
| `repository_root` | Landing page for a single repository or source tree | Identity, purpose, first path, canonical routes, boundaries |
| `published_package` | Registry-facing or source-facing page for an installable library | Install, minimal use, API/configuration route, compatibility, license |
| `cli_tool` | Landing page for a command-line interface | Installation choices, command examples, configuration, observable behavior |
| `end_user_application` | Source or distribution page for an application | Product/source relationship, run or download path, visual behavior, support |
| `framework_or_platform` | Entry point for a multi-surface development system | Scope, mental model, user and developer starts, supported components |
| `source_distribution` | Source tree for a runtime, language, operating system, or similarly documentation-rich project | Canonical docs, supported releases, build, security, governance |
| `monorepo_root` | Entry point for multiple related components | System identity, component relationships, root bootstrap, categorized routing |
| `component` | README scoped to a package, service, module, or subtree inside a larger repository | Local contract, relationship to parent, component-specific start and boundaries |
| `experiment` | Research artifact, benchmark, or reproducibility package | Question, input provenance, method, reproduction, outputs, limitations, citation |
| `fixture_or_example` | Intentionally small or unusual subtree consumed by a test, tutorial, or tool | Why it exists, how it is consumed, intentional irregularities |
| `archive` | Archived, deprecated, or superseded project | Status first, replacement or migration route, maintenance and security boundary |
| `profile` | Person or organization profile rendered from a special README | Identity, scope, work or community routes; software launch categories may not apply |
| `unspecified` | Role has not been assigned with adequate evidence | Preserve uncertainty; do not silently apply root-project expectations |

## Assignment evidence

A role assignment should record one of three methods:

- `declared`: a collector or annotator supplied the role from known context;
- `inferred`: a documented deterministic rule assigned the role; or
- `annotated`: a human judgment assigned the role with a note or protocol.

Automatic collection should prefer `unspecified` over an unsupported semantic
guess. A root path named `README.md` is enough to infer `repository_root` only
when the collection unit is known to be a repository.

## Multiple roles

Some documents genuinely face more than one surface—for example, a repository
root README that is also rendered as an npm package page. Record the primary
role that determines the reader's opening path, then add secondary roles. An
evaluation must say which role its expectations address.
