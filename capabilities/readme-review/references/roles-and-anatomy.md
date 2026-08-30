# Roles and anatomy

Use roles to establish context, not to force a repository into one template.

## Stable README jobs

| Job | Reader question |
| --- | --- |
| Identify | What is this? |
| Qualify | Is it for me? |
| Launch | How do I reach one useful result? |
| Route | Where is the rest? |
| Bound | What must I not assume? |
| Invite | How do I participate or attribute it? |

## Primary roles

- **Repository root:** identity, purpose, first path, canonical routes, and
  boundaries for a source repository.
- **Published package:** installation, minimal use, API/configuration route,
  compatibility, and license on repository and registry surfaces.
- **CLI tool:** installation choices, command examples, configuration, and
  observable command behavior.
- **End-user application:** product/source relationship, download or run path,
  visual behavior where relevant, and support.
- **Framework or platform:** scope, mental model, separate user and developer
  starts, supported components, and community/governance routes.
- **Source distribution:** canonical docs, supported releases, build, security,
  contribution, and governance; a short root router can be correct.
- **Monorepo root:** system identity, component relationships, root bootstrap,
  and categorized routes to component contracts.
- **Component:** local contract, relationship to the parent, component-specific
  start, and boundaries.
- **Experiment:** question, input provenance, method, exact reproduction,
  outputs, dated limitations, and citation.
- **Fixture or example:** why files are unusual, how the parent consumes them,
  and which irregularities are intentional.
- **Archive:** status first, replacement or migration route, and maintenance or
  security boundary.
- **Profile:** person or organization identity and relevant work or community
  routes; software launch categories may not apply.

Use `unspecified` when evidence does not support a role assignment. A README can
have secondary roles, such as a repository root also rendered on a package
registry.

## Conventional semantic spine

Consider these questions in reader order, then omit, combine, or route them when
the component makes that appropriate:

1. identity;
2. factual definition and purpose;
3. decision-relevant status metadata;
4. first successful path;
5. minimal use with expected behavior;
6. documentation, API, configuration, options, or examples;
7. consequential boundaries;
8. development and participation;
9. help, community, governance, or project structure; and
10. legal and provenance.

The opening should normally establish identity, orientation, and a first route
to success before sponsor, governance, history, or contributor depth. This is a
recognizable default, not a section checklist.

Canonical source: `domain/repository-roles.md` and `domain/taxonomy-v1.json` in
`k421o/readme-labs`.
