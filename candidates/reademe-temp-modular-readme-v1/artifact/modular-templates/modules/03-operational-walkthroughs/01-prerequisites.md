# Module: Prerequisites

| Field | Value |
| --- | --- |
| Output | A bounded list of conditions required before installation |
| Default placement | Immediately before installation, or nested within it |
| Applicability | Conditional |
| Reader question | “What must already be available before I start?” |

## Purpose

Prevent predictable setup failures by declaring the environment, tools, access, and external services the documented path assumes.

## Inputs

- Supported operating systems or platform constraints.
- Exact runtime and package-manager version ranges.
- Required system tools, services, accounts, ports, or hardware.
- Commands readers can use to verify the prerequisites.

## Template

````markdown
## Prerequisites

- {{RUNTIME}} {{VERSION_RANGE}} or later within the supported major version
- {{PACKAGE_MANAGER}} {{VERSION_RANGE}}
- {{SYSTEM_DEPENDENCY}} available on `PATH`
- Access to {{EXTERNAL_SERVICE_OR_RESOURCE}}

Verify the local tools:

```bash
{{RUNTIME_VERSION_COMMAND}}
{{PACKAGE_MANAGER_VERSION_COMMAND}}
```
````

## Rules

- State version bounds precisely enough to test.
- Separate required prerequisites from optional integrations.
- Explain how to obtain unusual dependencies, preferably through a stable relative guide.
- Name required access without publishing credentials or secrets.
- Do not repeat dependencies installed automatically by the documented installation command.
- Include OS-specific notes only for supported differences.

## Validation

- [ ] Every prerequisite is necessary for at least one documented path.
- [ ] Version requirements match manifests and CI.
- [ ] Verification commands run on the stated platforms.
- [ ] External services and permissions are named before they are used.
- [ ] Optional prerequisites are labeled and tied to their feature.

## Assembly note

Keep this as `## Prerequisites` when it stands alone. Change it to `### Prerequisites` when nesting it under `## Installation`.
