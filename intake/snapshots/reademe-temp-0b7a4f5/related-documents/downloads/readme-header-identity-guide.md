# Zone 1 Specification: Header & Project Identity for README.md

> **Document Type:** Technical Specification & Authoring Standard  
> **Target Audience:** Systems Architects, Maintainers, Technical Writers, AI Agent Developers  
> **Compliance Baselines:** `standard-readme` Specification v1.3.0, CommonMark / GFM, `markdownlint` (MD025, MD041), `mdsmith` (MDS004, MDS051)

---

## 1. Overview & Interface Role

The top-of-file block of a repository `README.md` serves as the primary **administrative interface** and **"front door"** of a software project. It governs initial interactions with both human developers seeking rapid onboarding and automated tooling (package indexers, static AST linters, RAG embedding pipelines, and autonomous AI coding agents).

Zone 1 must establish project identity, operational status, and core scope immediately upon file load. Under formal specifications like **standard-readme**, this zone functions without internal `##` heading markers, creating a continuous, semantically dense masthead.

---

## 2. Structural Component Sequence

Zone 1 comprises up to **five sequential components**. Optional components may be omitted, but the remaining items must strictly maintain their relative order to pass AST linting checks.

```
┌─────────────────────────────────────────────────────────┐
│ 1. Project Title (# H1)                                  │
├─────────────────────────────────────────────────────────┤
│ 2. Banner Image (Optional)                              │
├─────────────────────────────────────────────────────────┤
│ 3. Badges (Optional)                                    │
├─────────────────────────────────────────────────────────┤
│ 4. Short Description (Required)                         │
├─────────────────────────────────────────────────────────┤
│ 5. Long Description / Naming Discrepancy Note (Optional)│
└─────────────────────────────────────────────────────────┘
```

---

## 3. Deep Component Specifications

### Component 1: Project Title (`# H1`)

* **Status:** Mandatory (Exactly one `H1` header per document).
* **Formatting Rules:**
  * Must be constructed using ATX syntax (`# Title`). Setext headings (`===`) are discouraged for linter consistency.
  * Must appear on the very first non-comment line of the document.
* **Slug & Alias Matching:**
  * The title must match the parent repository folder, root directory, or published package manager name exactly.
  * **Parenthesized Alias Syntax:** If the human-friendly display name differs from the exact folder or registry slug, the slug must be appended in italics and parentheses at the end of the `H1` text:
    ```markdown
    # Standard Readme Style _(standard-readme)_
    ```
* **Linter Enforcement:**
  * **`markdownlint`**: Enforces `MD025` (*single-title/single-h1*) and `MD041` (*first-line-heading/first-line-h1*).
  * **`remark-lint`**: `remark-lint-appropriate-heading` verifies that the `H1` text matches the parent folder stem or parenthesized alias.
  * **`mdsmith`**: Enforces `MDS004` (*first-line-heading*) and `MDS051` (*single-h1*).

---

### Component 2: Banner Image *(Optional)*

* **Status:** Optional.
* **Formatting Rules:**
  * Must appear directly below the main title.
  * **No Heading Header:** Must **not** be preceded by its own heading tag (e.g., `## Banner` is strictly forbidden).
* **Asset Location & Security:**
  * Must link to a **local repository asset** (e.g., `assets/banner.png` or `images/logo.png`).
  * Absolute HTTP/HTTPS URLs for banners are prohibited to prevent third-party tracking, cross-site mixed content warnings, and broken assets during offline or air-gapped operations.
* **Visual Alignment:**
  * Standard Markdown image syntax or centered HTML wrappers (`<div align="center">`) are permitted:
    ```markdown
    <div align="center">
      <img src="assets/banner.png" alt="Project Banner" width="600" />
    </div>
    ```

---

### Component 3: Badges *(Optional)*

* **Status:** Optional.
* **Formatting Rules:**
  * Must reside directly under the title or banner without an `H2` header.
  * Must be **newline-delimited image links** (each badge image wrapped in an anchor link on its own line or separated by single whitespace) to ensure AST parsers process them cleanly.
