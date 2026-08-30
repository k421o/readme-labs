#!/usr/bin/env python3
"""Prepare, validate, and assemble isolated README component work."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_REPO_ROOT = SKILL_ROOT.parents[2]
CATALOG_PATH = SKILL_ROOT / "references" / "component-catalog.json"
DEFAULT_WORK_ROOT = SKILL_ROOT / "work"
RUN_SCHEMA_VERSION = 1
CONTEXT_SCAFFOLD_MARKERS = (
    "Before dispatch, replace this paragraph",
    "Before dispatch, record terminology",
)


class WorkflowError(RuntimeError):
    """A user-correctable workflow error."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def load_catalog() -> dict[str, Any]:
    catalog = read_json(CATALOG_PATH)
    if catalog.get("schema_version") != 1:
        raise WorkflowError(f"Unsupported catalog schema in {CATALOG_PATH}")

    components = catalog.get("components")
    if not isinstance(components, list) or not components:
        raise WorkflowError("The component catalog has no components")

    ids: set[str] = set()
    for component in components:
        component_id = component.get("id")
        if not isinstance(component_id, str) or component_id in ids:
            raise WorkflowError(f"Invalid or duplicate component id: {component_id!r}")
        ids.add(component_id)
        guide = TEMPLATE_REPO_ROOT / component.get("guide", "")
        if not guide.is_file():
            raise WorkflowError(f"Guide for {component_id} does not exist: {guide}")
        if component.get("mode") not in {
            "worker",
            "owner-extension",
            "policy",
            "derived",
        }:
            raise WorkflowError(f"Invalid execution mode for {component_id}")
        if component.get("heading") not in {"h1", "h2", "none"}:
            raise WorkflowError(f"Invalid heading contract for {component_id}")

    for profile_name, profile in catalog.get("profiles", {}).items():
        unknown = set(profile.get("components", [])) - ids
        if unknown:
            raise WorkflowError(
                f"Profile {profile_name} uses unknown components: {sorted(unknown)}"
            )
    unknown_always = set(catalog.get("always_on", [])) - ids
    if unknown_always:
        raise WorkflowError(f"Unknown always-on components: {sorted(unknown_always)}")
    return catalog


def component_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {component["id"]: component for component in catalog["components"]}


def sorted_components(
    ids: Iterable[str], catalog: dict[str, Any]
) -> list[dict[str, Any]]:
    components = component_map(catalog)
    return sorted(
        (components[component_id] for component_id in ids),
        key=lambda item: item["order"],
    )


def normalize_run_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower()).strip("-._")
    if not normalized:
        raise WorkflowError("Run id must contain at least one letter or number")
    return normalized


def resolve_selected(args: argparse.Namespace, catalog: dict[str, Any]) -> list[str]:
    profiles = catalog.get("profiles", {})
    if args.profile not in profiles:
        raise WorkflowError(
            f"Unknown profile {args.profile!r}; run the list command for choices"
        )

    components = component_map(catalog)
    include = set(args.include or [])
    exclude = set(args.exclude or [])
    unknown = (include | exclude) - set(components)
    if unknown:
        raise WorkflowError(f"Unknown component ids: {', '.join(sorted(unknown))}")

    always_on = set(catalog.get("always_on", []))
    forbidden_exclusions = always_on & exclude
    if forbidden_exclusions:
        raise WorkflowError(
            f"Always-on policies cannot be excluded: {', '.join(sorted(forbidden_exclusions))}"
        )

    selected = set(profiles[args.profile]["components"]) | include | always_on
    selected -= exclude

    for component_id in tuple(selected):
        component = components[component_id]
        if component["mode"] == "owner-extension":
            selected.add(component["owner"])

    workers = [
        component
        for component in sorted_components(selected, catalog)
        if component["mode"] == "worker"
    ]
    if not workers:
        raise WorkflowError("Select at least one worker component")
    return [component["id"] for component in sorted_components(selected, catalog)]


def validate_target_readme(target_root: Path, value: str) -> str:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise WorkflowError(
            "--target-readme must be a path inside the target repository"
        )
    resolved = (target_root / relative).resolve()
    try:
        resolved.relative_to(target_root)
    except ValueError as exc:
        raise WorkflowError("--target-readme escapes the target repository") from exc
    return relative.as_posix()


