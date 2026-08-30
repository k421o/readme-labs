# NotebookLM saved-page extraction

This repository documents the newest file found in Downloads at extraction time:

`Modern Repository Standards and Agentic AI Documentation Strategies - Gemini Notebook.html`

The saved page is unusually recoverable. Its rendered DOM contains the complete left source inventory, 18 full chat exchanges, and the right Studio inventory. The companion favicon files also retain most original source URLs in macOS provenance metadata.

## Findings at a glance

- **Sources:** 136 saved rows, 135 unique titles, all selected. The list contains 134 web rows and two internal NotebookLM deep-research Markdown reports. Original URLs were recovered for 131 web rows.
- **Chat:** 18 complete user/NotebookLM pairs (36 messages), including headings, lists, 12 code blocks, one comparison table, 369 visible numbered citation markers, and one expanded process panel. No response body has a saved truncation marker.
- **Studio:** six named entries plus one report still shown as generating. The saved cards contain titles and metadata, not artifact bodies; six related Google Docs and one downloaded Markdown file were recovered separately in a follow-up pass.
- **Consistency:** the chat claims that some documents were published even though they are absent from the saved Studio list. The panel inventory is therefore the stronger artifact-existence evidence.
- **Privacy:** the original HTML contains Google account and application bootstrap data. It is referenced by hash but intentionally not copied into this repository.

## Documentation

- [Notebook overview and recovery limits](docs/notebook-overview.md)
- [Left-panel source inventory](docs/sources.md)
- [Central chat transcript](docs/chat-transcript.md)
- [Right-panel Studio inventory](docs/studio-items.md)
- [Recovered Drive and Downloads documents](related-documents/README.md)
- [Modular README template system](modular-templates/README.md)
- [Repo-local modular README skill](.agents/skills/modular-readme/SKILL.md)

## Reproduce the mechanical extraction

The extractor regenerates `docs/sources.md` and `docs/chat-transcript.md` from a Chrome saved-page HTML file:

```sh
python3 scripts/extract_notebooklm_save.py \
  "/path/to/notebook.html" \
  --output-dir docs
```

It requires Python 3 and `lxml`. Source URL recovery additionally depends on the original macOS saved-page companion directory and its extended attributes.
