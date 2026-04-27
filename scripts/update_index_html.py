#!/usr/bin/env python3
"""Regenerate dynamic sections of docs/index.html from project state.

Reads pyproject.toml and ADR files to rebuild the DOC_CARDS and ADRS
sections between HTML comment markers. Prints a summary of changes.
"""

from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from html import escape
from pathlib import Path

type SectionMap = dict[str, str]

_DOC_CARDS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "Specification",
        "Flow Definition Spec",
        "github",
        "docs/spec/flow-definition-spec.md",
        "Authoritative YAML format reference — "
        "fields, conditions, subflows, validation rules",
    ),
    (
        "Architecture",
        "System Overview",
        "github",
        "docs/system.md",
        "Domain model, C4 diagrams, module structure, and constraints",
    ),
    (
        "Product",
        "Product Definition",
        "github",
        "docs/product-definition.md",
        "Product boundaries, users, and scope",
    ),
    (
        "Reference",
        "API Docs",
        "local",
        "api/flowr.html",
        "Auto-generated from source docstrings via pdoc",
    ),
    (
        "Language",
        "Glossary",
        "github",
        "docs/glossary.md",
        "Living domain glossary — source-traced definitions",
    ),
    (
        "Scope",
        "Scope Journal",
        "github",
        "docs/scope_journal.md",
        "Raw Q&A from discovery sessions",
    ),
)


@dataclass(frozen=True)
class Adr:
    """An architecture decision record with date, slug, and status."""

    date: str
    slug: str
    status: str


