#!/usr/bin/env python3
"""
wm_ask.py - Retrieve the wiki chunks that answer a question and print a grounded prompt for an LLM.

Retrieval is BM25 over chunks.jsonl (from wm_wiki.py) plus one hop along the call graph, so
"what happens when payment fails?" finds the flow, its callees and its findings. No network and no
pip packages. Paste the output into any LLM chat, or pipe it to a CLI that accepts a prompt.

  python wm_ask.py --wiki _wiki "What happens when a cancel arrives for a CONFIRMED order?"
  python wm_ask.py --wiki _wiki --top-k 12 --max-chars 20000 "Which tables does submitOrder write?"
  python wm_ask.py --wiki _wiki --sources "..."      # just list the best chunks, no prompt
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

RULES = """You answer questions about a webMethods Integration Server application using ONLY the context below.
Rules:
- If the context does not contain the answer, say "Not in the extracted facts" and name what is missing.
  Never guess or fill gaps from general webMethods knowledge.
- Describe what happens at runtime, step by step, including every branch, `$default` or missing default, TRY/CATCH and retry.
- Cite the source of each statement as [service or file#heading].
- Report relevant findings (semantic flags and architecture observations) even if the question did not ask.
- Keep exact values: status codes, literals, field and table names.
"""

STOP = set("the a an of to in on is are was were be by for and or what which how does do when it its with from that this "
           "there any as at if not into than then so can will happens happen".split())


def tokens(text):
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)  # camelCase -> words
    out = []
    for w in re.findall(r"[A-Za-z0-9$]+", text):
        w = w.lower()
        if w not in STOP and len(w) > 1:
            out.append(w)
            if w.endswith("s") and len(w) > 3:
                out.append(w[:-1])
    return out


class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tf = [Counter(tokens(c["title"] + " " + c["title"] + " " + c["text"])) for c in chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(self.len)) or 1
        df = Counter(w for t in self.tf for w in t)
        n = len(chunks)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def score(self, query, k1=1.4, b=0.75):
        q = tokens(query)
        res = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if f:
                    s += self.idf.get(w, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * self.len[i] / self.avg))
            if s:
                res.append((s, i))
        return sorted(res, reverse=True)


def neighbours(service, chunks):
    """Services directly invoked by `service`, taken from its Invokes section."""
    out = []
    for c in chunks:
        if c["service"] == service and c["title"].endswith("- Invokes"):
            out += re.findall(r"`([^`]+)`", c["text"])
    return out


def select(index, question, top_k, max_chars, forced=()):
    ranked = index.score(question)
    picked, seen = [], set()

    def take(i):
        if i not in seen and sum(len(index.chunks[j]["text"]) for j in picked) < max_chars:
            seen.add(i)
            picked.append(i)

    for i, c in enumerate(index.chunks):
        if c["service"] in forced:
            take(i)
    for _, i in ranked[:top_k]:
        take(i)
    # one hop: logic and findings of services called by the best-matching services
    hit_services = []
    for _, i in ranked[:top_k]:
        s = index.chunks[i]["service"]
        if s and s not in hit_services and ":" in s:
            hit_services.append(s)
    def body(c):  # chunks that say what a service actually does
        h = c["title"].split(" - ")[-1]
        return h.startswith(("Logic", "Semantic", "Java", "SQL"))

    for s in hit_services[:3]:  # the best matches' own logic first, then their callees'
        for i, c in enumerate(index.chunks):
            if c["service"] == s and body(c):
                take(i)
    for s in hit_services[:3]:  # triggers that invoke them: retry, concurrency and join settings change the answer
        for i, c in enumerate(index.chunks):
            if c["service"] != s and c["title"].endswith("Raw properties (secrets redacted)") \
                    and re.search(r"\| `service` \| " + re.escape(s) + r" \|", c["text"]):
                take(i)
                for j, d in enumerate(index.chunks):
                    if d["service"] == c["service"] and d["title"].split(" - ")[-1].startswith("Semantic"):
                        take(j)
    for s in hit_services[:3]:
        for callee in neighbours(s, index.chunks):
            for i, c in enumerate(index.chunks):
                if c["service"] == callee and body(c):
                    take(i)
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--wiki", default="_wiki")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--max-chars", type=int, default=24000, help="context size budget (~4 chars per token)")
    ap.add_argument("--service", action="append", default=[], help="always include this service (repeatable)")
    ap.add_argument("--sources", action="store_true", help="list matching chunks only, no prompt")
    a = ap.parse_args()
    path = os.path.join(a.wiki, "chunks.jsonl")
    if not os.path.isfile(path):
        sys.exit(f"{path} not found: run wm_wiki.py first")
    with open(path, encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    question = " ".join(a.question)
    idx = Index(chunks)
    picked = select(idx, question, a.top_k, a.max_chars, a.service)
    if a.sources:
        for i in picked:
            print(f"{chunks[i]['title']}   ({chunks[i]['source']})")
        return
    print(RULES)
    print("=== CONTEXT ===")
    for i in picked:
        c = chunks[i]
        print(f"\n--- source: {c['title']} ({c['source']}) ---\n{c['text']}")
    print("\n=== QUESTION ===\n" + question)


if __name__ == "__main__":
    main()
