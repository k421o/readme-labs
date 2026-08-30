# Corpus sampling plan, version 1

## Research questions

The corpus should eventually support four distinct questions:

1. How prevalent are semantic README categories within a defined public
   repository population?
2. How do structures differ by README role, ecosystem, repository age, and
   exposure?
3. Which patterns recur in unusually visible repositories that readers and
   agents are likely to have encountered?
4. Which structures or omissions predict task outcomes under controlled
   evaluation?

No single sample answers all four.

## Units

- **Collection unit:** one README-like document at one repository revision and
  path.
- **Repository unit:** a source repository, retained for clustered analyses.
- **Longitudinal unit:** the same path observed at two or more pinned revisions.
- **Evaluation unit:** one agent or human response to one task capsule.

Nested README files are not independent observations when they share a
repository. Analyses must account for clustering or operate explicitly at the
repository level.

## Sampling frames

### Prevalence frame

Build a reproducible population of public, non-fork repositories meeting a
declared activity and size window. Sample probabilistically, then stratify by
ecosystem, repository age, exposure band, and observed README role. Record the
query date, exclusions, non-response, and duplicate removal. This is the frame
for prevalence estimates and confidence intervals.

### High-exposure frame

Purposively select long-lived, highly starred, highly forked, mirrored, or
package-visible repositories across ecosystems. This frame finds recognizable
patterns and valuable counterexamples. It cannot estimate prevalence, quality,
or proprietary training weights.

The initial 16-document pilot belongs here. Stars and forks are captured as
selection metadata at collection time, not as outcome variables or quality
labels.

### Role and edge-case frame

Deliberately recruit package, CLI, application, monorepo, experiment, fixture,
archive, component, and profile READMEs. This frame tests whether the taxonomy
and capabilities preserve legitimate variation that a popularity sample would
miss.

### Evaluation frame

Select or construct repositories with evidence-backed tasks, controlled
mutations, and held-out scorecards. Use this frame for causal comparisons of
capabilities; do not infer causal effects from the observational corpus.

## Training-data prevalence

Exact prevalence in a proprietary model's training mix is ordinarily not
observable. Public corpus documentation may establish that public source code
or README-like files were eligible, but it usually does not expose file-level
membership, sampling weights, deduplication, filtering, or training influence.

Accordingly, analyses keep three claims separate:

- **document prevalence:** measured from a defined public sample;
- **public exposure:** proxied by repository age, stars, forks, package or
  platform rendering, mirrors, and discoverability; and
- **model familiarity:** measured behaviorally with held-out recognition or
  task experiments, not inferred from stars.

The phrase “highest training-data prevalence” should be reported as a proxy or
experimental result unless file-level corpus evidence is actually available.

## Collection and derivation

1. Pin repository revision, path, blob SHA, branch, license signal, and
   selection metadata in a manifest.
2. Fetch the raw document into an external cache and verify the Git blob SHA.
3. Emit `READMEObservation` using a pinned taxonomy and parser version.
4. Add human role or semantic annotations under a documented protocol.
5. Preserve raw and derived version identifiers in every analysis.
6. Publish aggregate results with sample counts, uncertainty, missingness, and
   sensitivity checks.

## Initial analyses

- Category-signal prevalence with Wilson or bootstrap intervals.
- Heading order and transition frequencies.
- Document length, heading depth, code block, and link distributions.
- Differences by role and ecosystem, reported with counts and uncertainty.
- Co-occurrence clusters without interpreting clusters as recommended
  templates.
- Longitudinal transitions around major releases, archival, or repository
  restructuring.
- Association between structural signals and evaluation outcomes, clearly
  labeled observational unless assigned experimentally.

## Bias and quality controls

- Deduplicate mirrors and near-identical generated READMEs.
- Record inaccessible, deleted, binary, non-UTF-8, and language-excluded cases.
- Separate repository license metadata from permission to redistribute a
  particular file.
- Measure annotation agreement and adjudicate role disagreements.
- Keep taxonomy development examples separate from held-out evaluation cases.
- Repeat results with and without extreme exposure values and very large
  documents.
- Never silently replace a pinned revision with current default-branch content.
