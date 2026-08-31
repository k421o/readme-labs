# Evaluation lab

The evaluation lab tests README-facing capabilities against controlled tasks
without confusing a Markdown fixture with a real repository.

These task capsules protect and measure the released `readme-review` job and
provide held-out repository subjects for experimental candidate review.
Open-ended candidate inquiry lives under `experiments/`. Failure against a
capsule may diagnose compatibility with this job, but it does not prevent a
structurally different candidate from completing its own plan.

## Fidelity ladder

1. **Static fixture** — parser and schema behavior.
2. **Snapshot** — files captured at a pinned source revision.
3. **Mutated snapshot** — one documented defect introduced into a snapshot.
4. **Local Git repository** — a task receives an isolated repository with
   history, paths, manifests, tests, and no scorecard in its workspace.
5. **Container replay** — a pinned toolchain executes build or usage claims.
6. **Remote replay** — disposable hosted infrastructure exercises integration
   behavior under explicit network policy.

The initial scenarios use level 4. This catches repository discovery and
evidence-checking behavior while remaining deterministic and inexpensive.

## Task capsules

Each scenario contains:

- `capsule.toml`: task, environment, fixture, mutation, and held-out scorecard
  location;
- `fixture/`: the only source files copied into the simulated repository;
- `mutation.diff`: an optional single controlled change applied after the base
  fixture commit; and
- `scorecard.json`: expected findings kept outside the simulated repository.

The contract is [`task-capsule-v1.schema.json`](task-capsule-v1.schema.json).
Materialize a scenario with:

```console
uv run readme-lab capsule materialize \
  evals/scenarios/missing-first-path/capsule.toml \
  --destination /tmp/readme-labs-missing-first-path
```

The result is an actual temporary Git repository with separate base and
mutation commits. The blinded runner launches Codex inside it and reads the
held-out scorecard only after the executor exits:

```console
CODEX_HOME=/path/to/disposable-authenticated-codex-home \
  uv run readme-lab capsule run \
  evals/scenarios/missing-first-path/capsule.toml \
  --workspace /tmp/readme-labs-missing-first-path \
  --run-dir /tmp/readme-labs-missing-first-path-run \
  --run-id example-finding-run \
  --artifact-revision <full-40-character-revision> \
  --model gpt-5.6-terra \
  --reasoning-effort high
```

The disposable Codex home must already contain an enabled
`readme-labs@readme-labs` plugin installed from the exact revision supplied to
`--artifact-revision`. The runner records and checks that inventory; the
argument is provenance, not an installation shortcut.

An experimental embedded Codex-skill candidate uses the same blinded capsule
without an installed plugin:

```console
CODEX_HOME=/path/to/clean-disposable-codex-home \
  uv run readme-lab candidate review-trial \
  candidates/example/candidate.json \
  --capsule evals/scenarios/missing-first-path/capsule.toml \
  --workspace /tmp/readme-candidate-workspace \
  --run-dir /tmp/readme-candidate-run \
  --run-id example-candidate-run \
  --model gpt-5.6-terra
```

Candidate mode refuses ambient skills and marketplaces, stages exactly one
verified repository-local skill, and records the automatic result separately
as evidence. It cannot reject the candidate or decide hypothesis truth.

The runner enforces the capsule's network policy, denies command access to the
factory checkout, verifies that boundary before inference, captures structured
Codex events and stderr, and performs deterministic scoring after exit. The
first
[`bootstrap-readme-review-v1`](runs/bootstrap-readme-review-v1/) run is an
explicitly non-blinded author dry run: it verifies materialization, repository
evidence, response capture, and score plumbing, but is not evidence that the
capability improves performance.

Codex `exec --json` currently omits the exact command when the command sandbox
denies a tool call. The runner preserves this limitation: it may correlate one
reported failed command with one unattributed stderr sandbox violation, labels
that evidence as unattributed, and requires independent semantic review. It
never rewrites the denial as an exact command event.

## Evaluation boundaries

- A scenario must name its fidelity level and network policy.
- A mutation changes one evaluation variable whenever practical.
- Expected findings identify evidence and a success condition; they do not
  require exact prose.
- Fixture correctness is tested before a mutated scenario is admitted.
- Agent prompts and model settings belong in run records, not in a scorecard.
- Human judgments should be blinded to treatment and report agreement.
- Automatic category matching is a gate, not a semantic judgment; an
  independent reviewer checks evidence, anti-findings, and unexpected claims.
- Automatic gates apply to the release or regression contract that names them,
  never to candidate admission or hypothesis truth.

See the [factory runbook](../docs/factory-runbook.md) for installation,
evaluation, packaging, and rollback commands. Material failures and their
dispositions are recorded in
[`failure-dispositions-v0.2.0.md`](failure-dispositions-v0.2.0.md).
