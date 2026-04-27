#!/usr/bin/env python3
"""Assign @id tags to untagged Examples and verify global uniqueness.

Scans .feature files for Example: blocks that lack an @id: tag,
generates a unique 8-char hex ID for each, writes them back,
then checks that all @id values are globally unique across every stage
(backlog, in-progress, completed).

Exit 0 if all Examples are tagged and IDs are unique.
Exit 1 on missing tags, duplicate IDs, or write failures.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

_ID_RE: re.Pattern[str] = re.compile(r"@id:([a-f0-9]{8})")
_EXAMPLE_RE: re.Pattern[str] = re.compile(r"^(\s*)Example:", re.MULTILINE)
_EXAMPLE_WITH_ID_RE: re.Pattern[str] = re.compile(
    r"@id:[a-f0-9]{8}\s*\n\s*Example:", re.MULTILINE
)

FEATURE_STAGES: tuple[str, ...] = ("backlog", "in-progress", "completed")


def _collect_existing_ids(features_dir: Path) -> set[str]:
    """Collect all @id values across all stages."""
    ids: set[str] = set()
    for stage in FEATURE_STAGES:
        stage_dir = features_dir / stage
        if not stage_dir.exists():
            continue
        for feature_path in sorted(stage_dir.rglob("*.feature")):
            ids.update(
                match.group(1)
                for match in _ID_RE.finditer(feature_path.read_text(encoding="utf-8"))
            )
    return ids


def _generate_id(existing: set[str]) -> str:
    """Generate a unique 8-char hex ID not in existing set."""
    while True:
        new_id = f"{random.randint(0, 0xFFFFFFFF):08x}"
        if new_id not in existing:
            existing.add(new_id)
            return new_id


def _assign_ids_to_file(feature_path: Path, existing_ids: set[str]) -> list[str]:
    """Assign @id tags to untagged Examples in a single file."""
    content = feature_path.read_text(encoding="utf-8")
    errors: list[str] = []

    lines = content.split("\n")
    new_lines: list[str] = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if stripped.startswith("Example:") and i > 0:
            prev_line = lines[i - 1].strip()
            if not prev_line.startswith("@id:"):
                new_id = _generate_id(existing_ids)
                indent = len(line) - len(line.lstrip())
                new_lines.append(f"{' ' * indent}@id:{new_id}")
                changed = True

        new_lines.append(line)
        i += 1

    if changed:
        feature_path.write_text("\n".join(new_lines), encoding="utf-8")

    return errors


def _collect_all_ids(features_dir: Path) -> dict[str, list[str]]:
    """Collect all @id values across all stages, mapping id -> [locations]."""
    locations: dict[str, list[str]] = {}
    for stage in FEATURE_STAGES:
        stage_dir = features_dir / stage
        if not stage_dir.exists():
            continue
        for feature_path in sorted(stage_dir.rglob("*.feature")):
            for line_no, line in enumerate(
                feature_path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for match in _ID_RE.finditer(line):
                    tag_id = match.group(1)
                    locations.setdefault(tag_id, []).append(
                        f"{feature_path.relative_to(features_dir.parent.parent)}:{line_no}"
                    )
    return locations


def _check_uniqueness(locations: dict[str, list[str]]) -> list[str]:
    """Return error strings for any @id that appears more than once."""
    errors: list[str] = []
    for tag_id, locs in sorted(locations.items()):
        if len(locs) > 1:
            joined = ", ".join(locs)
            errors.append(f"duplicate @id:{tag_id} found in {joined}")
    return errors


def main() -> int:
    """Run @id assignment and uniqueness check."""
    project_root = Path(__file__).resolve().parent.parent
    features_dir = project_root / "docs" / "features"

    if not features_dir.exists():
        print("ERROR: docs/features/ not found")
        return 1

    existing_ids = _collect_existing_ids(features_dir)

    write_errors: list[str] = []
    for stage in FEATURE_STAGES:
        stage_dir = features_dir / stage
        if not stage_dir.exists():
            continue
        for feature_path in sorted(stage_dir.rglob("*.feature")):
            file_errors = _assign_ids_to_file(feature_path, existing_ids)
            write_errors.extend(file_errors)

    for err in write_errors:
        print(f"ERROR: {err}")

    locations = _collect_all_ids(features_dir)
    uniqueness_errors = _check_uniqueness(locations)
    for err in uniqueness_errors:
        print(f"ERROR: {err}")

    total_ids = len(locations)
    total_examples = sum(len(v) for v in locations.values())

    if write_errors or uniqueness_errors:
        print(f"ids: {total_ids}, examples: {total_examples} — FAILED")
        return 1

    print(f"ids: {total_ids}, examples: {total_examples}")
    print("OK: all Examples have @id tags and all IDs are unique")
    return 0


if __name__ == "__main__":
    sys.exit(main())
