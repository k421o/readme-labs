---
name: modular-readme
description: Create or comprehensively refresh a repository README by selecting atomic modules, delegating independent components to one Codex subagent each, and validating and assembling isolated outputs. Use for multi-section README work; not for a small single-section edit.
---

# Modular README

Build a README from repository evidence without letting parallel workers edit the same file.

## Choose the route

- For one requested section, read its guide under `../../../modular-templates/modules/`, edit that section directly, and skip orchestration.
- For a new README or a multi-section refresh, use the parallel workflow below.
- Preserve a user's requested structure. Profiles are starting points, not mandatory schemas.

Before a parallel run, read [the component contract](references/component-contract.md) and [the parallel assembly guide](../../../modular-templates/PARALLEL-ASSEMBLY.md). Read individual module guides only for selected components.

## Prepare the run

Run helper commands from the template repository root.

1. Resolve the target repository and exact README path. Inspect existing instructions and uncommitted changes before writing.
2. Survey the repository once for its primary audience, supported setup path, public interfaces, governance files, license, and evidence sources.
3. List profiles and component IDs:

   ```bash
   python3 .agents/skills/modular-readme/scripts/readme_components.py list
   ```

4. Select only applicable components, then prepare an isolated run. Add conditional components explicitly.

   ```bash
   python3 .agents/skills/modular-readme/scripts/readme_components.py prepare \
     --run-id PROJECT-SLUG \
     --target-root /absolute/path/to/repository \
     --profile PROFILE \
     --include COMPONENT-ID
   ```

5. Read the guides for selected `derived` and `policy` components; worker packets already include every policy relevant to their fragments.
6. Complete the generated `shared-context.md` with verified cross-component facts and decisions before delegation. Do not use it for guesses.

## Delegate components

For every generated file in `briefs/`, start exactly one Codex subagent with that work packet as its prompt. Dispatch independent packets concurrently up to the host's concurrency limit; queue the remaining packets without combining their ownership. Wait for every worker before integration.

The parent agent owns the manifest, shared context, derived components, and final README. A worker owns only its named component and report paths. Do not let workers edit the target README, another component, shared context, or the manifest. If a worker is blocked or fails validation, steer that component's owner or replace that worker; do not have the parent silently invent missing project facts.

`repository-alias` extends the `project-title` packet, `relative-links` and `collapsible-details` are policies, and `table-of-contents` is derived from the completed headings. They do not receive competing worker files.

## Validate and assemble

Check progress, validate every ownership artifact, and build a preview:

```bash
python3 .agents/skills/modular-readme/scripts/readme_components.py status --run RUN-DIRECTORY
python3 .agents/skills/modular-readme/scripts/readme_components.py validate --run RUN-DIRECTORY
python3 .agents/skills/modular-readme/scripts/readme_components.py assemble --run RUN-DIRECTORY
```

Review the preview for cross-section consistency, reader flow, repeated claims, link targets, and exact commands. Run the target repository's Markdown, link, and example checks when available. Compare the preview with the exact destination, preserve unrelated edits, and replace the target README only when the user's request authorizes that write.

Do not publish placeholders, speculative commands, inferred support channels, or unverified legal claims. The deterministic checks are a floor; the parent remains responsible for factual and editorial integration.
