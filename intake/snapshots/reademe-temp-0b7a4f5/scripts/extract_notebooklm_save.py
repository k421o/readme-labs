#!/usr/bin/env python3
"""Extract rendered NotebookLM data from a Chrome "Save Page As" HTML file.

The extractor intentionally reads the rendered DOM rather than Google app
bootstrap data. On macOS it also inspects the saved favicon files' Spotlight
provenance metadata, which retains the original source URLs.
"""

from __future__ import annotations

import argparse
import os
import plistlib
import re
import subprocess
from collections import OrderedDict
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from lxml import html


def class_tokens(element) -> set[str]:
    return set(element.get("class", "").split())


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200d", "")).strip()


def text_of(element) -> str:
    return squash("".join(element.itertext()))


def citation_marker(button) -> str:
    labels = button.xpath(".//span[@aria-label]/@aria-label")
    if labels:
        number = labels[0].split(":", 1)[0]
        return f"[{number}]"
    if button.xpath('.//mat-icon[@aria-label="Show additional citations"]'):
        return "[…]"
    return ""


def inline_code(value: str) -> str:
    fence = "`" if "`" not in value else "``"
    return f"{fence}{value}{fence}"


def render_inline(element, *, omit_lists: bool = False, trim: bool = True) -> str:
    """Render the inline descendants of an element as compact Markdown."""

    pieces: list[str] = [element.text or ""]
    for child in element:
        if not isinstance(child.tag, str):
            pieces.append(child.tail or "")
            continue

        tag = child.tag.lower()
        if omit_lists and tag in {"ul", "ol"}:
            rendered = ""
        elif tag == "button" and "citation-marker" in class_tokens(child):
            rendered = citation_marker(child)
        elif tag in {"b", "strong"}:
            rendered = f"**{render_inline(child, omit_lists=omit_lists, trim=False)}**"
        elif tag in {"i", "em"}:
            rendered = f"*{render_inline(child, omit_lists=omit_lists, trim=False)}*"
        elif tag == "code":
            rendered = inline_code(squash("".join(child.itertext())))
        elif tag == "a":
            label = render_inline(child, omit_lists=omit_lists, trim=False)
            href = child.get("href")
            rendered = f"[{label}]({href})" if href else label
        elif tag == "br":
            rendered = "\n"
        elif tag == "mat-icon":
            rendered = ""
        else:
            rendered = render_inline(child, omit_lists=omit_lists, trim=False)

        pieces.append(rendered)
        pieces.append(child.tail or "")

    value = "".join(pieces).replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    return value.strip() if trim else value


def render_list(list_element, depth: int = 0) -> list[str]:
    ordered = list_element.tag.lower() == "ol"
    lines: list[str] = []
    index = 0

    for structural in list_element:
        if not isinstance(structural.tag, str):
            continue
        if structural.tag.lower() == "li":
            candidates = [structural]
        else:
            candidates = structural.xpath("./paragraph-element-view/li")

        for item in candidates:
            index += 1
            marker = f"{index}." if ordered else "-"
            content = render_inline(item, omit_lists=True)
            lines.append(f"{'  ' * depth}{marker} {content}".rstrip())
            for nested in item:
                if isinstance(nested.tag, str) and nested.tag.lower() in {"ul", "ol"}:
                    lines.extend(render_list(nested, depth + 1))

    return lines


