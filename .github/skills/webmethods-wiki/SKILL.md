---
name: webmethods-wiki
description: Build a browsable wiki (like a "deep wiki") of a webMethods Integration Server application from its packages, and answer questions about its functionality, flows, branches, error handling, data and integrations, grounded in the code. Use this whenever the user wants to explore, understand, query, ask questions about, or "chat with" a webMethods / IS package, flow service or Designer project, or wants a wiki, knowledge base or LLM-ready context of it, even if they don't say "wiki".
---

# webMethods → wiki + Q&A

Two jobs: **build** a wiki from the packages once, then **answer questions** from it. Answers must be
grounded in extracted facts, not in general webMethods knowledge or guesses.

## Build

1. Extract all packages in one run (reuse `_fsd_work/extract` if it exists and the packages haven't changed):
   ```
   python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir> [<pkgDir>...]
   ```
2. Build the wiki:
   ```
   python .github/skills/webmethods-wiki/scripts/wm_wiki.py --extract _fsd_work/extract --out _wiki
   ```
   It writes `_wiki/index.md` (start page), `capabilities/`, `services/` (cross-linked, with flowcharts),
   `tables/` (who reads and writes each table), `findings.md`, `architecture.md`, `chunks.jsonl` (search
   index) and `llm_context.md` (the whole application as one file, without diagrams).
3. Tell the user where the wiki is, and the `llm_context.md` token estimate that the script prints.

## Answer a question

Open only `_wiki` text files and `wm_ask.py` output. Never open images, jars or other binaries, and never attach or search the package folders (see rule 10 in `webmethods-fsd/SKILL.md`).

Never answer from memory. Retrieve first:

```
python .github/skills/webmethods-wiki/scripts/wm_ask.py --wiki _wiki "<the user's question>"
```

It prints a grounded prompt: rules, the best-matching wiki chunks (ranked, plus the best matches' own
logic and their callees' logic), and the question. Read that context, then answer:

- Lead with a short plain-English answer (2–4 sentences, no identifiers or webMethods jargon), then the technical detail.
- Use only the retrieved text. If it lacks the answer, say "Not in the extracted facts" and say what is
  missing; offer to widen the search (`--top-k 20`, `--service <name>`) or to open the raw file.
- Trace the full path: every branch, `$default` or missing default, TRY/CATCH, retry and exit. Walk calls
  to callees by re-running `wm_ask.py --service <callee>`, or by opening `_wiki/services/<name>.md`.
- Describe runtime behaviour. Check `findings.md` entries for the services involved, and mention the
  relevant ones (discarded trigger outputs, `$default` meaning, unchecked HTTP status, EXIT caught by a
  TRY, unbounded REPEAT, dead values), because they change the answer.
- Cite sources as `service#heading` or file path. Keep exact status codes, literals, field and table names.
- Never reveal secrets; the extract already redacts them.
- Cross-capability questions ("what if cancel arrives before submit?"): read `tables/<TABLE>.md` and each
  capability's page, then reason about ordering from what each one reads, writes and assumes.

## Using another LLM

- Small application (the printed `llm_context.md` token count fits the model): give the user
  `_wiki/llm_context.md` to attach, plus `RULES` from `wm_ask.py` as the instruction.
- Larger application: use `wm_ask.py` per question and paste its output.

## Limits to state when relevant

The wiki reflects only the scanned packages. For Trading Networks it has the calls (`trading-networks.md`: operation, literal document type, sender, receiver, status) but not the partner profiles, document types or processing rules, which live in TN. Scheduler tasks, JDBC connection settings, endpoint aliases,
global variables and Trading Networks rules live outside packages: say so instead of guessing.
