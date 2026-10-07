#!/usr/bin/env python3
"""
assemble_fsd.py - Join the FSD section files into one overall document, in file-name order, and write a
short plain-English summary document next to it.

Name section files with a numeric prefix so the order is explicit, e.g.
  00-intro.md  10-architecture.md  20-summary.md  30-CAP-01.md  31-CAP-02.md
  60-common.md  70-reimplementation.md  90-closing.md

Also writes <out dir>/FSD-summary.md: the title block, "## 0. Summary in Plain English" and each capability's
"In plain English" paragraph. It warns when those are missing or when the summary contains technical jargon.

Standard library only. Usage:
  python assemble_fsd.py [--sections _fsd_work/sections] [--out docs/FSD.md] [--summary-out docs/FSD-summary.md]
"""
import argparse
import os
import re
import sys

JARGON = [r"\$default", r"\$null", r"ISRuntimeException", r"\bMAP(SET|COPY)?\b", r"\bBRANCH\b", r"\bINVOKE\b",
          r"\bpub\.", r"flow\.xml", r"node\.ndf", r"\bpipeline\b", r"\bIData\b", r"\bTRY\b", r"\bCATCH\b",
          r"`[A-Za-z_.]+:[A-Za-z_]+`"]
SUMMARY_HEAD = "## 0. Summary in Plain English"


def summary_doc(text):
    """Title block + section 0 + the 'In plain English' paragraph of every capability."""
    title = text.split("\n## ", 1)[0].strip()
    m = re.search(re.escape(SUMMARY_HEAD) + r".*?(?=\n## )", text, re.S)
    out = [title, "", m.group(0).strip() if m else SUMMARY_HEAD + "\n\n_Missing._", "",
           "## Capabilities in plain English", ""]
    for h in re.finditer(r"^### (5\.\d+ [^\n]+)\n+\*\*In plain English:\*\* (.*?)(?=\n\n|\Z)", text, re.S | re.M):
        out += [f"**{h.group(1)}.** " + " ".join(h.group(2).split()), ""]
    out += ["_Full detail, diagrams and open questions are in the complete FSD._"]
    return "\n".join(out) + "\n"


def readability_warnings(text):
    warn = []
    m = re.search(re.escape(SUMMARY_HEAD) + r".*?(?=\n## )", text, re.S)
    if not m:
        warn.append(f"missing section '{SUMMARY_HEAD}'")
    else:
        bad = sorted({j for pat in JARGON for j in re.findall(pat, m.group(0))} or [])
        if bad:
            warn.append("plain-English summary contains technical terms: " + ", ".join(map(str, bad)))
        if len(m.group(0).split()) > 700:
            warn.append("plain-English summary is longer than ~700 words; shorten it")
    caps = re.findall(r"^### (5\.\d+ [^\n]+)\n+(\*\*In plain English:\*\*)?", text, re.M)
    for name, has in caps:
        if not has:
            warn.append(f"capability '{name}' has no 'In plain English' paragraph")
    return warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default="_fsd_work/sections")
    ap.add_argument("--out", default="docs/FSD.md")
    ap.add_argument("--summary-out", default=None, help="default: FSD-summary.md next to --out")
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.sections) if f.endswith(".md"))
    if not files:
        sys.exit(f"No .md section files in {a.sections}")
    parts = []
    for name in files:
        with open(os.path.join(a.sections, name), encoding="utf-8") as f:
            parts.append(f.read().strip("\n"))
    text = "\n\n".join(parts) + "\n"
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    summary_out = a.summary_out or os.path.join(os.path.dirname(a.out) or ".", "FSD-summary.md")
    with open(summary_out, "w", encoding="utf-8") as f:
        f.write(summary_doc(text))
    print(f"Assembled {len(files)} section(s) -> {a.out}, summary -> {summary_out}: " + ", ".join(files))
    for w in readability_warnings(text):
        print("READABILITY WARNING:", w)


if __name__ == "__main__":
    main()
