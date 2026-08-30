# New Module Authoring Checklist

Use this when extending the kit with another atomic README element.

- [ ] The module answers one distinct reader question.
- [ ] The filename and title describe that element, not a broad zone.
- [ ] The module card states its output, default placement, and applicability.
- [ ] Required author inputs use documented `{{UPPER_SNAKE_CASE}}` placeholders.
- [ ] The template is copy-ready and contains only one primary fragment.
- [ ] Optional branches are clearly marked and removable.
- [ ] Internal paths are relative to a repository-root README.
- [ ] Code fences have language identifiers.
- [ ] Validation checks are specific and manually testable.
- [ ] Assembly notes identify ordering, nesting, or dependency constraints.
- [ ] The component catalog records whether the module is a worker, owner extension, policy, or derived output.
- [ ] A worker module has one unambiguous heading contract and can be emitted without editing another fragment.
- [ ] Any dependency that prevents safe parallel authorship is assigned to an owner or integration phase.
- [ ] The module is linked from the catalog in `../README.md`.
- [ ] Any new source-derived rule is recorded in `../PROVENANCE.md`.