* **Metadata & Telemetry Signals:**
  * Dynamic badges (via [Shields.io](https://shields.io)) communicate real-time project health: build status, test coverage, package registry version, SPDX license type, and runtime requirements.
* **Curing "Badge Noise":**
  * Limit badges to **3–5 high-value indicators** (e.g., CI Build Status, Release Version, License). Excessive badge clusters create visual clutter, slow page rendering, and increase token noise for AI parsers.
  * Standard Readme compliance can be signaled via the official badge:
    ```markdown
    [![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
    ```

---

### Component 4: Short Description *(Required)*

* **Status:** Mandatory.
* **Formatting Rules:**
  * Must be a single, concise sentence **under 120 characters**.
  * Must reside on its own line directly following title/banner/badges.
  * Must **not** use heading markup (`#`), bold styling, or blockquote prefixes (`>`).
* **Cross-Platform Metadata Alignment:**
  * To maintain operational consistency across registries, this exact text string must match:
    1. The `description` field in package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`).
    2. The repository description field in GitHub / GitLab settings.

---

### Component 5: Long Description *(Optional)*

* **Status:** Optional.
* **Formatting Rules:**
  * Must reside within the header block **without an H2 heading header**.
  * Spans 1–3 conceptual paragraphs explaining the core problem, architectural goals, and target audience.
* **Naming Discrepancy Protocol:**
  * If the repository name, local directory folder, and package manager registration name do not match, standard-readme **mandates** adding an explicit explanatory note in this section explaining the variance.
* **Progressive Disclosure Rule:**
  * If the long description expands beyond 3 paragraphs into lengthy background essays, it must be trimmed and offloaded to an explicit `## Background` section lower in the document to preserve header scannability.

---

## 4. Static Linting & Validation Matrix

| Rule ID (`markdownlint` / `mdsmith`) | Rule Identifier Name | Validation Objective | Operational Fix / Enforcement |
| :--- | :--- | :--- | :--- |
| `MD041` / `MDS004` | `first-line-heading` | Enforces that the document starts with a top-level heading (`# H1`). | Place `# Title` on line 1. |
| `MD025` / `MDS051` | `single-title/single-h1` | Blocks multiple top-level `H1` headers in a single document. | Convert secondary `#` headers to `## H2`. |
| `MD013` / `MDS001` | `line-length` | Flags unformatted lines exceeding character thresholds (default 80/120 chars). | Wrap prose or configure linter exclusions for badge lines. |
| `remark-appropriate-heading` | `appropriate-heading` | Ensures `H1` text matches parent directory stem or italicized alias. | Update `H1` or add `_(folder-slug)_`. |
| `standard-readme:section-order` | `section-order` | AST check validating that header elements precede `## Table of Contents` or `## Install`. | Reorder components sequentially. |

---

## 5. Production Exemplar Template

```markdown
# FastData Engine _(fastdata-pipeline)_

<div align="center">
  <img src="assets/banner.png" alt="FastData Engine Logo" width="600" />
</div>

[![CI Build](https://img.shields.io/github/actions/workflow/status/my-org/fastdata-pipeline/ci.yml?branch=main)](https://github.com/my-org/fastdata-pipeline/actions)
[![Coverage](https://img.shields.io/codecov/c/github/my-org/fastdata-pipeline)](https://codecov.io/gh/my-org/fastdata-pipeline)
[![PyPI Version](https://img.shields.io/pypi/v/fastdata-engine)](https://pypi.org/project/fastdata-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A lightweight Python engine for real-time telemetry log streaming and zero-allocation parsing.

FastData Engine bridges edge telemetry feeds and downstream analytical stores. Built with native Rust bindings and Python interfaces, it handles multi-gigabyte log streams with minimal memory overhead and zero lock contention.

_Note: The repository directory is named `fastdata-pipeline`, while the distributed PyPI package is registered as `fastdata-engine` to prevent naming collisions with legacy packages._
```
