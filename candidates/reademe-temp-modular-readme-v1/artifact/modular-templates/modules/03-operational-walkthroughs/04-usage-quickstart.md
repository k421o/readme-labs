# Module: Usage / Quickstart

| Field | Value |
| --- | --- |
| Output | One minimal, verified path to a meaningful result |
| Default placement | After installation and configuration |
| Applicability | Required |
| Reader question | “What is the smallest real thing I can do successfully?” |

## Purpose

Turn a correctly installed project into an observable result. The example should expose the project's core interface without requiring readers to infer missing imports, files, or arguments.

## Inputs

- The exact command or code needed for the primary path.
- Required working directory and input fixture.
- A stable description of expected output.
- The next deeper guide for readers who succeed.

## CLI template

````markdown
## Usage

Run the smallest complete example from the repository root:

```bash
{{COMMAND}} {{ARGUMENTS}}
```

You should see {{EXPECTED_RESULT}}.

For additional workflows, see the [usage guide]({{USAGE_GUIDE_PATH}}).
````

## Library variant

Replace the CLI block with a complete program in the project's language:

````markdown
## Usage

```{{LANGUAGE}}
{{IMPORTS}}

{{MINIMAL_WORKING_EXAMPLE}}
```

The example produces {{EXPECTED_RESULT}}. See the [usage guide]({{USAGE_GUIDE_PATH}}) for additional workflows.
````

## Rules

- Choose one primary example; do not make readers combine fragments.
- Include imports, initialization, and execution for library code.
- Use values safe to copy and run.
- State the working directory when commands depend on it.
- Prefer five to fifteen meaningful lines; move elaborate scenarios to a guide or example directory.
- Keep expected output descriptive unless exact text is part of the public contract.
- Test fenced examples in CI when the ecosystem supports it.

## Validation

- [ ] A newly installed user can run the example without undocumented steps.
- [ ] Imports, commands, flags, and return shapes match the current release.
- [ ] The example demonstrates the project's primary value.
- [ ] Sample data contains no secrets or environment-specific paths.
- [ ] The next-step link resolves when retained.

## Assembly note

Use either the CLI or library variant, not both unless the project genuinely serves both interfaces. A tiny preview can precede installation; keep the full quickstart in one place.
