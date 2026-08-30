# README Labs

README Labs is the canonical domain repository for evidence, research, and
derived capabilities about README structure, authoring, and review. It treats
a README as an interface whose useful content depends on its delivery contract:
repository landing page, package metadata, registry surface, component
onboarding, experiment record, fixture explanation, or another evidenced use.

The repository currently publishes `readme-contract-review`, a skill that
checks README authority and claims against those concrete consumers. Research
under [`research/`](research/) supports the skill but is not loaded as skill
instruction.

## Use the skill

Install the `readme-labs` plugin from an immutable release with the plugin
workflow supported by your agent host, then invoke:

```text
Use $readme-labs:readme-contract-review to review this README's evidenced contract.
```

The skill is also available directly at
[`skills/readme-contract-review/SKILL.md`](skills/readme-contract-review/SKILL.md).
Downstream bundles should pin a README Labs release or commit; they should not
copy this editable skill tree.

## Scope

README Labs owns:

- README roles, vocabulary, evidence rules, and research;
- README-specific review and future authoring or classification projections;
- README-domain scenarios and corpus contracts as they are added; and
- evidence-backed releases of those capabilities.

It does not own generic repository guidance, `AGENTS.md` policy, downstream
plugin routing, or a shared evaluation platform. The originating
[`repository-guidance`](https://github.com/k421o/repository-guidance) plugin
owns its AGENTS.md capability, documentation-baseline workflow, and current
evaluation harness. The harness remains there until a second independent
domain proves a reusable contract.

Research manifests, labels, schemas, and reproducible acquisition rules should
remain here initially. Raw corpus data should separate only when storage,
licensing, privacy, access, refresh cadence, or independent consumers create a
different lifecycle.

## Research provenance

The initial work was produced in Codex session
`01a05036-1c5b-7db0-a9f8-508ea45aaa0f` on 2026-08-29
(America/New_York). It originated in repository-guidance
[PR #3](https://github.com/k421o/repository-guidance/pull/3) and
[draft PR #5](https://github.com/k421o/repository-guidance/pull/5). The
[extraction record](docs/migrations/2026-08-29-repository-guidance-extraction.md)
classifies the moved and retained artifacts and records the migration checks.

## Validate a change

```console
python3 tools/validate_repository.py
```

The deterministic check validates both plugin manifests, the skill entry
point, local Markdown links, and active checkout-path independence. Research
claims and external sources still require human review.