def heading_instruction(contract: str) -> str:
    if contract == "h1":
        return (
            "Start with exactly one H1 (`# `). Emit no other headings in this fragment."
        )
    if contract == "h2":
        return "Start with one H2 (`## `). Subheadings may use H3 or deeper without skipping levels."
    return "Emit a header fragment with no Markdown headings."


def render_shared_context(
    target_root: Path,
    target_readme: str,
    profile: str,
    selected: list[dict[str, Any]],
) -> str:
    lines = [
        "# Shared project context",
        "",
        f"- Target repository: `{target_root}`",
        f"- Target README: `{target_readme}`",
        f"- Starting profile: `{profile}`",
        "",
        "## Verified repository facts",
        "",
        (
            "Before dispatch, replace this paragraph with a compact evidence-backed summary of the "
            "project name, audience, primary value, supported installation and usage paths, public "
            "interfaces, governance routes, and license status. Record unknowns explicitly instead of guessing."
        ),
        "",
        "## Cross-component decisions",
        "",
        (
            "Before dispatch, record terminology, preferred reader journey, canonical documentation "
            "paths, command working directory, and any intentionally omitted profile components."
        ),
        "",
        "## Selected components",
        "",
    ]
    lines.extend(
        f"- `{component['id']}`: {component['label']}" for component in selected
    )
    return "\n".join(lines) + "\n"


