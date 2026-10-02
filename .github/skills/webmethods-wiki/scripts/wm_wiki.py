#!/usr/bin/env python3
"""
wm_wiki.py - Build a browsable wiki and a question-answering index from wm_extract.py output.

Input : the extract folder written by webmethods-fsd/scripts/wm_extract.py
        (inventory.json, architecture.md, callgraphs.md, services/*.md)
Output: <out>/
          index.md              start page: packages, capabilities, links
          architecture.md       copy of the existing-architecture facts
          findings.md           every semantic flag and architecture observation
          capabilities/*.md     one page per entry point: components and call graph
          services/*.md         one page per node, with cross-links
          tables/*.md           one page per database table: who reads and writes it
          chunks.jsonl          retrieval chunks for wm_ask.py
          llm_context.md        whole application in one file (no diagrams) to paste into an LLM

Standard library only (Python 3.8+).
  python wm_wiki.py --extract _fsd_work/extract --out _wiki
"""
import argparse
import json
import os
import re
import sys


def safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name.replace(":", "__"))


def split_sections(md):
    """Return [(heading, body)] where the first heading is 'Overview'. Mermaid blocks are dropped."""
    md = re.sub(r"```mermaid.*?```", "", md, flags=re.S)
    parts = re.split(r"^## ", md, flags=re.M)
    out = [("Overview", parts[0].strip())]
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out.append((head.strip(), body.strip()))
    return [(h, b) for h, b in out if b and b != "_(none)_"]


def link_names(text, names, prefix=""):
    def sub(m):
        n = m.group(1)
        return f"[`{n}`]({prefix}{safe(n)}.md)" if n in names else m.group(0)
    return re.sub(r"`([^`\n]+)`", sub, text)


