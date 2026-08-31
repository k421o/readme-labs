# NotebookLM Saved-Page Extraction

A reproducible NotebookLM saved-page recovery project for maintainers that documents source, chat, and Studio metadata while keeping the private original HTML out of the repository.

## Usage

From the repository root, run the extractor with Python 3, `lxml`, and the Chrome saved-page HTML file available:

```bash
python3 scripts/extract_notebooklm_save.py \
  "/path/to/notebook.html" \
  --output-dir docs
```

The command regenerates the [source inventory](docs/sources.md) and [chat transcript](docs/chat-transcript.md). Recovering original source URLs additionally requires the saved page's original macOS companion directory and its extended attributes.
