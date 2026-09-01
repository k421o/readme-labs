# Candidate library

Candidates are first-class experimental treatments. A candidate may contain or
reference one skill, several skills, a plugin, tooling, automation, scripts, a
research method, a generated README workflow, or another complete design.

Every candidate has an immutable descriptor, source bindings, and either a
checked-in artifact tree or an external immutable reference. Checked-in
candidate trees are intentionally non-authoritative copies used for
experimentation. They must not be installed as the current README Labs product
or edited as a second canonical source.

Candidate validation checks identity, provenance, containment, and content
digests. It deliberately does not require the current `readme-review` file
layout, reference names, interface, skill count, or progressive-disclosure
shape.

## Review-skill trials

An embedded candidate with a `codex_skill` entrypoint can be exercised against
any held-out README review capsule:

```console
CODEX_HOME=/path/to/clean-disposable-codex-home \
  uv run readme-lab candidate review-trial candidate.json \
  --capsule ../evals/scenarios/missing-first-path/capsule.toml \
  --workspace /tmp/readme-candidate-workspace \
  --run-dir /tmp/readme-candidate-run \
  --run-id candidate-finding \
  --model gpt-5.6-terra
```

The runner verifies the descriptor and tree, materializes an isolated Git
subject, stages exactly one repository-local candidate skill outside the
visible subject status, and refuses ambient skills, plugin caches, or
marketplaces in `CODEX_HOME`. It supports explicit invocation and discovery
trials. It records subject and treatment hashes before and after execution;
the held-out score remains evidence only.

Plugin, tooling, automation, and script candidates can be admitted and tested
through appropriate experiment methods. This runner executes only a
`codex_skill` entrypoint, including one exposed by a larger plugin candidate.
Write-producing candidate execution still requires a lifetime-owned isolation
backend that can prove no descendant retains access to the mutable workspace.
That experiment boundary remains tracked in
[issue #14](https://github.com/k421o/readme-labs/issues/14); it does not block
the canonical `readme-generate` capability's owner-authorized repository work.
