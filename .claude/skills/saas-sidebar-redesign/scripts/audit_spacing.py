#!/usr/bin/env python3
"""Audit spacing values in Vue/CSS files.

Reports every distinct padding/margin/gap value, how often it appears, and
which ones are off the 4px scale or hard-coded instead of using var(--space-*).

Usage: python3 audit_spacing.py <src-dir> [--json]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROPS = re.compile(
    r"^\s*(padding|margin|gap|row-gap|column-gap)(-(top|right|bottom|left|inline|block))?\s*:\s*([^;}{]+)",
    re.MULTILINE,
)
LENGTH = re.compile(r"(-?\d*\.?\d+)(px|rem|em)\b")
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL)
ROOT_PX = 16


def to_px(num: float, unit: str) -> float:
    return num if unit == "px" else num * ROOT_PX


def css_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix == ".vue":
        return "\n".join(STYLE_BLOCK.findall(text))
    return text


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        return 2
    root = Path(args[0])
    files = [p for p in root.rglob("*") if p.suffix in {".vue", ".css", ".scss"} and "node_modules" not in p.parts]

    values = Counter()
    off_scale = Counter()
    where = defaultdict(set)
    tokenized = 0
    hardcoded = 0

    for f in files:
        for m in PROPS.finditer(css_of(f)):
            decl = m.group(4).strip()
            if "var(--space" in decl:
                tokenized += 1
            for num, unit in LENGTH.findall(decl):
                n = float(num)
                if n == 0:
                    continue
                hardcoded += 1
                token = f"{num}{unit}"
                values[token] += 1
                where[token].add(str(f.relative_to(root)))
                px = to_px(abs(n), unit)
                # 1px/2px are legit for hairline offsets; everything else should sit on the 4px grid
                if px > 2 and px % 4 != 0:
                    off_scale[token] += 1

    report = {
        "files_scanned": len(files),
        "distinct_values": len(values),
        "hardcoded_lengths": hardcoded,
        "tokenized_declarations": tokenized,
        "off_scale_occurrences": sum(off_scale.values()),
        "off_scale_values": {k: {"count": v, "files": sorted(where[k])} for k, v in off_scale.most_common()},
        "all_values": dict(values.most_common()),
    }

    if as_json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"Files scanned:            {report['files_scanned']}")
    print(f"Hard-coded spacing values: {hardcoded} ({len(values)} distinct)")
    print(f"Declarations using tokens: {tokenized}")
    print(f"Off 4px scale:            {report['off_scale_occurrences']}")
    if off_scale:
        print("\nOff-scale values (value  count  files):")
        for k, v in off_scale.most_common():
            files_str = ", ".join(sorted(where[k])[:4])
            more = "" if len(where[k]) <= 4 else f" +{len(where[k]) - 4} more"
            print(f"  {k:<10} {v:>4}  {files_str}{more}")
    print("\nAll distinct values:")
    print("  " + ", ".join(f"{k}x{v}" for k, v in values.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
