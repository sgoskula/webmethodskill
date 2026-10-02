#!/usr/bin/env python3
"""
assemble_fsd.py - Join the FSD section files into one overall document, in file-name order.

Name section files with a numeric prefix so the order is explicit, e.g.
  00-intro.md  10-architecture.md  20-summary.md  30-CAP-01.md  31-CAP-02.md
  60-common.md  70-reimplementation.md  90-closing.md

Standard library only. Usage:
  python assemble_fsd.py [--sections _fsd_work/sections] [--out docs/FSD.md]
"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default="_fsd_work/sections")
    ap.add_argument("--out", default="docs/FSD.md")
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.sections) if f.endswith(".md"))
    if not files:
        sys.exit(f"No .md section files in {a.sections}")
    parts = []
    for name in files:
        with open(os.path.join(a.sections, name), encoding="utf-8") as f:
            parts.append(f.read().strip("\n"))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    print(f"Assembled {len(files)} section(s) -> {a.out}: " + ", ".join(files))


if __name__ == "__main__":
    main()
