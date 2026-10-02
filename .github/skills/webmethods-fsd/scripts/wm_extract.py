#!/usr/bin/env python3
"""
wm_extract.py - Deterministic extractor for webMethods Integration Server packages.

Reads IS package folders (manifest.v3, ns/**/node.ndf, ns/**/flow.xml, code/source/*.java)
and writes compact, LLM-friendly facts so the FSD agent never has to reason over raw XML:

  <out>/inventory.md        overview: packages, dependencies, counts, entry points, integrations
  <out>/inventory.json      same data, machine-readable
  <out>/services/<ns>.md    one file per service/node: signature, pseudocode, mermaid flowchart,
                            invokes / invoked-by, raw properties for adapters/triggers/etc.
  <out>/callgraphs.md       mermaid call graph per entry point

Standard library only (Python 3.8+). Usage:
  python wm_extract.py --out _fsd_work/extract <package_dir> [<package_dir> ...]
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

# ---------------------------------------------------------------- integrations
INTEGRATION_PREFIXES = [
    ("pub.client:http", "HTTP/REST call"),
    ("pub.client:soap", "SOAP call"),
    ("pub.client:ftp", "FTP"),
    ("pub.client:sftp", "SFTP"),
    ("pub.client:smtp", "Email (SMTP)"),
    ("pub.jms:", "JMS messaging"),
    ("pub.publish:", "Publish/subscribe (Broker/UM)"),
    ("pub.mqtt", "MQTT"),
    ("pub.file:", "File system"),
    ("pub.flatFile:", "Flat file parsing"),
    ("pub.xml:", "XML handling"),
    ("pub.json:", "JSON handling"),
    ("pub.cache", "Cache"),
    ("pub.storage:", "IS storage/locking"),
    ("pub.art.", "Adapter runtime"),
    ("wm.tn", "Trading Networks"),
    ("pub.remote:", "Remote IS invoke"),
    ("pub.event:", "Event/exception handling"),
]
SQL_RE = re.compile(r"\b(select|insert\s+into|update|delete\s+from|merge\s+into|call|exec)\b", re.I)


def classify_invoke(svc):
    for prefix, label in INTEGRATION_PREFIXES:
        if svc.startswith(prefix):
            return label
    return None


# ---------------------------------------------------------------- IData (node.ndf) parsing
def idata_to_py(el):
    tag = el.tag.lower()
    if tag in ("values", "record"):
        d = {}
        for child in el:
            d[child.get("name", child.tag)] = idata_to_py(child)
        return d
    if tag in ("array", "list"):
        return [idata_to_py(c) for c in el]
    if tag == "null":
        return None
    return (el.text or "").strip()


def load_ndf(path):
    try:
        return idata_to_py(ET.parse(path).getroot())
    except Exception as exc:  # malformed or binary
        return {"_parse_error": str(exc)}


def flatten(obj, prefix="", out=None, limit=400):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, f"{prefix}.{k}" if prefix else k, out, limit)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flatten(v, f"{prefix}[{i}]", out, limit)
    elif obj not in (None, ""):
        s = str(obj)
        if re.search(r"pass(word)?|secret|token|credential", prefix, re.I):
            s = "***redacted***"
        out.append((prefix, s[:500]))
    return out


def fields_table(rec_fields, depth=0, rows=None):
    rows = [] if rows is None else rows
    for f in rec_fields or []:
        if not isinstance(f, dict):
            continue
        name = f.get("field_name", "?")
        ftype = f.get("field_type", "")
        dim = f.get("field_dim", "0")
        ref = f.get("rec_ref", "")
        arr = "[]" * int(dim) if str(dim).isdigit() else ""
        opt = "optional" if f.get("field_opt") == "true" else ""
        nill = "nillable" if f.get("nillable") == "true" else ""
        comment = (f.get("node_comment") or "").replace("\n", " ")
        rows.append(("  " * depth + name + arr, ftype + (f" → {ref}" if ref else ""),
                     " ".join(x for x in (opt, nill) if x), comment))
        fields_table(f.get("rec_fields"), depth + 1, rows)
    return rows


def sig_section(title, rec):
    rows = fields_table((rec or {}).get("rec_fields"))
    if not rows:
        return f"**{title}:** _(none)_\n"
    md = [f"**{title}:**\n", "| Field | Type | Flags | Comment |", "|---|---|---|---|"]
    md += [f"| `{a}` | {b} | {c} | {d} |" for a, b, c, d in rows]
    return "\n".join(md) + "\n"


# ---------------------------------------------------------------- flow.xml parsing
def clean_path(p):
    if not p:
        return ""
    segs = [s.split(";")[0] for s in p.strip("/").split("/") if s]
    return "/".join(segs)


def mapset_value(el):
    data = el.find(".//DATA")
    if data is None:
        return ""
    for v in data.iter():
        if v.tag.lower() == "value" and v.text:
            return v.text.strip()
    return ""


def describe_map(map_el):
    ops = []
    for c in map_el:
        t = c.tag
        if t == "MAPCOPY":
            ops.append(f"{clean_path(c.get('TO'))} ← {clean_path(c.get('FROM'))}")
        elif t == "MAPSET":
            val = mapset_value(c)
            var = " (with %var% substitution)" if c.get("VARIABLES") == "true" else ""
            ops.append(f'set {clean_path(c.get("FIELD"))} = "{val}"{var}')
        elif t == "MAPDELETE":
            ops.append(f"drop {clean_path(c.get('FIELD'))}")
        elif t == "MAPINVOKE":
            inner = []
            for m in c.findall("MAP"):
                inner += describe_map(m)
            ops.append(f"transformer {c.get('SERVICE')}" + (f" [{'; '.join(inner)}]" if inner else ""))
    return ops


def comment_of(el):
    c = el.find("COMMENT")
    txt = (c.text or "").strip() if c is not None else ""
    return txt


STEP_TAGS = {"SEQUENCE", "BRANCH", "LOOP", "RETRY", "REPEAT", "INVOKE", "MAP", "EXIT"}


class FlowWalker:
    def __init__(self):
        self.lines = []
        self.invokes = []
        self.mm = []
        self.nid = 0
        self.truncated = False
        self.max_nodes = 120

    def new_node(self, label, shape="rect"):
        self.nid += 1
        if self.nid > self.max_nodes:
            self.truncated = True
        nid = f"n{self.nid}"
        label = label.replace('"', "'").replace("\n", " ")[:90]
        s = {"rect": f'{nid}["{label}"]', "dia": f'{nid}{{"{label}"}}',
             "stad": f'{nid}(["{label}"])', "round": f'{nid}("{label}")'}[shape]
        self.mm.append("  " + s)
        return nid

    def edge(self, srcs, dst, label=None):
        for s in srcs:
            self.mm.append(f'  {s} -->|"{label}"| {dst}' if label else f"  {s} --> {dst}")

    def walk_children(self, el, depth, prev):
        try_ctx = None  # (try_node, exits_after_try) for TRY/CATCH/FINALLY siblings
        for c in el:
            if c.tag not in STEP_TAGS:
                continue
            form = (c.get("FORM") or "").upper() if c.tag == "SEQUENCE" else ""
            if form == "TRY":
                self._pending_try = None
                prev = self.walk(c, depth, prev)
                try_ctx = (self._pending_try, prev)
            elif form == "CATCH" and try_ctx and try_ctx[0]:
                self._catch_from = try_ctx[0]
                catch_exits = self.walk(c, depth, [])
                prev = list(try_ctx[1]) + catch_exits
                try_ctx = None
            else:
                prev = self.walk(c, depth, prev)
        return prev

    def walk(self, el, depth, prev):
        ind = "  " * depth
        t = el.tag
        disabled = el.get("DISABLED") == "true"
        cmt = comment_of(el)
        if cmt:
            self.lines.append(f"{ind}# {cmt}")
        if disabled:
            self.lines.append(f"{ind}({t} {el.get('SERVICE', '')} DISABLED — not executed)")
            return prev
        label = el.get("NAME") or el.get("LABEL")

        if t == "SEQUENCE":
            form = el.get("FORM", "")
            kind = {"TRY": "TRY", "CATCH": "CATCH", "FINALLY": "FINALLY"}.get(form.upper(), "SEQUENCE")
            exit_on = el.get("EXIT-ON", "")
            self.lines.append(f"{ind}{kind}{' ['+label+']' if label else ''}"
                              f"{' (exit on '+exit_on+')' if exit_on else ''}")
            if kind != "SEQUENCE":
                n = self.new_node(kind + (f": {label}" if label else ""), "round")
                if kind == "CATCH" and getattr(self, "_catch_from", None):
                    self.edge([self._catch_from], n, "on error")
                    self._catch_from = None
                else:
                    self.edge(prev, n)
                if kind == "TRY":
                    self._pending_try = n
                prev = [n]
            return self.walk_children(el, depth + 1, prev)

        if t == "BRANCH":
            switch = clean_path(el.get("SWITCH"))
            expr = el.get("LABELEXPRESSIONS") == "true"
            head = f"BRANCH on {switch}" if switch else "BRANCH (evaluate labels as conditions)"
            self.lines.append(ind + head)
            n = self.new_node(head, "dia")
            self.edge(prev, n)
            exits, has_default = [], False
            for c in el:
                if c.tag not in STEP_TAGS:
                    continue
                case = c.get("NAME") or "(unlabelled)"
                has_default |= case == "$default"
                kind = "WHEN" if expr else "CASE"
                self.lines.append(f"{ind}  {kind} {case}:")
                exits += self.walk(c, depth + 2, [n])
                # re-label the first edge of this case
                for i in range(len(self.mm) - 1, -1, -1):
                    if self.mm[i].startswith(f"  {n} --> "):
                        self.mm[i] = self.mm[i].replace(f"{n} --> ", f'{n} -->|"{case[:40]}"| ', 1)
                        break
            if not has_default:
                self.lines.append(f"{ind}  (no $default: unmatched values fall through)")
                exits.append(n)
            return exits

        if t == "LOOP":
            arr, out = clean_path(el.get("IN-ARRAY")), clean_path(el.get("OUT-ARRAY"))
            head = f"LOOP over {arr}" + (f" → collect {out}" if out else "")
            self.lines.append(ind + head)
            n = self.new_node(head, "stad")
            self.edge(prev, n)
            body_exit = self.walk_children(el, depth + 1, [n])
            self.edge([b for b in body_exit if b != n], n, "next")
            return [n]

        if t in ("RETRY", "REPEAT"):
            head = (f"REPEAT up to {el.get('COUNT')} times on {el.get('LOOP-ON', 'FAILURE')}"
                    f" (backoff {el.get('BACK-OFF', '0')}s)")
            self.lines.append(ind + head)
            n = self.new_node(head, "stad")
            self.edge(prev, n)
            body_exit = self.walk_children(el, depth + 1, [n])
            self.edge([b for b in body_exit if b != n], n, "retry")
            return [n]

        if t == "INVOKE":
            svc = el.get("SERVICE", "?")
            self.invokes.append(svc)
            kind = classify_invoke(svc)
            self.lines.append(f"{ind}INVOKE {svc}" + (f"   ⟵ {kind}" if kind else ""))
            for m in el.findall("MAP"):
                ops = describe_map(m)
                if ops:
                    self.lines.append(f"{ind}  {m.get('MODE', '').lower() or 'map'}: " + "; ".join(ops))
            n = self.new_node(("⚡ " if kind else "") + svc)
            self.edge(prev, n)
            return [n]

        if t == "MAP":
            ops = describe_map(el)
            for m in el.findall("MAPINVOKE"):
                self.invokes.append(m.get("SERVICE", "?"))
            self.lines.append(f"{ind}MAP{' ['+label+']' if label else ''}: " + ("; ".join(ops) or "(no ops)"))
            if not ops:
                return prev
            n = self.new_node(f"MAP: {len(ops)} op(s)")
            self.edge(prev, n)
            return [n]

        if t == "EXIT":
            frm, sig = el.get("FROM", "$parent"), el.get("SIGNAL", "SUCCESS")
            msg = el.get("FAILURE-MESSAGE", "")
            txt = f"EXIT from {frm} signal {sig}" + (f' message "{msg}"' if msg else "")
            self.lines.append(ind + txt)
            n = self.new_node(txt, "stad")
            self.edge(prev, n)
            return [] if (sig == "FAILURE" or frm == "$flow") else [n]
        return prev


def parse_flow(path):
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return {"error": str(exc), "lines": [], "invokes": [], "mermaid": ""}
    w = FlowWalker()
    start = w.new_node("Start", "stad")
    ends = w.walk_children(root, 0, [start])
    end = w.new_node("End", "stad")
    w.edge(ends, end)
    mermaid = "" if w.truncated else "flowchart TD\n" + "\n".join(w.mm)
    return {"lines": w.lines, "invokes": w.invokes, "mermaid": mermaid, "truncated": w.truncated}


# ---------------------------------------------------------------- java source
def java_body(pkg_dir, ns_folder, svc):
    src = os.path.join(pkg_dir, "code", "source", *ns_folder.split(".")) + ".java"
    if not os.path.isfile(src):
        return None
    text = open(src, encoding="utf-8", errors="replace").read()
    m = re.search(r"<<IS-START\(" + re.escape(svc) + r"\)>>.*?\n(.*?)//\s*---\s*<<IS-END>>", text, re.S)
    return (m.group(1).strip() if m else None), src


# ---------------------------------------------------------------- package walk
def scan_package(pkg_dir):
    pkg = os.path.basename(os.path.normpath(pkg_dir))
    info = {"package": pkg, "requires": [], "startup": [], "shutdown": [], "nodes": []}
    man = os.path.join(pkg_dir, "manifest.v3")
    if os.path.isfile(man):
        m = load_ndf(man)
        info["version"] = m.get("version", "")
        req = m.get("requires") or {}
        info["requires"] = list(req.keys()) if isinstance(req, dict) else []
        for k in ("startup_services", "shutdown_services"):
            v = m.get(k) or {}
            info[k.split("_")[0]] = list(v.keys()) if isinstance(v, dict) else []
    ns_root = os.path.join(pkg_dir, "ns")
    for dirpath, _, files in os.walk(ns_root):
        if "node.ndf" not in files:
            continue
        rel = os.path.relpath(dirpath, ns_root).split(os.sep)
        if rel == ["."]:
            continue
        folder, name = ".".join(rel[:-1]), rel[-1]
        fq = f"{folder}:{name}" if folder else name
        ndf = load_ndf(os.path.join(dirpath, "node.ndf"))
        node = {
            "name": fq, "package": pkg, "folder": folder,
            "node_type": ndf.get("node_type", ""), "svc_type": ndf.get("svc_type", ""),
            "svc_subtype": ndf.get("svc_subtype", ""),
            "comment": (ndf.get("node_comment") or "").strip(),
            "ndf": ndf, "dir": dirpath,
        }
        if os.path.isfile(os.path.join(dirpath, "flow.xml")):
            node["flow"] = parse_flow(os.path.join(dirpath, "flow.xml"))
        if node["svc_type"] == "java":
            jb = java_body(pkg_dir, folder, name)
            if jb:
                node["java"], node["java_src"] = jb
        info["nodes"].append(node)
    return info


def kind_of(n):
    st, nt = n["svc_type"].lower(), n["node_type"].lower()
    if st:
        return {"flow": "Flow service", "java": "Java service", "spec": "Specification"}.get(st, f"{n['svc_type']} service")
    if "record" in nt:
        return "Document type"
    if "trigger" in nt:
        return "Trigger"
    if "conn" in nt or "connection" in nt:
        return "Adapter connection"
    if "notif" in nt or "listener" in nt:
        return n["node_type"]
    return n["node_type"] or "Other"


# ---------------------------------------------------------------- outputs
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("packages", nargs="+")
    ap.add_argument("--out", default="_fsd_work/extract")
    a = ap.parse_args()

    pkgs = [scan_package(p) for p in a.packages]
    nodes = {n["name"]: n for p in pkgs for n in p["nodes"]}
    invoked_by = defaultdict(set)
    referenced = defaultdict(set)  # non-flow nodes (triggers, REST, WSD) mentioning services
    for n in nodes.values():
        for s in (n.get("flow") or {}).get("invokes", []):
            invoked_by[s].add(n["name"])
        if not n.get("flow"):
            blob = json.dumps(n["ndf"])
            for other in nodes:
                if other != n["name"] and ":" in other and other in blob:
                    referenced[other].add(n["name"])

    services = [n for n in nodes.values() if n["svc_type"]]
    entry = sorted(s["name"] for s in services
                   if s["svc_type"] in ("flow", "java") and not invoked_by.get(s["name"]))
    triggered = sorted(k for k in referenced if k in nodes and nodes[k]["svc_type"])
    integrations = defaultdict(set)
    external = defaultdict(set)
    for n in nodes.values():
        for s in (n.get("flow") or {}).get("invokes", []):
            k = classify_invoke(s)
            if k:
                integrations[k].add(n["name"])
            elif s not in nodes and not s.startswith("pub."):
                external[s].add(n["name"])
        if n["svc_type"] and n["svc_type"] not in ("flow", "java", "spec"):
            integrations[f"Adapter service ({n['svc_type']})"].add(n["name"])

    os.makedirs(os.path.join(a.out, "services"), exist_ok=True)

    # per-node files
    for n in nodes.values():
        md = [f"# {n['name']}", "", f"- **Kind:** {kind_of(n)}", f"- **Package:** {n['package']}",
              f"- **Source dir:** `{n['dir']}`"]
        if n["comment"]:
            md.append(f"- **Developer comment:** {n['comment']}")
        if invoked_by.get(n["name"]):
            md.append("- **Invoked by:** " + ", ".join(sorted(invoked_by[n["name"]])))
        if referenced.get(n["name"]):
            md.append("- **Referenced by (trigger/REST/WSD/other):** " + ", ".join(sorted(referenced[n["name"]])))
        sig = n["ndf"].get("svc_sig") if isinstance(n["ndf"], dict) else None
        if isinstance(sig, dict):
            md += ["", "## Signature", sig_section("Inputs", sig.get("sig_in")), sig_section("Outputs", sig.get("sig_out"))]
        if "record" in n["node_type"].lower():
            md += ["", "## Fields", sig_section("Document fields", n["ndf"])]
        fl = n.get("flow")
        if fl:
            calls = sorted(set(fl["invokes"]))
            md += ["", "## Invokes", *(f"- `{c}`" + (f" — {classify_invoke(c)}" if classify_invoke(c) else "")
                                        + ("" if c in nodes or c.startswith("pub.") else " — **outside scanned packages**")
                                        for c in calls)]
            md += ["", "## Logic (pseudocode, generated from flow.xml)", "```text", *fl["lines"], "```"]
            if fl.get("mermaid"):
                md += ["", "## Flowchart", "```mermaid", fl["mermaid"], "```"]
            elif fl.get("truncated"):
                md += ["", "_Flow too large for one diagram — split by top-level SEQUENCE when writing the FSD._"]
        if n.get("java"):
            md += ["", "## Java body", f"Source: `{n.get('java_src')}`", "```java", n["java"][:6000], "```"]
        if not fl and not n.get("java") and "record" not in n["node_type"].lower():
            props = flatten(n["ndf"])
            sql = [v for _, v in props if SQL_RE.search(v)]
            if sql:
                md += ["", "## SQL / statements found", *(f"```sql\n{s}\n```" for s in sql[:20])]
            md += ["", "## Raw properties (secrets redacted)", "| Key | Value |", "|---|---|"]
            md += ["| `%s` | %s |" % (k, v.replace("|", "\\|").replace("\n", " ")) for k, v in props]
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", n["name"].replace(":", "__"))
        with open(os.path.join(a.out, "services", safe + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")

    # call graphs
    def mid(name):
        return "s_" + re.sub(r"[^A-Za-z0-9_]", "_", name)

    def cg(root, depth=0, seen=None, lines=None, max_depth=6):
        seen, lines = (seen or set()), (lines if lines is not None else [])
        if root in seen or depth > max_depth:
            return lines
        seen.add(root)
        for c in sorted(set((nodes.get(root, {}).get("flow") or {}).get("invokes", []))):
            if c.startswith("pub.") and not classify_invoke(c):
                continue  # skip utility built-ins (string, list, math...) to keep graphs readable
            lines.append(f'  {mid(root)}["{root}"] --> {mid(c)}["{c}"]')
            cg(c, depth + 1, seen, lines)
        return lines

    with open(os.path.join(a.out, "callgraphs.md"), "w", encoding="utf-8") as f:
        for e in sorted(set(entry) | set(triggered)):
            body = cg(e)
            if body:
                f.write(f"## {e}\n\n```mermaid\nflowchart LR\n" + "\n".join(body) + "\n```\n\n")

    # inventory
    counts = defaultdict(int)
    for n in nodes.values():
        counts[kind_of(n)] += 1
    inv = ["# webMethods inventory", ""]
    for p in pkgs:
        inv += [f"## Package {p['package']} {p.get('version', '')}",
                f"- Requires: {', '.join(p['requires']) or 'none'}",
                f"- Startup services: {', '.join(p['startup']) or 'none'}",
                f"- Shutdown services: {', '.join(p['shutdown']) or 'none'}", ""]
    inv += ["## Node counts", *(f"- {k}: {v}" for k, v in sorted(counts.items())), "",
            "## Candidate entry points (not invoked by any scanned flow)", *(f"- `{e}`" for e in entry), "",
            "## Services referenced by triggers / REST / WSD / other config nodes",
            *(f"- `{t}` ← {', '.join(sorted(referenced[t]))}" for t in triggered), "",
            "## Integrations detected", *(f"- **{k}**: {', '.join(sorted(v))}" for k, v in sorted(integrations.items())), "",
            "## Calls to services outside scanned packages", *(f"- `{k}` ← {', '.join(sorted(v))}" for k, v in sorted(external.items())), "",
            "## All nodes", "| Name | Kind | Comment |", "|---|---|---|",
            *(f"| `{n['name']}` | {kind_of(n)} | {n['comment'][:80].replace(chr(10), ' ')} |" for n in sorted(nodes.values(), key=lambda x: x["name"]))]
    with open(os.path.join(a.out, "inventory.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(inv) + "\n")
    slim = {"packages": [{k: v for k, v in p.items() if k != "nodes"} for p in pkgs],
            "nodes": {k: {"kind": kind_of(v), "invokes": sorted(set((v.get("flow") or {}).get("invokes", []))),
                          "invoked_by": sorted(invoked_by.get(k, []))} for k, v in nodes.items()},
            "entry_points": entry, "triggered": triggered,
            "integrations": {k: sorted(v) for k, v in integrations.items()},
            "external_calls": {k: sorted(v) for k, v in external.items()}}
    with open(os.path.join(a.out, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump(slim, f, indent=2)
    print(f"Scanned {len(pkgs)} package(s), {len(nodes)} nodes, {len(entry)} entry points -> {a.out}")


if __name__ == "__main__":
    sys.exit(main())
