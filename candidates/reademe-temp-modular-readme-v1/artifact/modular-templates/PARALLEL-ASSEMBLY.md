# Parallel README Assembly with Codex

Use this workflow when several README components can be researched and authored independently. The repository-local `$modular-readme` skill turns the existing module catalog into isolated Codex work packets, so section agents never compete over `README.md`.

## Ownership model

```text
parent agent
|-- selects components and records shared facts
|-- dispatches one work packet per independent component
|   |-- worker: project-title
|   |-- worker: short-description
|   |-- worker: installation
|   `-- worker: usage-quickstart
|-- waits for all workers
|-- validates fragments and evidence reports
`-- assembles and reviews one README preview
```

Every worker writes a unique Markdown fragment and JSON evidence report. Only the parent handles the manifest, shared context, derived content, cross-section review, and target README.

## Component modes

Most content modules are `worker` components and receive one agent each. Three other modes prevent merge conflicts or premature work:

| Mode | Examples | Handling |
| --- | --- | --- |
| `worker` | Installation, usage, API, security | One agent writes one isolated fragment and report. |
| `owner-extension` | Repository alias | Its rules are included in the project-title packet. |
| `policy` | Relative links, collapsible details | Relevant agents apply the pattern; no standalone fragment is emitted. |
| `derived` | Table of contents | The assembler generates it from finalized `H2` headings. |

This still gives every independently authorable component a focusable owner. Components whose output depends on another component stay with that owner or the integration step.

## Run the workflow

From this repository root, inspect the available profiles and components:

```bash
python3 .agents/skills/modular-readme/scripts/readme_components.py list
```

Prepare a run from a profile, adding or removing components based on repository evidence:

```bash
python3 .agents/skills/modular-readme/scripts/readme_components.py prepare \
  --run-id example-project \
  --target-root /absolute/path/to/example-project \
  --profile reusable-library \
  --include table-of-contents \
  --include license
```

The command creates an ignored run directory inside the local skill. Before spawning workers, the parent completes `shared-context.md` with canonical names, audience, terminology, paths, commands, and known gaps. Each file in `briefs/` is a complete prompt for one component agent.

Dispatch as many packets concurrently as the Codex host permits. When the selected component count exceeds the concurrency limit, keep one-agent-per-component ownership and start the remaining packets as slots become available. Do not group components merely to fit one wave.

## Integrate results

After all workers finish:

```bash
python3 .agents/skills/modular-readme/scripts/readme_components.py status --run RUN-DIRECTORY
python3 .agents/skills/modular-readme/scripts/readme_components.py validate --run RUN-DIRECTORY
python3 .agents/skills/modular-readme/scripts/readme_components.py assemble --run RUN-DIRECTORY
```

Validation rejects incomplete shared context, missing or blocked reports, unverified claims, unresolved placeholders, heading ownership violations, unlabeled code fences, machine-specific paths, and invalid final structure. Assembly writes `assembled/README.md` inside the run directory by default; it does not overwrite the target README.

The parent then reviews the preview as a whole. Check vocabulary, duplicate explanations, reader flow, cross-links, commands, paths, support and security routes, license accuracy, and target-renderer anchors. Use the target repository's lint, link, and executable-example checks before replacing its README.

## Conflict and retry rules

- A worker never edits `README.md`, the manifest, shared context, or another worker's files.
- The parent does not edit worker files while agents are active.
- A factual gap produces a blocked report instead of plausible filler.
- A failed component returns to its original owner through a focused follow-up; unrelated components remain complete.
- The final README is a reviewed deliverable, not a raw concatenation of agent prose.

For the exact artifact schema, read [the skill's component contract](../.agents/skills/modular-readme/references/component-contract.md).

## Codex basis

This layout follows official OpenAI guidance: repository-scoped skills are discovered under [`.agents/skills`](https://learn.chatgpt.com/docs/build-skills), and applicable skill instructions can request [parallel Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents). The isolated-file contract addresses the same guidance's caution that concurrent write-heavy work creates conflicts and coordination overhead.
