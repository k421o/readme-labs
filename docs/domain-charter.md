# Domain charter

## Purpose

`readme-labs` studies how README files identify, orient, launch, route, bound,
and invite participation in software repositories and published components. It
turns those observations into explicit domain models, reproducible research,
evaluation methods, and optional derived capabilities.

The repository is domain-first. A skill, plugin, CLI, report, or dataset is a
consumer of the domain work rather than the reason every research decision is
made.

## Questions in scope

- What semantic roles do README files serve at repository, package, component,
  experiment, fixture, archive, and profile boundaries?
- Which information categories are common across repositories, and which are
  conditional on role or ecosystem?
- Which section orders and routing patterns are recognizable without becoming
  mandatory templates?
- Can a reader or agent identify the component and reach a first successful
  result using the README?
- Which commands, links, constraints, compatibility claims, and status claims
  are supported by the repository and its executable environment?
- How do README structures differ across roles, ecosystems, maturity, and time?
- Can evidence-backed review or authoring guidance improve outcomes without
  introducing generic prose or erasing necessary variation?
- Which parts of README evaluation can be deterministic, and which require
  blinded human judgment?
- How do agents interpret, navigate, and act on README content under realistic
  repository tasks?
- How do people understand, trust, navigate, and use README content, and which
  research methods can support those claims responsibly?
- Which outside research, methods, skills, plugins, tooling, automation,
  scripts, and complete solutions improve or challenge the current domain
  model and capability designs?

## Outputs

The domain may produce:

- Taxonomies and versioned observation schemas.
- Research findings with traceable sources and limitations.
- Corpus manifests, annotations, derived features, and statistical reports.
- Controlled fixtures, real-repository replays, mutations, and executable task
  capsules.
- Provenance-bearing intake records and isolated libraries of candidate skills,
  plugins, tooling, automation, scripts, bundles, methods, and whole-solution
  snapshots.
- Soft agent perspectives and privacy-bounded human/user-response observations.
- Review, authoring, classification, or navigation capabilities.
- Packaging adapters such as a Codex plugin.
- A generic evaluation component after non-README reuse demonstrates a stable
  extraction boundary.

## Non-goals

- Defining one universal README template.
- Treating stars, forks, age, length, badges, or training-data speculation as a
  quality score.
- Replacing canonical API, operations, security, contribution, or release
  documentation with an exhaustive root README.
- Turning human-facing README content into agent policy.
- Redistributing arbitrary public README text without provenance and license
  review.
- Claiming causal relationships from observational repository data.
- Making plugin packaging the repository's identity.

## Stable domain core

The stable middle of the project consists of:

1. A vocabulary for repository and document roles.
2. A semantic taxonomy for README information.
3. A captured README artifact model that separates immutable bytes, provenance,
   repository occurrence, collection purpose, lineage, and evidence.
4. `READMEObservation`, the structural interchange format between collectors,
   annotators, analyzers, evaluators, and capabilities.
5. Evidence and confidence rules.
6. Evaluation outcomes that distinguish structural, behavioral, and human
   judgments.

Collectors and consumers may change independently when they preserve these
contracts or version their changes. Experimental candidates are not required
to preserve the current contracts: they may challenge them, complete their
declared trials, and propose a versioned replacement.

## Evidence hierarchy

Evidence is interpreted by the claim it can support:

1. **Repository and executable evidence** supports claims about a specific
   component, command, path, package, or constraint.
2. **Official platform and ecosystem documentation** supports behavior of the
   platform or publication surface it governs.
3. **Empirical samples** support bounded prevalence and association claims when
   their selection, unit of analysis, and method are recorded.
4. **Maintained repositories** demonstrate possible and recognizable patterns;
   popularity does not make them normative.
5. **Public model-corpus documentation** can establish that a class of files is
   eligible or present, but not the contents or sampling weights of an
   undisclosed proprietary corpus.
6. **User preference and exploratory watchlists** identify candidates for
   review, not conclusions.

Every consequential finding should record its evidence class, collection date
or revision, and important limitations.

## Canonical ownership

`readme-labs` owns the editable README domain model and the canonical README
capabilities derived from it. Downstream bundles consume intentionally released
artifacts identified by version, source revision, and content hash.

Outside research and candidate copies remain evidence, not competing source
authority. Canonical ownership determines where an accepted change lands; it
does not make the current method, schema, directory layout, skill count, or
progressive-disclosure design immune from replacement.

`repository-guidance` continues to own AGENTS.md guidance and cross-surface
integration. It must not become a second editable home for the README domain.

Generic evaluation infrastructure remains incubated with the domain until a
second independent consumer proves the interface and justifies extraction.

## Change discipline

- Version schemas and taxonomies when a change can alter stored observations or
  their interpretation.
- Separate research conclusions from operational skill instructions.
- Add criteria to a capability only when observed behavior or evidence supports
  a recurring decision boundary.
- Admit structurally different candidates without requiring compatibility with
  the current capability or its regression tests.
- Let an admitted hypothesis complete its planned run unless a recorded safety,
  authorization, or infrastructure boundary makes the run incomplete.
- Treat automated experimental results and soft agent recommendations as
  evidence; reserve adoption, rejection, and promotion for owner or designated
  review after the declared run.
- Keep held-out evaluation material out of the agent-visible workspace.
- Record migrations and generated-product provenance.
- Use the complexity progression to decide when adapters, directories,
  releases, or repositories have earned their existence.
