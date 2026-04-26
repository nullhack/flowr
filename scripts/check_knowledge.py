#!/usr/bin/env python3
"""Check knowledge files for structure, correspondence, and link integrity."""

from __future__ import annotations

import re
import sys
from pathlib import Path

KNOWLEDGE_DIR = ".opencode/knowledge"
SKILLS_DIR = ".opencode/skills"
VALID_SECTIONS = ["Key Takeaways", "Concepts", "Content", "Related"]
VALID_FRAGMENTS = {"key-takeaways", "concepts"}

WIKILINK_RE = re.compile(r"\[\[([a-z0-9-]+/[a-z0-9-]+)(?:#([a-z0-9-]+))?\]\]")


def _strip_code(text: str) -> str:
    """Remove fenced code blocks and inline code."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    return re.sub(r"`[^`]+`", "", text)


def _parse_frontmatter(
    text: str,
) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and return (keys, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 3 :].lstrip("\n")
    keys: dict[str, str] = {}
    for line in fm_text.splitlines():
        match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if match:
            keys[match.group(1)] = match.group(2).strip()
    return keys, body


def _extract_sections(
    body: str,
) -> list[tuple[str, str]]:
    """Extract ## sections from body as [(heading, content), ...].

    Ignores headings inside fenced code blocks.
    """
    cleaned = _strip_code(body)
    sections: list[tuple[str, str]] = []
    parts = re.split(r"^## (.+)$", cleaned, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((heading, content))
    return sections


def _count_bullets(text: str) -> int:
    """Count non-empty bullet lines (lines starting with '- ')."""
    return sum(1 for line in text.splitlines() if line.strip().startswith("- "))


def _count_concept_paragraphs(text: str) -> int:
    """Count concept paragraphs in Concepts section.

    Each concept paragraph starts with a bold heading
    (**...**: or **...**). Blank lines separate paragraphs.
    """
    count = 0
    in_paragraph = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            in_paragraph = False
            continue
        if stripped.startswith("**") and not in_paragraph:
            count += 1
            in_paragraph = True
        elif not in_paragraph and stripped:
            in_paragraph = True
            count += 1
    return count


def _extract_wikilinks(text: str) -> set[str]:
    """Extract [[domain/concept]] and [[domain/concept#fragment]] references.

    Skips wikilinks inside fenced code blocks and
    those with template placeholders (<...>).
    """
    cleaned = _strip_code(text)
    links: set[str] = set()
    for m in WIKILINK_RE.finditer(cleaned):
        inner = m.group(1)
        if "<" in inner or ">" in inner:
            continue
        links.add(m.group(0))
    return links


def _resolve_wikilink(link: str, knowledge_root: Path) -> Path | None:
    """Resolve wikilink to a file path."""
    inner = link[2:-2]
    path_part = inner.split("#", 1)[0] if "#" in inner else inner
    parts = path_part.split("/")
    if len(parts) != 2:
        return None
    domain, concept = parts
    return knowledge_root / domain / f"{concept}.md"


def _collect_skill_wikilinks(
    skills_dir: Path,
) -> set[str]:
    """Collect all wikilinks from skill files."""
    links: set[str] = set()
    if not skills_dir.exists():
        return links
    for f in skills_dir.rglob("*.md"):
        links.update(_extract_wikilinks(f.read_text()))
    return links


def _check_frontmatter(
    keys: dict[str, str],
    rel: Path,
    errors: list[str],
    stats: dict[str, int],
) -> None:
    """Validate frontmatter keys for a single file."""
    for required in ("domain", "tags", "last-updated"):
        if required not in keys:
            errors.append(f"{rel}: missing required frontmatter key '{required}'")
            stats["frontmatter_issues"] += 1
    if "purpose" in keys:
        errors.append(
            f"{rel}: 'purpose' key in frontmatter "
            "— routing is handled by skills, tags, and Key Takeaways"
        )
        stats["frontmatter_issues"] += 1


def _check_sections(
    sections: list[tuple[str, str]],
    rel: Path,
    errors: list[str],
    stats: dict[str, int],
) -> None:
    """Validate section structure for a single file."""
    section_names = [s[0] for s in sections]
    if section_names != VALID_SECTIONS:
        errors.append(f"{rel}: sections {section_names} != expected {VALID_SECTIONS}")
        stats["section_issues"] += 1
    if "Purpose" in section_names:
        errors.append(
            f"{rel}: has ## Purpose section — remove it "
            "(routing is handled by skills, tags, and Key Takeaways)"
        )
        stats["section_issues"] += 1


def _check_correspondence(
    sections: list[tuple[str, str]],
    rel: Path,
    errors: list[str],
    stats: dict[str, int],
) -> None:
    """Validate Key Takeaways / Concepts correspondence."""
    kt_text = ""
    concepts_text = ""
    for name, content in sections:
        if name == "Key Takeaways":
            kt_text = content
        elif name == "Concepts":
            concepts_text = content
    bullets = _count_bullets(kt_text)
    paras = _count_concept_paragraphs(concepts_text)
    if bullets == 0:
        errors.append(f"{rel}: Key Takeaways has no bullets")
        stats["correspondence_issues"] += 1
    elif paras == 0:
        errors.append(f"{rel}: Concepts has no paragraphs")
        stats["correspondence_issues"] += 1
    elif bullets != paras:
        errors.append(
            f"{rel}: correspondence mismatch — "
            f"{bullets} Key Takeaway bullets vs "
            f"{paras} Concept paragraphs"
        )
        stats["correspondence_issues"] += 1


def _check_wikilinks(
    text: str,
    rel: Path,
    knowledge_root: Path,
    all_wikilinks_in_files: set[str],
    all_referenced_paths: set[str],
    errors: list[str],
    stats: dict[str, int],
) -> None:
    """Validate wikilinks within a single file."""
    file_wikilinks = _extract_wikilinks(text)
    all_wikilinks_in_files.update(file_wikilinks)
    for link in file_wikilinks:
        inner = link[2:-2]
        fragment = None
        if "#" in inner:
            path_part, fragment = inner.split("#", 1)
        else:
            path_part = inner
        target = _resolve_wikilink(link, knowledge_root)
        if target is None or not target.exists():
            errors.append(f"{rel}: broken wikilink {link} — target not found")
            stats["wikilink_issues"] += 1
        elif fragment is not None and fragment not in VALID_FRAGMENTS:
            errors.append(
                f"{rel}: invalid fragment #{fragment} in {link}"
                f" — valid: {sorted(VALID_FRAGMENTS)}"
            )
            stats["wikilink_issues"] += 1
        all_referenced_paths.add(path_part)


def _check_orphans(
    knowledge_files: list[Path],
    knowledge_root: Path,
    project_root: Path,
    skill_wikilinks: set[str],
    all_wikilinks_in_files: set[str],
    errors: list[str],
    stats: dict[str, int],
) -> None:
    """Detect orphaned knowledge files."""
    for f in knowledge_files:
        rel = f.relative_to(knowledge_root)
        domain = rel.parts[0]
        concept = rel.stem
        path_key = f"{domain}/{concept}"
        referenced = False
        for link in skill_wikilinks | all_wikilinks_in_files:
            inner = link[2:-2]
            if "#" in inner:
                inner = inner.split("#", 1)[0]
            if inner == path_key:
                referenced = True
                break
        if not referenced:
            errors.append(
                f"{f.relative_to(project_root)}: orphan "
                "— not referenced by any skill or knowledge file"
            )
            stats["orphan_issues"] += 1


def check_knowledge(
    project_root: Path,
) -> tuple[bool, list[str], dict]:
    """Check all knowledge files; return (ok, errors, stats)."""
    knowledge_root = project_root / KNOWLEDGE_DIR
    skills_dir = project_root / SKILLS_DIR
    errors: list[str] = []
    stats: dict[str, int] = {
        "files_checked": 0,
        "frontmatter_issues": 0,
        "section_issues": 0,
        "correspondence_issues": 0,
        "wikilink_issues": 0,
        "orphan_issues": 0,
    }
    if not knowledge_root.exists():
        return (
            False,
            [f"knowledge directory not found: {knowledge_root}"],
            stats,
        )
    all_wikilinks_in_files: set[str] = set()
    skill_wikilinks = _collect_skill_wikilinks(skills_dir)
    all_referenced_paths: set[str] = set()
    knowledge_files = sorted(knowledge_root.rglob("*.md"))
    stats["files_checked"] = len(knowledge_files)
    for f in knowledge_files:
        rel = f.relative_to(project_root)
        text = f.read_text()
        keys, body = _parse_frontmatter(text)
        if not keys:
            errors.append(f"{rel}: missing or invalid frontmatter")
            stats["frontmatter_issues"] += 1
            continue
        _check_frontmatter(keys, rel, errors, stats)
        sections = _extract_sections(body)
        _check_sections(sections, rel, errors, stats)
        _check_correspondence(sections, rel, errors, stats)
        _check_wikilinks(
            text,
            rel,
            knowledge_root,
            all_wikilinks_in_files,
            all_referenced_paths,
            errors,
            stats,
        )
    _check_orphans(
        knowledge_files,
        knowledge_root,
        project_root,
        skill_wikilinks,
        all_wikilinks_in_files,
        errors,
        stats,
    )
    ok = not errors
    return ok, errors, stats


def main() -> int:
    """Run knowledge structure checks and print results."""
    project_root = Path(__file__).resolve().parent.parent
    ok, errors, stats = check_knowledge(project_root)
    print(f"files checked: {stats['files_checked']}")
    print(
        f"issues: {stats['frontmatter_issues']} frontmatter, "
        f"{stats['section_issues']} section, "
        f"{stats['correspondence_issues']} correspondence, "
        f"{stats['wikilink_issues']} wikilink, "
        f"{stats['orphan_issues']} orphan"
    )
    if ok:
        print("OK: all knowledge files pass structure and integrity checks")
        return 0
    for err in errors:
        print(f"ERROR: {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
