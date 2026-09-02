#!/usr/bin/env python3
"""Normalize GitHub-Flavored Markdown tables across the repo.

Fixes the failure modes seen in generated files:
- separator rows whose column count no longer matches header/body rows
- rows with fewer/more cells than the table's canonical column count

Every table block is normalized to a consistent column count (the maximum
seen in that block, so no data is ever dropped), with a regenerated
separator row. Files are rewritten only when content actually changes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGETS = [ROOT / "reports", ROOT / "select"]
_SEP_CELL = re.compile(r"^\s*:?-{2,}:?\s*$")


def is_separator_row(cells):
    return bool(cells) and all(_SEP_CELL.match(c) for c in cells)


def normalize_block(lines):
    """lines: consecutive raw markdown lines starting with '|'."""
    parsed = []
    for line in lines:
        body = line.strip()
        body = body[1:] if body.startswith("|") else body
        body = body[:-1] if body.endswith("|") else body
        parsed.append([c.strip() for c in body.split("|")])

    sep_idx = 1 if len(parsed) > 1 and is_separator_row(parsed[1]) else None
    ncols = max(len(row) for row in parsed)

    out = []
    for idx, cells in enumerate(parsed):
        if sep_idx is not None and idx == sep_idx:
            aligns = []
            for c in cells[:ncols]:
                if len(c) > 2 and c.startswith(":") and c.endswith(":"):
                    aligns.append(":---:")
                elif c.endswith(":"):
                    aligns.append("---:")
                elif c.startswith(":"):
                    aligns.append(":---")
                else:
                    aligns.append("---")
            aligns += ["---"] * (ncols - len(aligns))
            out.append("| " + " | ".join(aligns) + " |")
        else:
            padded = (cells + [""] * ncols)[:ncols]
            out.append("| " + " | ".join(padded) + " |")
    return out


def fix_markdown(text):
    lines = text.splitlines()
    out = []
    i = 0
    in_fence = False
    changed = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue
        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            fixed = normalize_block(block)
            if fixed != block:
                changed += 1
            out.extend(fixed)
        else:
            out.append(line)
            i += 1
    return "\n".join(out), changed


def main():
    changed_files = []
    total_tables = 0
    targets = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else TARGETS
    for target in targets:
        if target.is_file():
            files = [target]
        else:
            files = sorted(target.rglob("*.md"))
        for f in files:
            text = f.read_text(encoding="utf-8")
            fixed, n = fix_markdown(text)
            total_tables += n
            if fixed != text:
                f.write_text(fixed, encoding="utf-8")
                changed_files.append(str(f))
    if changed_files:
        print(f"Fixed {total_tables} table block(s) in {len(changed_files)} file(s):")
        for name in changed_files:
            print(f"  {name}")
    else:
        print(f"No table issues found ({total_tables} blocks checked).")
    return 0 if changed_files else 0


if __name__ == "__main__":
    sys.exit(main())
