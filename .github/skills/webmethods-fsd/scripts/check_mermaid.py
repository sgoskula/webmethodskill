#!/usr/bin/env python3
"""
check_mermaid.py - Offline lint for Mermaid blocks in Markdown files.

Catches the mistakes that most often stop GitHub / VS Code from rendering a diagram:
unbalanced quotes or brackets, unknown diagram types, alt/loop/opt blocks without `end`,
and `;` inside sequence-diagram text (Mermaid treats it as a statement separator).

Standard library only. Usage:
  python check_mermaid.py docs/FSD.md [more.md ...]     exit code 1 if any block has errors
"""
import re
import sys

BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.S)
KNOWN = {"flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram", "stateDiagram-v2",
         "erDiagram", "gantt", "pie", "journey", "mindmap", "timeline", "gitGraph"}
SEQ_OPENERS = {"alt", "opt", "loop", "par", "critical", "break", "rect"}
PAIRS = {"(": ")", "[": "]", "{": "}"}


def lint_block(src):
    errs = []
    lines = src.splitlines()
    kind = lines[0].strip().split()[0] if lines and lines[0].strip() else ""
    if kind not in KNOWN:
        errs.append(f"line 1: unknown diagram type {kind!r}")
    stack, depth = [], 0
    for no, raw in enumerate(lines[1:], 2):
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        if line.count('"') % 2:
            errs.append(f"line {no}: unbalanced double quote")
            continue
        for ch in re.sub(r'"[^"]*"', '""', line):
            if ch in PAIRS:
                stack.append((PAIRS[ch], no))
            elif ch in PAIRS.values():
                if not stack or stack.pop()[0] != ch:
                    errs.append(f"line {no}: unexpected '{ch}' outside quotes")
                    stack = []
                    break
        word = line.split()[0]
        if kind in ("flowchart", "graph"):
            if word == "subgraph":
                depth += 1
            elif word == "end":
                depth -= 1
                if depth < 0:
                    errs.append(f"line {no}: 'end' without an open subgraph")
                    depth = 0
        if kind == "sequenceDiagram":
            if word in SEQ_OPENERS:
                depth += 1
            elif word == "end":
                depth -= 1
                if depth < 0:
                    errs.append(f"line {no}: 'end' without an open alt/loop/opt block")
                    depth = 0
            if ";" in line:
                errs.append(f"line {no}: ';' splits statements in sequence diagrams; remove it")
    errs += [f"line {no}: '{want}' never closed" for want, no in stack]
    if depth:
        errs.append(f"{depth} block(s) (alt/loop/opt/subgraph) missing 'end'")
    return kind, errs


def main(paths):
    failed = 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            blocks = BLOCK_RE.findall(f.read())
        for i, b in enumerate(blocks, 1):
            kind, errs = lint_block(b)
            status = "OK" if not errs else "ERROR"
            print(f"{path} block {i} ({kind}): {status}")
            for e in errs:
                print(f"    {e}")
            failed += bool(errs)
        if not blocks:
            print(f"{path}: no mermaid blocks")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
