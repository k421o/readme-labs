# Module: Installation

| Field | Value |
| --- | --- |
| Output | The shortest supported path from prerequisites to installed software |
| Default placement | Before configuration and full usage |
| Applicability | Required for installable projects |
| Reader question | “How do I install this correctly?” |

## Purpose

Provide one authoritative, copy-pasteable installation path. Secondary package managers or source-build paths should appear only when they are actively supported.

## Inputs

- `{{INSTALL_COMMAND}}`: exact recommended install command.
- `{{VERIFY_COMMAND}}`: command that proves installation succeeded.
- `{{EXPECTED_VERSION_SHAPE}}`: a recognizable result, not a brittle full output dump.
- Optional platform or source-build guide paths.

## Template

````markdown
## Installation

Install the latest supported release:

```bash
{{INSTALL_COMMAND}}
```

Verify the installation:

```bash
{{VERIFY_COMMAND}}
```

The command should report a version in the form `{{EXPECTED_VERSION_SHAPE}}`.
````

## Optional supported variants

Add a variant only when the project tests and maintains it:

```markdown
### Install from source

For an editable development installation, follow the [contribution setup](CONTRIBUTING.md#development-setup).
```

## Rules

- Put the recommended path first and label alternatives.
- State the directory from which a command must run when it is not obvious.
- Pin a version only when reproducibility or compatibility requires it; otherwise describe the supported range.
- Keep development setup in `CONTRIBUTING.md` unless end users also need it.
- Never put secrets in install commands.
- Avoid `curl | sh` examples unless the project owns, secures, and explains that path.

## Validation

- [ ] A clean supported environment can run the command as written.
- [ ] The install source and package name are canonical.
- [ ] The verification command proves the intended executable or library is present.
- [ ] Alternative paths are clearly separated and maintained.
- [ ] Uninstall, upgrade, or migration links are included only when necessary.

## Assembly note

Installation usually follows prerequisites. A short usage preview may come first when readers need to evaluate the interface before investing in setup; see [ASSEMBLY.md](../../ASSEMBLY.md).