def render_packet(
    component: dict[str, Any],
    selected: list[dict[str, Any]],
    run_dir: Path,
    target_root: Path,
) -> str:
    component_id = component["id"]
    guides = [TEMPLATE_REPO_ROOT / component["guide"]]
    for selected_component in selected:
        if (
            selected_component["mode"] == "owner-extension"
            and selected_component.get("owner") == component_id
        ):
            guides.append(TEMPLATE_REPO_ROOT / selected_component["guide"])
    for selected_component in selected:
        if selected_component["mode"] == "policy":
            guides.append(TEMPLATE_REPO_ROOT / selected_component["guide"])

    output_path = run_dir / "components" / f"{component_id}.md"
    report_path = run_dir / "reports" / f"{component_id}.json"
    context_path = run_dir / "shared-context.md"
    contract_path = SKILL_ROOT / "references" / "component-contract.md"
    conventions_path = TEMPLATE_REPO_ROOT / "modular-templates" / "CONVENTIONS.md"
    report_example = json.dumps(
        {
            "component_id": component_id,
            "status": "ready",
            "source_files": ["path/relative/to/target-repository"],
            "verified": [
                "A concise statement of what repository evidence established."
            ],
            "unverified": [],
            "notes": "Optional integration note for the parent.",
        },
        indent=2,
    )
    lines = [
        f"# Component work packet: {component['label']}",
        "",
        f"You own the `{component_id}` README component. Work independently and do not delegate further.",
        "",
        "## Read",
        "",
        f"- Shared decisions: `{context_path}`",
        f"- Component contract: `{contract_path}`",
        f"- Template conventions: `{conventions_path}`",
    ]
    lines.extend(f"- `{path}`" for path in dict.fromkeys(guides))
    lines.extend(
        [
            "",
            (
                f"Inspect `{target_root}` only for evidence relevant to this component. "
                "Follow any applicable repository instructions."
            ),
            "",
            "## Write boundary",
            "",
            "Write only these two files:",
            "",
            f"- Markdown fragment: `{output_path}`",
            f"- Evidence report: `{report_path}`",
            "",
            (
                "Do not edit the target README, manifest, shared context, another component, or another "
                "report. If another component appears inconsistent, record a note for the parent instead "
                "of editing it."
            ),
            "",
            "## Fragment requirements",
            "",
            f"- {heading_instruction(component['heading'])}",
            "- Emit final README Markdown only, without an outer fence or authoring commentary.",
            "- Remove template placeholders and optional-branch instructions.",
            (
                "- Include only claims, commands, paths, contacts, and legal statements supported by "
                "repository evidence."
            ),
            (
                "- Keep the fragment independently understandable and avoid positional language such "
                'as "above" or "below".'
            ),
            "",
            "## Evidence report",
            "",
            "Use this JSON shape, replacing the example values:",
            "",
            "```json",
            report_example,
            "```",
            "",
            (
                "Use repository-relative paths in `source_files`. If a required fact cannot be verified, "
                "set `status` to `blocked`, describe it in `unverified`, and tell the parent; do not fill "
                "the gap by inference."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def cmd_list(catalog: dict[str, Any]) -> int:
    print("Profiles")
    for name, profile in catalog["profiles"].items():
        components = ", ".join(profile["components"]) or "selected explicitly"
        print(f"  {name}: {profile['description']}")
        print(f"    {components}")
    print("\nComponents")
    print("  id | mode | heading | applicability")
    for component in sorted_components(
        (item["id"] for item in catalog["components"]), catalog
    ):
        print(
            f"  {component['id']} | {component['mode']} | "
            f"{component['heading']} | {component['applicability']}"
        )
    return 0


def cmd_prepare(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    target_root = Path(args.target_root).expanduser().resolve()
    if not target_root.is_dir():
        raise WorkflowError(f"Target repository does not exist: {target_root}")
    target_readme = validate_target_readme(target_root, args.target_readme)
    selected_ids = resolve_selected(args, catalog)
    selected = sorted_components(selected_ids, catalog)

    run_id = normalize_run_id(args.run_id)
    workspace_root = (
        Path(args.workspace_root).expanduser().resolve()
        if args.workspace_root
        else DEFAULT_WORK_ROOT
    )
    run_dir = workspace_root / run_id
    if run_dir.exists():
        raise WorkflowError(
            f"Run directory already exists; choose a new run id: {run_dir}"
        )
    for directory in ("briefs", "components", "reports", "assembled"):
        (run_dir / directory).mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "profile": args.profile,
        "target_root": str(target_root),
        "target_readme": target_readme,
        "template_repo_root": str(TEMPLATE_REPO_ROOT),
        "selected_components": selected_ids,
        "worker_components": [
            item["id"] for item in selected if item["mode"] == "worker"
        ],
        "derived_components": [
            item["id"] for item in selected if item["mode"] == "derived"
        ],
        "policy_components": [
            item["id"] for item in selected if item["mode"] == "policy"
        ],
    }
    write_json(run_dir / "manifest.json", manifest)
    (run_dir / "shared-context.md").write_text(
        render_shared_context(target_root, target_readme, args.profile, selected),
        encoding="utf-8",
    )
    for component in selected:
        if component["mode"] != "worker":
            continue
        packet = render_packet(component, selected, run_dir, target_root)
        (run_dir / "briefs" / f"{component['id']}.md").write_text(
            packet, encoding="utf-8"
        )

    print(f"Prepared run: {run_dir}")
    print(f"Worker packets: {len(manifest['worker_components'])}")
    if manifest["derived_components"]:
        print(f"Derived during assembly: {', '.join(manifest['derived_components'])}")
    print(f"Complete shared context before dispatch: {run_dir / 'shared-context.md'}")
    return 0


def load_run(
    run_value: str, catalog: dict[str, Any]
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    run_dir = Path(run_value).expanduser().resolve()
    manifest = read_json(run_dir / "manifest.json")
    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        raise WorkflowError(f"Unsupported run schema in {run_dir / 'manifest.json'}")
    selected_ids = manifest.get("selected_components")
    if not isinstance(selected_ids, list) or not selected_ids:
        raise WorkflowError("Run manifest has no selected components")
    components = component_map(catalog)
    unknown = set(selected_ids) - set(components)
    if unknown:
        raise WorkflowError(
            f"Run manifest references unknown components: {sorted(unknown)}"
        )
    selected = sorted_components(selected_ids, catalog)
    expected_ids = [item["id"] for item in selected]
    if selected_ids != expected_ids:
        raise WorkflowError("Run manifest component order differs from the catalog")
    return run_dir, manifest, selected


def report_state(path: Path) -> str:
    if not path.is_file():
        return "missing report"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid report"
    return str(report.get("status", "missing status"))


def validate_context(run_dir: Path) -> list[str]:
    path = run_dir / "shared-context.md"
    if not path.is_file():
        return [f"missing shared context: {path}"]
    context = path.read_text(encoding="utf-8")
    if any(marker in context for marker in CONTEXT_SCAFFOLD_MARKERS):
        return ["shared context still contains preparation instructions"]
    return []


def cmd_status(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    run_dir, _, selected = load_run(args.run, catalog)
    context_errors = validate_context(run_dir)
    print(f"shared-context | {'incomplete' if context_errors else 'ready'}")
    print("component | fragment | report")
    incomplete = bool(context_errors)
    for component in selected:
        if component["mode"] != "worker":
            continue
        component_id = component["id"]
        fragment = run_dir / "components" / f"{component_id}.md"
        fragment_state = (
            "present" if fragment.is_file() and fragment.stat().st_size else "missing"
        )
        state = report_state(run_dir / "reports" / f"{component_id}.json")
        print(f"{component_id} | {fragment_state} | {state}")
        if fragment_state != "present" or state != "ready":
            incomplete = True
    return 1 if incomplete else 0


def visible_lines(markdown: str) -> list[str]:
    visible: list[str] = []
    open_fence: tuple[str, int] | None = None
    for line in markdown.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, suffix = match.groups()
            if open_fence is None:
                open_fence = (marker[0], len(marker))
            elif (
                marker[0] == open_fence[0]
                and len(marker) >= open_fence[1]
                and not suffix.strip()
            ):
                open_fence = None
            continue
        if open_fence is None:
            visible.append(line)
    return visible


def validate_fences(component_id: str, markdown: str) -> list[str]:
    errors: list[str] = []
    open_fence: tuple[str, int] | None = None
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if not match:
            continue
        marker, suffix = match.groups()
        if open_fence is None:
            if not suffix.strip():
                errors.append(
                    f"{component_id}: code fence on line {line_number} has no language"
                )
            open_fence = (marker[0], len(marker))
        elif (
            marker[0] == open_fence[0]
            and len(marker) >= open_fence[1]
            and not suffix.strip()
        ):
            open_fence = None
    if open_fence is not None:
        errors.append(f"{component_id}: unclosed code fence")
    return errors


def markdown_headings(markdown: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    for line in visible_lines(markdown):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
    return headings


def validate_fragment(component: dict[str, Any], markdown: str) -> list[str]:
    component_id = component["id"]
    errors: list[str] = []
    if not markdown.strip():
        return [f"{component_id}: fragment is empty"]
    if re.search(r"\{\{[^{}]+\}\}", markdown):
        errors.append(f"{component_id}: unresolved template placeholder")
    if re.search(r"\[(?:TODO|TBD)(?::|\])", markdown, flags=re.IGNORECASE):
        errors.append(f"{component_id}: unfinished TODO/TBD marker")
    if re.search(
        r"<!--\s*(?:Optional|Choose|Delete|Replace)\b", markdown, flags=re.IGNORECASE
    ):
        errors.append(f"{component_id}: template-selection comment remains")
    if re.search(r"(?:file://|/Users/|/home/|[A-Za-z]:\\\\)", markdown):
        errors.append(f"{component_id}: machine-specific absolute path remains")

    raw_nonblank = [line for line in markdown.splitlines() if line.strip()]
    nonblank = [line for line in visible_lines(markdown) if line.strip()]
    first = nonblank[0].strip() if nonblank else ""
    raw_first = raw_nonblank[0].strip() if raw_nonblank else ""
    raw_last = raw_nonblank[-1].strip() if raw_nonblank else ""
    if re.match(
        r"^(?:`{3,}|~{3,})\s*(?:markdown|md)\s*$",
        raw_first,
        flags=re.IGNORECASE,
    ) and re.match(r"^(?:`{3,}|~{3,})\s*$", raw_last):
        errors.append(f"{component_id}: fragment is wrapped in an outer Markdown fence")

    headings = markdown_headings(markdown)
    contract = component["heading"]
    if contract == "h1":
        if not re.match(r"^#\s+\S", first) or first.startswith("##"):
            errors.append(f"{component_id}: fragment must start with one H1")
        if headings != headings[:1] or len(headings) != 1 or headings[0][0] != 1:
            errors.append(
                f"{component_id}: title fragment must contain exactly one H1 and no other headings"
            )
    elif contract == "h2":
        if not re.match(r"^##\s+\S", first) or first.startswith("###"):
            errors.append(f"{component_id}: section fragment must start with an H2")
        if any(level == 1 for level, _ in headings):
            errors.append(f"{component_id}: only project-title may emit an H1")
    elif headings:
        errors.append(f"{component_id}: header fragment must not emit headings")

    errors.extend(validate_fences(component_id, markdown))
    return errors


def validate_report(
    component_id: str,
    path: Path,
    target_root: Path,
) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"{component_id}: missing evidence report {path}"]
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{component_id}: invalid evidence report JSON: {exc}"]
    if report.get("component_id") != component_id:
        errors.append(f"{component_id}: report component_id does not match")
    if report.get("status") != "ready":
        errors.append(f"{component_id}: report status is not ready")

    source_files = report.get("source_files")
    if (
        not isinstance(source_files, list)
        or not source_files
        or not all(isinstance(item, str) and item for item in source_files)
    ):
        errors.append(f"{component_id}: report must list at least one source file")
    else:
        for source in source_files:
            source_path = Path(source)
            if source_path.is_absolute() or ".." in source_path.parts:
                errors.append(
                    f"{component_id}: source file must be target-relative: {source}"
                )
            elif not (target_root / source_path).exists():
                errors.append(
                    f"{component_id}: reported source file does not exist: {source}"
                )

    verified = report.get("verified")
    if (
        not isinstance(verified, list)
        or not verified
        or not all(isinstance(item, str) and item for item in verified)
    ):
        errors.append(
            f"{component_id}: report must include at least one verified statement"
        )
    unverified = report.get("unverified")
    if not isinstance(unverified, list):
        errors.append(f"{component_id}: report unverified field must be a list")
    elif unverified:
        errors.append(f"{component_id}: report still contains unverified claims")
    return errors


def strip_heading_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    return value.replace("`", "").replace("*", "").replace("_", "").strip()


def github_anchor(value: str) -> str:
    plain = strip_heading_markup(value).casefold()
    kept: list[str] = []
    for character in plain:
        category = unicodedata.category(character)
        if character.isspace():
            kept.append("-")
        elif character == "-" or category[0] in {"L", "N"}:
            kept.append(character)
    return re.sub(r"-+", "-", "".join(kept)).strip("-")


def render_toc(blocks: list[tuple[str, str]]) -> str:
    entries: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    for _, markdown in blocks:
        for level, title in markdown_headings(markdown):
            if level != 2:
                continue
            base = github_anchor(title)
            count = seen.get(base, 0)
            seen[base] = count + 1
            anchor = base if count == 0 else f"{base}-{count}"
            entries.append((strip_heading_markup(title), anchor))
    if len(entries) < 2:
        raise WorkflowError("table-of-contents requires at least two H2 sections")
    lines = ["## Table of contents", ""]
    lines.extend(f"- [{title}](#{anchor})" for title, anchor in entries)
    return "\n".join(lines)


def validate_assembled(
    markdown: str, rendered_ids: list[str], selected_ids: list[str]
) -> list[str]:
    errors: list[str] = []
    headings = markdown_headings(markdown)
    h1_count = sum(1 for level, _ in headings if level == 1)
    if h1_count != 1:
        errors.append(f"assembled README: expected exactly one H1, found {h1_count}")
    nonblank = [line for line in visible_lines(markdown) if line.strip()]
    if (
        not nonblank
        or not re.match(r"^#\s+\S", nonblank[0].strip())
        or nonblank[0].lstrip().startswith("##")
    ):
        errors.append("assembled README: H1 is not the first substantive line")
    previous_level: int | None = None
    for level, title in headings:
        if previous_level is not None and level > previous_level + 1:
            errors.append(f"assembled README: heading level skips before {title!r}")
        previous_level = level
    h2_titles = [github_anchor(title) for level, title in headings if level == 2]
    duplicates = sorted({title for title in h2_titles if h2_titles.count(title) > 1})
    if duplicates:
        errors.append(
            f"assembled README: duplicate H2 anchors: {', '.join(duplicates)}"
        )
    if "license" in selected_ids and (
        not rendered_ids or rendered_ids[-1] != "license"
    ):
        errors.append("assembled README: license is not the final component")
    return errors


def validate_run(
    run_dir: Path,
    manifest: dict[str, Any],
    selected: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    errors = validate_context(run_dir)
    target_root = Path(manifest["target_root"])
    if not target_root.is_dir():
        errors.append(f"target repository no longer exists: {target_root}")

    worker_blocks: dict[str, str] = {}
    for component in selected:
        if component["mode"] != "worker":
            continue
        component_id = component["id"]
        fragment_path = run_dir / "components" / f"{component_id}.md"
        if not fragment_path.is_file():
            errors.append(f"{component_id}: missing fragment {fragment_path}")
        else:
            markdown = fragment_path.read_text(encoding="utf-8")
            worker_blocks[component_id] = markdown.strip()
            errors.extend(validate_fragment(component, markdown))
        report_path = run_dir / "reports" / f"{component_id}.json"
        errors.extend(validate_report(component_id, report_path, target_root))

    rendered: list[tuple[str, str]] = []
    if not errors:
        base_blocks = [
            (component["id"], worker_blocks[component["id"]])
            for component in selected
            if component["mode"] == "worker"
        ]
        for component in selected:
            if component["mode"] == "worker":
                rendered.append((component["id"], worker_blocks[component["id"]]))
            elif component["mode"] == "derived":
                if component["id"] != "table-of-contents":
                    errors.append(f"Unsupported derived component: {component['id']}")
                else:
                    try:
                        rendered.append((component["id"], render_toc(base_blocks)))
                    except WorkflowError as exc:
                        errors.append(str(exc))

    assembled = (
        "\n\n".join(markdown.rstrip() for _, markdown in rendered).rstrip() + "\n"
        if rendered
        else ""
    )
    if assembled and not errors:
        errors.extend(
            validate_assembled(
                assembled,
                [component_id for component_id, _ in rendered],
                manifest["selected_components"],
            )
        )
    return assembled, errors


def print_errors(errors: list[str]) -> None:
    print("Validation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


def cmd_validate(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    run_dir, manifest, selected = load_run(args.run, catalog)
    _, errors = validate_run(run_dir, manifest, selected)
    if errors:
        print_errors(errors)
        return 1
    print(
        f"Validated {len(manifest['worker_components'])} worker components: {run_dir}"
    )
    return 0


def cmd_assemble(args: argparse.Namespace, catalog: dict[str, Any]) -> int:
    run_dir, manifest, selected = load_run(args.run, catalog)
    assembled, errors = validate_run(run_dir, manifest, selected)
    if errors:
        print_errors(errors)
        return 1

    default_output = (run_dir / "assembled" / "README.md").resolve()
    output = Path(args.output).expanduser() if args.output else default_output
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    else:
        output = output.resolve()
    if output.exists() and output != default_output and not args.force:
        raise WorkflowError(
            f"Refusing to overwrite {output}; review the preview, then pass --force explicitly"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(assembled, encoding="utf-8")
    print(f"Assembled README preview: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, validate, and assemble isolated README component work."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list", help="List profiles, component ids, and execution modes"
    )

    prepare = subparsers.add_parser(
        "prepare", help="Create an isolated run and one packet per worker"
    )
    prepare.add_argument("--run-id", required=True, help="Stable name for this run")
    prepare.add_argument(
        "--target-root",
        required=True,
        help="Absolute or relative target repository path",
    )
    prepare.add_argument(
        "--target-readme",
        default="README.md",
        help="README path relative to target root",
    )
    prepare.add_argument(
        "--profile", required=True, help="Starting profile from the catalog"
    )
    prepare.add_argument(
        "--include",
        action="append",
        default=[],
        help="Add one component id; repeat as needed",
    )
    prepare.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Remove one profile component; repeat as needed",
    )
    prepare.add_argument(
        "--workspace-root", help="Override the ignored skill-local work directory"
    )

    status = subparsers.add_parser(
        "status", help="Show fragment and report state for each worker"
    )
    status.add_argument("--run", required=True, help="Run directory created by prepare")

    validate = subparsers.add_parser(
        "validate", help="Validate worker artifacts and assembled structure"
    )
    validate.add_argument(
        "--run", required=True, help="Run directory created by prepare"
    )

    assemble = subparsers.add_parser(
        "assemble", help="Validate and write an assembled README preview"
    )
    assemble.add_argument(
        "--run", required=True, help="Run directory created by prepare"
    )
    assemble.add_argument(
        "--output", help="Optional explicit output path; defaults to the run preview"
    )
    assemble.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting an explicit existing output",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        catalog = load_catalog()
        if args.command == "list":
            return cmd_list(catalog)
        if args.command == "prepare":
            return cmd_prepare(args, catalog)
        if args.command == "status":
            return cmd_status(args, catalog)
        if args.command == "validate":
            return cmd_validate(args, catalog)
        if args.command == "assemble":
            return cmd_assemble(args, catalog)
        parser.error(f"Unknown command: {args.command}")
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
