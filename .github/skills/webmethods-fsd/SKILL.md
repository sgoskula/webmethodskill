---
name: webmethods-fsd
description: Reverse-engineer a webMethods Integration Server application (IS packages with flow services, Java services, adapter services, document types, triggers, REST/SOAP descriptors) into a complete, detailed Functional Specification Document (FSD) with business rules, every branch condition, data mappings, error handling, integrations and Mermaid diagrams. Use this whenever the user asks to document, reverse-engineer, analyse, explain or write an FSD/functional spec/technical spec/design doc for a webMethods, wM, Integration Server, IS package, flow service or Designer project, even if they don't say "FSD".
---

# webMethods → FSD

You produce an FSD that a business analyst can sign off and a developer could re-implement from,
without opening Designer. Accuracy beats prose: every rule must be traceable to a service.

## Golden rules

1. **Never invent behaviour.** If something isn't in the code or config you read, write
   `[TO CONFIRM: <question>]`. Collect these in the "Open Questions" section.
2. **Traceability.** Every business rule, decision row and mapping cites its source service in
   backticks, e.g. ``(`order.process:submitOrder`)``.
3. **Every condition is captured.** Every BRANCH case (including `$default` and the *absence* of a
   default), every EXIT with FAILURE, every TRY/CATCH, every REPEAT/retry, every LOOP must
   appear in the FSD as a decision table row, error-handling row or processing step.
4. **Work from the extract, not raw XML.** Raw `flow.xml` is huge and burns context. Only open raw
   files for things the extract flags as unclear (adapter config, Java, odd node types).
5. **Persist progress to disk.** Context will run out on real packages. Keep `_fsd_work/plan.md`
   as a checklist and tick items as you go, so a new chat can resume with "continue the FSD".
6. **No secrets.** Never copy passwords, keys or tokens into any output, even if found.

## Phase 0 — Scope (ask once, then proceed)

Confirm: which package folder(s) are in scope, the FSD audience (business / technical / both),
and output path (default `docs/FSD.md`). Ask whether they also have these, which live outside
packages and change the spec: scheduler task export, global variables, JDBC/JMS connection
settings, REST/SOAP endpoint aliases, Trading Networks processing rules, UM/Broker config.
Missing ones become Open Questions; don't block on them.

## Phase 1 — Extract (deterministic)

Run in the terminal:

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir> [<pkgDir>...]
```

It writes `inventory.md`, `inventory.json`, `callgraphs.md` and `services/<name>.md`
(signature tables, generated pseudocode, Mermaid flowchart, invokes / invoked-by, Java bodies,
adapter SQL and properties). If Python is unavailable, read
`references/webmethods-artifacts.md` and build the same notes by hand, one service at a time.

## Phase 2 — Plan

Read `_fsd_work/extract/inventory.md`. Group services into **business capabilities**, each rooted
at an entry point: trigger-subscribed services, REST resources / API descriptors, web service
descriptors, scheduler tasks, startup services, and remaining "not invoked" services.
Utility services (logging, formatting) are not capabilities; document them once in the
"Common Services" section.

Write `_fsd_work/plan.md`:

```
# FSD plan
- [ ] CAP-01 Order submission — entry order.process:submitOrder (trigger orderTrigger)
- [ ] CAP-02 ...
- [ ] Cross-cutting: data dictionary, integrations, errors, config, NFRs
- [ ] Assembly + coverage check
```

Show the plan to the user and continue unless they change it.

## Phase 3 — One capability at a time

For each capability, walk its call graph depth-first from `callgraphs.md`. For every service
in it, read `services/<name>.md`. Then write `_fsd_work/sections/CAP-xx.md` using the
capability section of `references/fsd-template.md`. Translate technical steps into business
language, but keep the exact values (status codes, literals, field names, SQL table names).

How to turn extract content into FSD content:

| In the extract | In the FSD |
|---|---|
| `BRANCH on X` + `CASE` labels | Decision table: condition on X → outcome; add "Any other value" row = `$default` or "no action (falls through)" |
| `WHEN <expr>` (label expressions) | Decision table with the expression rewritten in plain words *and* the raw expression |
| `MAP` copy / set / drop, `input:` / `output:` | Data-mapping table: target ← source, transformation, default/literal |
| `transformer X` | Mapping row naming the transformation |
| `LOOP over X` | "For each item in X…" processing step; note if results are collected |
| `REPEAT … on FAILURE` | Retry policy row: attempts, backoff, what is retried |
| `TRY` / `CATCH` / `EXIT … FAILURE` | Error-handling table: trigger, action, message, outcome |
| `⟵ HTTP/REST`, JMS, SFTP, adapter SQL… | Integration catalog row + sequence diagram participant |
| Java body | Read it; describe the algorithm in plain words; flag hard-coded values |
| `DISABLED` steps | Mention in "Notes": present but not executed |
| `outside scanned packages` | Dependency row + Open Question if behaviour matters |

Diagrams per capability (Mermaid, fenced as ```mermaid):
- **Sequence diagram**: source system → IS services → databases / APIs / queues → responses,
  including error and retry paths as `alt` / `loop` blocks.
- **Process flowchart**: business-level decision flow. Start from the generated flowchart, merge
  technical-only nodes (MAPs, logging), and rename nodes to business words.
- If the generated flowchart was truncated, draw one per top-level SEQUENCE.

Mermaid hygiene: put every label in double quotes, avoid `()[]{}` inside unquoted text, keep a
diagram under ~40 nodes (split larger ones), use `participant A as "Name"` aliases.

Tick the item in `plan.md` when the section file is written.

## Phase 4 — Cross-cutting sections

Using all section files plus the extract, write `_fsd_work/sections/common.md` covering: context
diagram (all external systems), integration catalog, data dictionary (from document types),
error catalog, configuration and environment dependencies, scheduling, NFRs that the code
reveals (timeouts, retries, transactions, batch sizes, validation), package dependencies
diagram, and common services.

## Phase 5 — Assemble and verify

1. Build `docs/FSD.md` from `references/fsd-template.md`, pasting section files in order.
2. **Coverage check** — for each service in `inventory.json`: is it referenced in the FSD body or
   listed in Appendix A? For each flow service, does every CASE, EXIT FAILURE and CATCH from its
   pseudocode appear somewhere? Write gaps into Appendix B ("Coverage report") and fix what you can.
3. Re-check every Mermaid block for syntax (balanced quotes, no stray brackets).
4. Report to the user: capabilities covered, number of open questions, any gaps.

If the user later asks for Word, export the Markdown (e.g. pandoc) and note that Mermaid needs
rendering to images first.
