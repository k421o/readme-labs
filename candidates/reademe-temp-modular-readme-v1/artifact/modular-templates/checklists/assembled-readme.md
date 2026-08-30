# Assembled README Checklist

## Structure

- [ ] There is exactly one `H1`, and it is the first substantive content.
- [ ] Heading levels increase one level at a time.
- [ ] The section order supports the intended reader journey.
- [ ] A table of contents is present when the README is long enough to need one.
- [ ] The license section is final when present.

## Content

- [ ] The short description explains what the project is, who it serves, and why it matters.
- [ ] Setup commands are exact and copy-pasteable.
- [ ] The happy-path usage example is minimal and verified.
- [ ] Prerequisites, configuration, CLI, and API sections appear only when applicable.
- [ ] Exhaustive material is delegated and linked instead of duplicated.
- [ ] Security and contribution routes point to current destinations.
- [ ] License text and SPDX identifier match the repository's actual license.

## Rendering and resilience

- [ ] No `{{PLACEHOLDER}}` tokens or template comments remain.
- [ ] Internal file links are relative and resolve from the root README.
- [ ] Table-of-contents anchors work in the target renderer.
- [ ] Images render, have useful alt text, and use durable assets.
- [ ] Badges resolve and link to the underlying status page.
- [ ] Mermaid or other diagrams render without syntax errors.
- [ ] Every fenced block declares a language.

## Verification

- [ ] Commands were tested in a clean or documented environment.
- [ ] Code examples still match the public API.
- [ ] Markdown linting passes under the repository's configured rules.
- [ ] Link checking passes, including delegated documents.
- [ ] A human unfamiliar with the project can identify the first successful action.

## Parallel integration

- [ ] Every selected worker produced its uniquely owned fragment and evidence report.
- [ ] Every report is ready, cites existing repository files, and has no unresolved claims.
- [ ] No worker edited the target README or another component's artifacts.
- [ ] Derived navigation was generated after headings stabilized.
- [ ] The assembled preview was reviewed for duplicate claims, vocabulary drift, and cross-section contradictions.
