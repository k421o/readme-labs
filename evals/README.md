# Evaluation lab

The evaluation lab tests README-facing capabilities against controlled tasks
without confusing a Markdown fixture with a real repository.

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
mutation commits. A future runner can launch agents inside it and score their
structured findings without exposing the scorecard.

## Evaluation boundaries

- A scenario must name its fidelity level and network policy.
- A mutation changes one evaluation variable whenever practical.
- Expected findings identify evidence and a success condition; they do not
  require exact prose.
- Fixture correctness is tested before a mutated scenario is admitted.
- Agent prompts and model settings belong in run records, not in a scorecard.
- Human judgments should be blinded to treatment and report agreement.
