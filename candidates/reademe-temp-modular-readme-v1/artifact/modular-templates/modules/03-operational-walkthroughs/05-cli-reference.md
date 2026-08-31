# Module: CLI Reference

| Field | Value |
| --- | --- |
| Output | A concise command synopsis and common operations |
| Default placement | After the usage quickstart |
| Applicability | Conditional; for projects with a command-line interface |
| Reader question | “Which command, argument, or flag do I need next?” |

## Purpose

Document the stable command surface readers need most often. Keep generated or exhaustive command help elsewhere when the interface is large.

## Inputs

- Executable name and canonical invocation.
- Stable commands, positional arguments, and global flags.
- One or two common examples.
- Full CLI reference or built-in help command.

## Template

````markdown
## CLI reference

```text
{{EXECUTABLE}} [GLOBAL_OPTIONS] <COMMAND> [ARGUMENTS]
```

| Command | Purpose |
| --- | --- |
| `{{EXECUTABLE}} {{COMMAND}}` | {{PURPOSE}} |
| `{{EXECUTABLE}} {{COMMAND}}` | {{PURPOSE}} |

Common options:

| Option | Value | Purpose |
| --- | --- | --- |
| `{{FLAG}}` | `{{VALUE_SHAPE}}` | {{PURPOSE}} |
| `{{FLAG}}` | — | {{PURPOSE}} |

Example:

```bash
{{EXECUTABLE}} {{COMMAND}} {{SAFE_ARGUMENTS}}
```

Run `{{EXECUTABLE}} --help` or see the [complete CLI reference]({{CLI_REFERENCE_PATH}}) for every command and option.
````

## Rules

- Match spelling, casing, defaults, and required arguments exactly.
- Distinguish global options from command-specific options.
- Use placeholders only in this authoring guide; final examples should contain safe realistic values.
- Avoid copying a huge generated help screen into the README.
- State exit-code or output contracts only when users rely on them.
- Link to shell-completion or environment-specific setup only when supported.

## Validation

- [ ] The synopsis parses under the current release.
- [ ] Listed commands and flags appear in built-in help.
- [ ] The example exits successfully in the stated environment.
- [ ] Defaults and value types match implementation.
- [ ] The full-reference path or help command is current.

## Assembly note

The usage module owns the first successful command. This module helps readers branch into additional commands without duplicating the full reference.
