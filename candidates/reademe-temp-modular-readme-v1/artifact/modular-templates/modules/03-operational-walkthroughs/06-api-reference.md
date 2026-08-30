# Module: API Reference

| Field | Value |
| --- | --- |
| Output | A concise public-interface summary or a routed reference link |
| Default placement | After usage and CLI material |
| Applicability | Conditional; for projects exposing a programmatic API |
| Reader question | “What stable interface can I call, and where is the complete contract?” |

## Purpose

Expose a small public surface directly or route readers to canonical generated documentation. The README should not become a second, drifting copy of a large API reference.

## Inputs

- Public symbol, endpoint, or interface names.
- Stable signature and parameter meanings.
- Return value or observable behavior.
- Canonical full-reference path or URL.

## Small-API template

````markdown
## API

### `{{PUBLIC_SYMBOL}}({{SIGNATURE}})`

{{ONE_SENTENCE_BEHAVIOR}}

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `{{PARAMETER}}` | `{{TYPE}}` | Yes | {{DESCRIPTION}} |
| `{{PARAMETER}}` | `{{TYPE}}` | No | {{DESCRIPTION_AND_DEFAULT}} |

Returns `{{RETURN_TYPE}}`: {{RETURN_BEHAVIOR}}.

See the [complete API reference]({{API_REFERENCE_PATH}}) for the full public surface.
````

## Delegated-reference variant

Use this instead when the API is extensive:

```markdown
## API

The public API covers {{HIGH_LEVEL_SURFACE}}. See the [complete API reference]({{API_REFERENCE_PATH}}) for signatures, types, errors, and examples.
```

## Rules

- Choose the small or delegated variant based on interface size; do not maintain two exhaustive copies.
- Document only public, supported interfaces.
- Keep signatures synchronized with the released version.
- Include errors, authentication, rate limits, or compatibility notes in the canonical reference when applicable.
- For OpenAPI or AsyncAPI projects, prefer generated canonical reference material and link it here.
- Pair the reference with a runnable usage example rather than expecting signatures to teach the workflow.

## Validation

- [ ] Symbol names and signatures match the current public API.
- [ ] Parameter and return descriptions match actual behavior.
- [ ] The canonical reference is version-aligned and reachable.
- [ ] Removed or experimental interfaces are absent or labeled.
- [ ] The README summary and generated docs do not contradict each other.

## Assembly note

Use the smallest API block that helps readers reach the canonical contract. If no programmatic API exists, omit the module.