def _read_pyproject(root: Path) -> dict[str, object]:
    """Parse pyproject.toml and return the project section plus urls."""
    with (root / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    project: dict[str, object] = data.get("project", {})
    return project


def _repo_base_url(project: dict[str, object]) -> str:
    """Extract the repository base URL from pyproject.toml project.urls."""
    urls = project.get("urls", {})
    if isinstance(urls, dict):
        repo = urls.get("Repository", "")
        if isinstance(repo, str) and repo:
            return repo.rstrip("/")
    return ""


def _project_name(project: dict[str, object]) -> str:
    """Extract the project name from pyproject.toml."""
    name = project.get("name", "")
    return str(name) if name else ""


def _scan_adrs(adr_dir: Path) -> list[Adr]:
    """Scan ADR directory and return Adr objects sorted by date."""
    adrs: list[Adr] = []
    if not adr_dir.exists():
        return adrs
    for path in sorted(adr_dir.iterdir()):
        if not path.name.startswith("ADR-") or path.suffix != ".md":
            continue
        date, slug = _parse_adr_filename(path.name)
        status = _extract_adr_status(path)
        adrs.append(Adr(date=date, slug=slug, status=status))
    return adrs


def _parse_adr_filename(name: str) -> tuple[str, str]:
    """Parse ADR-YYYY-MM-DD-slug.md into (date, slug)."""
    stem = name.removesuffix(".md")
    parts = stem.split("-", 3)
    if len(parts) >= 4:
        date = f"{parts[1]}-{parts[2]}-{parts[3][:2]}"
        slug_parts = parts[3].split("-")[2:]
        slug = "-".join(slug_parts) if len(parts[3]) > 2 else parts[3]
        return date, slug
    return "", stem


def _extract_adr_status(path: Path) -> str:
    """Extract the status from an ADR markdown file."""
    text = path.read_text(encoding="utf-8")
    in_status = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Status":
            in_status = True
            continue
        if in_status:
            if stripped.startswith("##"):
                break
            if stripped:
                return stripped
    return "Unknown"


def _doc_card(
    label: str,
    card_title: str,
    href: str,
    desc: str,
) -> str:
    """Render a single doc-card anchor element."""
    return (
        f'      <a class="doc-card" href="{escape(href)}">\n'
        f'        <div class="doc-card-label">{escape(label)}</div>\n'
        f'        <div class="doc-card-title">{escape(card_title)}</div>\n'
        f'        <div class="doc-card-desc">{escape(desc)}</div>\n'
        f"      </a>"
    )


def _card_href(kind: str, path: str, repo_url: str) -> str:
    """Resolve the href for a doc card based on its kind."""
    if kind == "github" and repo_url:
        return f"{repo_url}/blob/main/{path}"
    return path


def _render_doc_cards(repo_url: str, project_name: str) -> str:
    """Render the DOC_CARDS section HTML."""
    cards: list[str] = []
    for label, card_title, kind, path, desc in _DOC_CARDS:
        href = _card_href(kind, path, repo_url)
        cards.append(_doc_card(label, card_title, href, desc))
    inner = "\n".join(cards)
    return f'    <div class="docs-grid">\n{inner}\n    </div>'


def _render_adrs(adrs: list[Adr]) -> str:
    """Render the ADRS section HTML."""
    items: list[str] = []
    for adr in adrs:
        items.append(
            '      <li class="adr-item">\n'
            f'        <span class="adr-date">'
            f"{escape(adr.date)}</span>\n"
            f'        <span class="adr-slug">'
            f"{escape(adr.slug)}</span>\n"
            f'        <span class="adr-status">'
            f"{escape(adr.status)}</span>\n"
            "      </li>"
        )
    inner = "\n".join(items)
    return f'    <ul class="adr-list">\n{inner}\n    </ul>'


def _render_footer(repo_url: str, project_name: str) -> str:
    """Render the FOOTER section HTML."""
    display_url = repo_url.replace("https://", "") if repo_url else ""
    if display_url:
        link = f'<a href="{escape(repo_url)}">{escape(display_url)}</a>'
        repo_span = f"{escape(project_name)} &nbsp;·&nbsp; {link}"
    else:
        repo_span = escape(project_name)
    return (
        "  <footer>\n"
        "    <span>Built with pdoc · pytest-cov · pytest-html</span>\n"
        f"    <span>{repo_span}</span>\n"
        "  </footer>"
    )


def _parse_sections(html: str) -> SectionMap:
    """Extract content between BEGIN/END markers from the HTML."""
    sections: SectionMap = {}
    for name in ("DOC_CARDS", "ADRS", "FOOTER"):
        pattern = rf"<!-- BEGIN:{name} -->\n(.*?)<!-- END:{name} -->"
        match = re.search(pattern, html, re.DOTALL)
        if match:
            sections[name] = match.group(1)
    return sections


def _replace_section(html: str, name: str, new_content: str) -> str:
    """Replace the content between markers for a named section."""
    pattern = rf"(<!-- BEGIN:{name} -->\n)(.*?)(<!-- END:{name} -->)"
    return re.sub(pattern, rf"\g<1>{new_content}\n\g<3>", html, flags=re.DOTALL)


def update_index_html(project_root: Path) -> int:
    """Regenerate dynamic sections of docs/index.html.

    Returns 0 on success, 1 on failure.
    """
    project = _read_pyproject(project_root)
    repo_url = _repo_base_url(project)
    project_name = _project_name(project)
    adrs = _scan_adrs(project_root / "docs" / "adr")

    index_path = project_root / "docs" / "index.html"
    if not index_path.exists():
        print(f"ERROR: {index_path} not found")
        return 1

    html = index_path.read_text(encoding="utf-8")
    old_sections = _parse_sections(html)

    html = _replace_section(
        html, "DOC_CARDS", _render_doc_cards(repo_url, project_name)
    )
    html = _replace_section(html, "ADRS", _render_adrs(adrs))
    html = _replace_section(html, "FOOTER", _render_footer(repo_url, project_name))

    index_path.write_text(html, encoding="utf-8")

    new_sections = _parse_sections(html)
    _print_summary(old_sections, new_sections, adrs)
    return 0


def _print_summary(
    old: SectionMap,
    new: SectionMap,
    adrs: list[Adr],
) -> None:
    """Print a summary of what changed."""
    changed = [name for name in old if old.get(name) != new.get(name)]
    if not changed:
        print("No changes detected.")
        return
    print("Updated sections: " + ", ".join(changed))
    print(f"  ADRs: {len(adrs)}")


def main() -> int:
    """Entry point for the update_index_html script."""
    project_root = Path(__file__).resolve().parent.parent
    return update_index_html(project_root)


if __name__ == "__main__":
    sys.exit(main())