def split_big(text, limit=2500):
    """Split long section text on blank lines or lines so retrieval chunks stay small."""
    if len(text) <= limit:
        return [text]
    chunks, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) > limit and cur:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    return chunks + ([cur] if cur.strip() else [])


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", default="_fsd_work/extract")
    ap.add_argument("--out", default="_wiki")
    a = ap.parse_args()

    inv_path = os.path.join(a.extract, "inventory.json")
    if not os.path.isfile(inv_path):
        sys.exit(f"{inv_path} not found: run webmethods-fsd/scripts/wm_extract.py first")
    with open(inv_path, encoding="utf-8") as f:
        inv = json.load(f)
    arch = inv["architecture"]
    nodes = inv["nodes"]
    names = set(nodes)
    roles = arch["roles"]
    flags = inv.get("semantic_flags", {})
    chunks = []

    def add_chunk(source, title, text, service=""):
        for i, t in enumerate(split_big(text)):
            chunks.append({"id": f"{source}#{len(chunks)}", "source": source, "service": service,
                           "title": title + (f" (part {i + 1})" if i else ""), "text": t.strip()})

    # ---- services
    svc_dir = os.path.join(a.extract, "services")
    llm = []
    for name in sorted(names):
        path = os.path.join(svc_dir, safe(name) + ".md")
        if not os.path.isfile(path):
            continue
        raw = open(path, encoding="utf-8").read()
        sections = split_sections(raw)
        page = [f"# {name}", "", f"[← index](../index.md) · kind: **{nodes[name]['kind']}** · "
                f"role: {roles.get(name, '')}", ""]
        for head, body in sections:
            if head == "Overview":
                body = "\n".join(l for l in body.split("\n") if not l.startswith("# "))
            if head in ("Overview", "Invokes") or "Invoked by" in body:
                body = link_names(body, names)
            page += [f"## {head}", "", body, ""]
            add_chunk("services/" + safe(name) + ".md", f"{name} - {head}",
                      f"[{name}] {head}\n{body}", name)
        flow = re.search(r"## Flowchart\n(```mermaid.*?```)", raw, re.S)
        if flow:
            page += ["## Flowchart", "", flow.group(1), ""]
        write(os.path.join(a.out, "services", safe(name) + ".md"), "\n".join(page))
        llm.append(f"\n### {name}\n" + "\n\n".join(
            f"**{h}**\n{b}" for h, b in sections if h != "Overview" or b))

    # ---- capabilities
    cg = {}
    cgp = os.path.join(a.extract, "callgraphs.md")
    if os.path.isfile(cgp):
        for m in re.finditer(r"^## (.+?)\n\n(```mermaid.*?```)", open(cgp, encoding="utf-8").read(), re.S | re.M):
            cg[m.group(1)] = m.group(2)
    cap_links = []
    for root in arch["roots"]:
        comps = arch["capability_components"].get(root, [])
        body = [f"# Capability: {root}", "", f"[← index](../index.md) · {roles.get(root, '')}", "",
                "## Components used", ""]
        body += [f"- [`{c}`](../services/{safe(c)}.md) - {roles.get(c, '')}" for c in comps]
        body += ["", "## Findings in this capability", ""]
        body += [f"- `{c}`: {f}" for c in comps for f in flags.get(c, [])] or ["- none"]
        if root in cg:
            body += ["", "## Call graph", "", cg[root]]
        write(os.path.join(a.out, "capabilities", safe(root) + ".md"), "\n".join(body))
        add_chunk("capabilities/" + safe(root) + ".md", f"capability {root}",
                  f"[capability {root}] {roles.get(root, '')}. Components: " + ", ".join(comps), root)
        cap_links.append(f"- [`{root}`](capabilities/{safe(root)}.md) - {roles.get(root, '')} "
                         f"({len(comps)} components)")

    # ---- tables
    tbl_links = []
    adapters = arch.get("adapters", {})
    for t, caps in sorted(arch["data_access"].items()):
        users = sorted(s for s, i in adapters.items() if t in i["tables"])
        body = [f"# Table {t}", "", "[← index](../index.md)", "", "## Capabilities and operations", ""]
        body += [f"- [`{c}`](../capabilities/{safe(c)}.md): {'/'.join(ops)}" for c, ops in sorted(caps.items())]
        body += ["", "## Adapter services touching it", ""]
        body += [f"- [`{s}`](../services/{safe(s)}.md) ({'/'.join(adapters[s]['operations'])}, "
                 f"connection `{adapters[s]['connection']}`)" for s in users]
        write(os.path.join(a.out, "tables", safe(t) + ".md"), "\n".join(body))
        add_chunk("tables/" + safe(t) + ".md", f"table {t}", f"[table {t}] " + "; ".join(
            f"{c} {'/'.join(o)}" for c, o in sorted(caps.items())) + ". Adapters: " + ", ".join(users), t)
        tbl_links.append(f"- [`{t}`](tables/{safe(t)}.md) - used by {len(caps)} capabilit(y/ies)")

    # ---- Trading Networks
    tn = arch.get("trading_networks", {})
    if tn:
        body = ["# Trading Networks usage", "", "[← index](index.md)", "",
                "Calls to Trading Networks, grouped by operation. Partner profiles, document types, processing rules "
                "and delivery settings are configured in TN, outside the packages, so they are not in this wiki.", ""]
        for op, cs in tn.items():
            body += [f"## {op}", ""]
            for k, calls in cs.items():
                for c in calls:
                    inputs = "; ".join(c["inputs"]) or "no mapped inputs"
                    body.append(f"- [`{k}`](services/{safe(k)}.md) calls `{c['service']}`: {inputs}")
                    add_chunk("trading-networks.md", f"Trading Networks - {op}",
                              f"[Trading Networks: {op}] {k} calls {c['service']} with {inputs}", k)
            body.append("")
        write(os.path.join(a.out, "trading-networks.md"), "\n".join(body))

    # ---- findings
    fnd = ["# Findings", "", "[← index](index.md)", "", "Automatic leads from the extractor: verify before relying "
           "on them.", "", "## Per service", ""]
    for s in sorted(flags):
        fnd.append(f"### [`{s}`](services/{safe(s)}.md)")
        fnd += [f"- {x}" for x in flags[s]] + [""]
        add_chunk("findings.md", f"findings {s}", f"[findings for {s}]\n" + "\n".join(flags[s]), s)
    obs = arch.get("observations", [])
    fnd += ["## Across services", ""] + [f"- {o}" for o in obs]
    if obs:
        add_chunk("findings.md", "architecture observations", "[architecture observations]\n" + "\n".join(obs))
    write(os.path.join(a.out, "findings.md"), "\n".join(fnd))

    # ---- architecture
    ap_ = os.path.join(a.extract, "architecture.md")
    if os.path.isfile(ap_):
        raw = open(ap_, encoding="utf-8").read()
        write(os.path.join(a.out, "architecture.md"), "[← index](index.md)\n\n" + raw)
        for h, b in split_sections(raw):
            add_chunk("architecture.md", f"architecture - {h}", f"[architecture] {h}\n{b}")

    # ---- index
    idx = ["# Application wiki", "", "Generated from the webMethods packages. Every page is derived from the code; "
           "nothing is guessed. Ask questions with `wm_ask.py` or paste `llm_context.md` into an LLM.", "",
           "## Packages", ""]
    idx += [f"- `{p['package']}` {p.get('version', '')} (requires: {', '.join(p['requires']) or 'none'})"
            for p in inv["packages"]]
    idx += ["", "## Capabilities (entry points)", ""] + cap_links
    idx += ["", "## Tables", ""] + (tbl_links or ["- none"])
    idx += ["", "## Other", "", "- [Architecture](architecture.md)", "- [Findings](findings.md)"] + \
           (["- [Trading Networks usage](trading-networks.md)"] if tn else []) + [""] + [
           
            "## All components", ""]
    idx += [f"- [`{n}`](services/{safe(n)}.md) - {nodes[n]['kind']}; {roles.get(n, '')}" for n in sorted(names)]
    write(os.path.join(a.out, "index.md"), "\n".join(idx))

    # ---- chunks + llm context
    with open(os.path.join(a.out, "chunks.jsonl"), "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
    ctx = ["# Application context for LLM questions", "",
           "Facts extracted from webMethods Integration Server packages. Answer only from this text.", ""]
    ctx += ["## Capabilities"] + [f"- {r}: {roles.get(r, '')}" for r in arch["roots"]]
    ctx += ["", "## Findings"] + [f"- {s}: {x}" for s in sorted(flags) for x in flags[s]] + \
           [f"- {o}" for o in obs]
    ctx += ["", "## Components"] + llm
    text = "\n".join(ctx) + "\n"
    write(os.path.join(a.out, "llm_context.md"), text)
    print(f"Wiki: {len(names)} service pages, {len(chunks)} chunks, llm_context.md ~{len(text) // 4} tokens -> {a.out}")


if __name__ == "__main__":
    main()
