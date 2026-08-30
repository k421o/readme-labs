# Shared project context

- Target repository: `/Users/karltonsuits/Documents/ChatGPT/reademe-temp`
- Target README: `README.md`
- Starting profile: `minimal`

## Verified repository facts

- Project name: NotebookLM saved-page extraction.
- Purpose: recover and document source, chat, and Studio metadata from a Chrome-saved NotebookLM page while keeping the original private HTML out of the repository.
- Primary audience: maintainers reproducing or reviewing the saved-page extraction and its recovered documentation.
- Canonical extractor: `scripts/extract_notebooklm_save.py`; the existing root `README.md` documents the supported invocation and prerequisites.
- Canonical outputs: `docs/sources.md` and `docs/chat-transcript.md`.
- Supporting project documentation is linked from the existing root `README.md`.
- No license file is present, so no license component is selected.
- This is a forward test only. Workers must not replace or edit the existing root `README.md`.

## Cross-component decisions

- Use the display name "NotebookLM Saved-Page Extraction" and the term "saved page" in prose.
- Lead from project identity to a compact value statement, then the reproducible extraction command.
- Commands run from the repository root and must match existing documentation or script help.
- Keep this minimal profile concise. Do not add unsupported API, governance, badge, or license claims.

## Selected components

- `project-title`: Project title
- `short-description`: Short description
- `relative-links`: Relative links
- `usage-quickstart`: Usage / quickstart