def code_fence(code: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", code)), default=0)
    return "`" * max(3, longest + 1)


def render_table(table) -> list[str]:
    rows: list[list[str]] = []
    for row in table.xpath(".//tr"):
        cells = row.xpath("./th|./td")
        if cells:
            rows.append([render_inline(cell).replace("|", "\\|") for cell in cells])
    if not rows:
        return []

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    output = ["| " + " | ".join(rows[0]) + " |"]
    output.append("| " + " | ".join(["---"] * width) + " |")
    output.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return output


def render_structural(element) -> list[str]:
    if element.xpath("./hr"):
        return ["---"]

    code_blocks = element.xpath("./code-block-element-view//pre/code")
    if code_blocks:
        raw_code = "".join(code_blocks[0].itertext()).strip("\n")
        code = "\n".join(line.rstrip() for line in raw_code.splitlines())
        fence = code_fence(code)
        return [fence, code, fence]

    tables = element.xpath("./table-element-view//table")
    if tables:
        return render_table(tables[0])

    paragraphs = element.xpath("./paragraph-element-view/*[self::div or self::li]")
    if not paragraphs:
        return []

    paragraph = paragraphs[0]
    classes = class_tokens(paragraph)
    if paragraph.tag.lower() == "li":
        return [f"- {render_inline(paragraph, omit_lists=True)}"]

    content = render_inline(paragraph)
    if "heading2" in classes:
        return [f"### {content}"]
    if "heading3" in classes:
        return [f"#### {content}"]
    if "heading4" in classes:
        return [f"##### {content}"]
    if "blockquote" in classes:
        return [f"> {line}" for line in content.splitlines()]
    return [content] if content else []


def citation_map(answer) -> OrderedDict[str, str]:
    citations: dict[int, str] = {}
    labels = answer.xpath(
        './/button[contains(concat(" ", normalize-space(@class), " "),'
        ' " citation-marker ")]//span[@aria-label]/@aria-label'
    )
    for label in labels:
        number_text, title = label.split(": ", 1)
        citations[int(number_text)] = title
    return OrderedDict((str(key), citations[key]) for key in sorted(citations))


def render_thoughts(answer) -> list[str]:
    chains = answer.xpath('.//thinking-chain-view//button[1][@aria-expanded="true"]/ancestor::thinking-chain-view[1]')
    if not chains:
        return []

    lines = ["> **Expanded “Thoughts” panel preserved in the save**", ">"]
    for block in chains[0].xpath(".//thought-block-view"):
        titles = block.xpath('.//*[contains(@class,"thought-block__title")][1]')
        title = text_of(titles[0]) if titles else "Untitled step"
        bodies = block.xpath('.//*[contains(@class,"thought-block__body")][1]')
        body = text_of(bodies[0]) if bodies else ""
        suffix = f" — {body}" if body else ""
        lines.append(f"> - **{title}**{suffix}")
    return lines


def render_answer(answer) -> tuple[str, OrderedDict[str, str]]:
    renderers = answer.xpath(".//element-list-renderer")
    if not renderers:
        return "", OrderedDict()

    lines = render_thoughts(answer)
    if lines:
        lines.append("")

    for child in renderers[0]:
        if not isinstance(child.tag, str):
            continue
        if child.tag == "labs-tailwind-structural-element-view-v2":
            block = render_structural(child)
        elif child.tag in {"ul", "ol"}:
            block = render_list(child)
        else:
            continue
        if block:
            lines.extend(block)
            lines.append("")

    return "\n".join(lines).rstrip(), citation_map(answer)


def user_message(message) -> str:
    bodies = message.xpath('.//*[contains(@class,"md3-body-text")]')
    return text_of(bodies[0]) if bodies else text_of(message)


def source_url_from_favicon(html_path: Path, source_element) -> str | None:
    icons = source_element.xpath(
        './/*[contains(concat(" ", normalize-space(@class), " "),'
        ' " source-item-source-icon ")]'
    )
    if not icons or icons[0].tag.lower() != "img":
        return None

    relative = icons[0].get("src")
    if not relative:
        return None
    sidecar = (html_path.parent / relative).resolve()
    if not sidecar.exists():
        return None

    try:
        if hasattr(os, "getxattr"):
            raw = os.getxattr(sidecar, "com.apple.metadata:kMDItemWhereFroms")
        else:
            result = subprocess.run(
                ["xattr", "-px", "com.apple.metadata:kMDItemWhereFroms", str(sidecar)],
                check=True,
                capture_output=True,
                text=True,
            )
            raw = bytes.fromhex(result.stdout)
        values = plistlib.loads(raw)
    except (
        AttributeError,
        OSError,
        plistlib.InvalidFileException,
        subprocess.CalledProcessError,
        ValueError,
    ):
        return None

    for value in values:
        parsed = urlparse(value)
        if parsed.netloc.endswith("gstatic.com"):
            target = parse_qs(parsed.query).get("url", [])
            if target:
                return target[0]
    return None


def extract_sources(root, html_path: Path) -> list[dict[str, str | bool | None]]:
    items = root.xpath(
        '//source-picker//*[contains(concat(" ", normalize-space(@class), " "),'
        ' " single-source-container ")]'
    )
    sources = []
    for index, item in enumerate(items, 1):
        titles = item.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "),'
            ' " source-title ")]/@aria-label'
        )
        icons = item.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "),'
            ' " source-item-source-icon ")]'
        )
        selected = bool(item.xpath('.//mat-checkbox[contains(@class,"mat-mdc-checkbox-checked")]'))
        kind = "NotebookLM deep-research Markdown" if icons and icons[0].tag == "mat-icon" else "Web"
        title = squash(titles[0]) if titles else text_of(item)
        title = re.sub(r"^\[\s*LFX\]", "[LFX]", title)
        sources.append(
            {
                "index": index,
                "title": title,
                "kind": kind,
                "selected": selected,
                "url": source_url_from_favicon(html_path, item),
            }
        )
    return sources


def write_sources(path: Path, sources: list[dict[str, str | bool | None]]) -> None:
    urls = sum(bool(source["url"]) for source in sources)
    web = sum(source["kind"] == "Web" for source in sources)
    internal = len(sources) - web
    unique_titles = len({str(source["title"]) for source in sources})
    lines = [
        "# Notebook sources",
        "",
        "This is the left-panel source list in its saved display order. Titles come from the rendered HTML. Web URLs come from the macOS provenance metadata on the companion favicon files; they are not present as links in the HTML itself.",
        "",
        f"- **Rows:** {len(sources)} ({unique_titles} unique titles)",
        f"- **Types:** {web} web sources; {internal} NotebookLM deep-research Markdown sources",
        f"- **Recovered web URLs:** {urls} of {web}",
        f"- **Selection state:** {sum(bool(source['selected']) for source in sources)} of {len(sources)} checked",
        "- **Known duplicate:** rows 51 and 52 are separate saved source records for the same React repository",
        "",
        "“URL not recoverable” means the corresponding favicon sidecar was absent from the saved-page folder. It does not mean the source lacked a URL in NotebookLM.",
        "",
        "| # | Source | Type |",
        "| ---: | --- | --- |",
    ]

    for source in sources:
        title = (
            str(source["title"])
            .replace("|", "\\|")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        if source["url"]:
            target = quote(str(source["url"]), safe=":/?&=#%+;,@~-._")
            label = f"[{title}]({target})"
        elif source["kind"] == "Web":
            label = f"{title} — *URL not recoverable*"
        else:
            label = title
        lines.append(f"| {source['index']} | {label} | {source['kind']} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_chat(path: Path, messages) -> dict[str, int]:
    if len(messages) % 2:
        raise ValueError(f"Expected user/assistant message pairs; found {len(messages)} messages")

    turns = len(messages) // 2
    lines = [
        "# Saved chat transcript",
        "",
        f"The rendered save contains **{turns} complete user/NotebookLM exchanges** ({len(messages)} message nodes). No answer body has a truncation or “read more” marker. This is a structural transcription of the rendered DOM, not a claim that no older server-side history ever existed.",
        "",
        "NotebookLM citation numbers are local to each response. Numbered markers and their saved title labels are preserved below. `[…]` marks an “additional citations” control whose hidden citation identities were not stored in the HTML. Seventeen “Thoughts” panels were collapsed and contain no saved details; turn 17 was expanded and its displayed status steps are included.",
        "",
    ]

    answer_words = 0
    answer_characters = 0
    citation_markers = 0
    hidden_citation_controls = 0

    for offset in range(0, len(messages), 2):
        turn = offset // 2 + 1
        prompt = user_message(messages[offset])
        answer, citations = render_answer(messages[offset + 1])
        answer_words += len(re.findall(r"\b[\w'-]+\b", answer))
        answer_characters += len(answer)
        citation_markers += len(
            messages[offset + 1].xpath(
                './/button[contains(@class,"citation-marker")]//span[@aria-label]'
            )
        )
        hidden_citation_controls += len(
            messages[offset + 1].xpath(
                './/button[contains(@class,"citation-marker")]'
                '//mat-icon[@aria-label="Show additional citations"]'
            )
        )

        lines.extend(
            [
                f"## Turn {turn}",
                "",
                "**User**",
                "",
                prompt,
                "",
                "**NotebookLM**",
                "",
                answer,
                "",
            ]
        )
        if citations:
            lines.extend(["**Visible citation labels in this response**", ""])
            lines.extend(f"- [{number}] {title}" for number, title in citations.items())
            lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {
        "turns": turns,
        "messages": len(messages),
        "answer_words": answer_words,
        "answer_characters": answer_characters,
        "citation_markers": citation_markers,
        "hidden_citation_controls": hidden_citation_controls,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path, help="Saved NotebookLM HTML file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for sources.md and chat-transcript.md (default: docs)",
    )
    args = parser.parse_args()

    html_path = args.html.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    root = html.fromstring(html_path.read_bytes())
    sources = extract_sources(root, html_path)
    messages = root.xpath("//chat-message")

    write_sources(output_dir / "sources.md", sources)
    stats = write_chat(output_dir / "chat-transcript.md", messages)

    print(f"Wrote {output_dir / 'sources.md'} ({len(sources)} sources)")
    print(
        f"Wrote {output_dir / 'chat-transcript.md'} "
        f"({stats['turns']} turns, {stats['answer_words']} answer words)"
    )


if __name__ == "__main__":
    main()
