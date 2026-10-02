---
name: webmethods-fsd
description: Reverse-engineer a webMethods Integration Server application (IS packages with flow services, Java services, adapter services, document types, triggers, REST/SOAP descriptors) into a complete, detailed Functional Specification Document (FSD) with business rules, every branch condition, data mappings, error handling, integrations, Mermaid diagrams, and re-implementation notes for migrating to another language such as Java. Use this whenever the user asks to document, reverse-engineer, analyse, explain, migrate, re-platform or write an FSD/functional spec/technical spec/design doc for a webMethods, wM, Integration Server, IS package, flow service or Designer project, even if they don't say "FSD".
---

# webMethods → FSD

You produce an FSD that a business analyst can sign off and a developer could re-implement from
in another language, without opening Designer. Accuracy beats prose: every rule must be traceable
to a service, and every statement must describe what the code **actually does at runtime**, not
what it seems meant to do.

## Golden rules

1. **Never invent behaviour.** If something isn't in the code or config you read, write
   `[TO CONFIRM: <question>]`. Collect these in the "Open Questions" section. This includes
   details that "obviously" exist, such as an HTTP method that the flow never sets.
2. **Traceability.** Every business rule, decision row and mapping cites its source service in
   backticks, e.g. ``(`order.process:submitOrder`)``.
3. **Every condition is captured.** Every BRANCH case (including `$default` and the *absence* of a
   default), every EXIT with FAILURE, every TRY/CATCH, every REPEAT/retry, every LOOP must
   appear in the FSD as a decision table row, error-handling row or processing step.
4. **Runtime semantics over intent.** Describe what Integration Server does, using
   `references/webmethods-artifacts.md` → "Runtime semantics". Typical traps: trigger-invoked
   services' outputs are discarded, `pub.client:http` doesn't fail on 4xx/5xx, REPEAT `COUNT` is
   *re*-tries, `$default` catches null/non-numeric values, and trigger retries need an
   ISRuntimeException. Never write "retries on failure" or "returns X" without checking.
5. **Follow every value to where it ends up.** For each output, persisted column and outbound
   payload, state the value that actually arrives there. Values that are computed but never used,
   or changed after they were saved, are findings and must be stated.
6. **Work from the extract, not raw XML.** Raw `flow.xml` is huge and burns context. Only open raw
   files for things the extract flags as unclear (adapter config, Java, odd node types).
7. **Persist progress to disk.** Context will run out on real packages. Keep `_fsd_work/plan.md`
   as a checklist and tick items as you go, so a new chat can resume with "continue the FSD".
8. **No secrets.** Never copy passwords, keys or tokens into any output, even if found.

## Phase 0 — Scope (ask once, then proceed)

Confirm: which package folder(s) are in scope, the FSD audience (business / technical / both),
output path (default `docs/FSD.md`), and **whether the FSD will drive a migration** (and to which
language/stack, default Java). Ask whether they also have these, which live outside packages and
change the spec: scheduler task export, global variables, JDBC/JMS connection settings
(especially transaction type), REST/SOAP endpoint aliases, trigger "on retry failure" settings,
Trading Networks processing rules, UM/Broker config. Missing ones become Open Questions; don't
block on them.

## Phase 1 — Extract (deterministic)

Run in the terminal:

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir> [<pkgDir>...]
```

It writes `inventory.md`, `inventory.json`, `callgraphs.md` and `services/<name>.md`
(signature tables, generated pseudocode, Mermaid flowchart, invokes / invoked-by, Java bodies,
adapter SQL and properties, and **semantic flags**). If Python is unavailable, read
`references/webmethods-artifacts.md` and build the same notes by hand, one service at a time,
including the semantic checks listed there.

**Semantic flags** (in `inventory.md` and each service file) are automatic findings: dead values,
swallowed errors, unchecked HTTP status, values changed after they were saved, floating-point money,
discarded trigger outputs, trigger retries that never happen, `$default` meaning. They are leads,
not conclusions: confirm each one against the pseudocode, then carry it into the FSD.

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
- [ ] Re-implementation notes (if migrating)
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
| `WHEN <expr>` (label expressions) | Decision table with the expression rewritten in plain words *and* the raw expression; the `$default` row is "any other value, including missing or non-numeric", never "≤ X" |
| `MAP` copy / set / drop, `input:` / `output:` | Data-mapping table: target ← source, transformation, default/literal |
| `transformer X` | Mapping row naming the transformation |
| `LOOP over X → collect Y` | "For each item in X…" processing step; say where Y is used (or that it isn't) |
| `REPEAT on FAILURE: re-run up to N more time(s)` | Retry policy row: total attempts (N+1), interval, what counts as failure (an exception, not an error response) |
| `TRY` / `CATCH` / `EXIT … FAILURE` | Error-handling table: trigger, action, message, outcome; say whether the original error is logged or lost |
| `⟵ HTTP/REST`, JMS, SFTP, adapter SQL… | Integration catalog row + sequence diagram participant; only list method/headers/auth if mapped |
| Java body | Read it; describe the algorithm in plain words; flag hard-coded values and numeric types |
| `DISABLED` steps | Mention in "Notes": present but not executed |
| `outside scanned packages` | Dependency row + Open Question if behaviour matters |
| Semantic flag | Fold the confirmed behaviour into the relevant table/step, and add a Notes bullet; if it looks like a defect, add an Open Question asking whether it is intended |
| Service referenced by a trigger | Outputs table marks outputs "discarded"; Trigger section states the real retry behaviour |

Diagrams per capability (Mermaid, fenced as ```mermaid):
- **Sequence diagram**: source system → IS services → databases / APIs / queues → responses,
  including error and retry paths as `alt` / `loop` blocks. Show what is really persisted
  and returned.
- **Process flowchart**: business-level decision flow. Start from the generated flowchart, merge
  technical-only nodes (MAPs, logging), and rename nodes to business words.
- If the generated flowchart was truncated, draw one per top-level SEQUENCE.

Mermaid hygiene: put every label in double quotes, avoid `()[]{}` inside unquoted text, never use
`;` or `#` in sequence-diagram text, keep a diagram under ~40 nodes (split larger ones), use
`participant A as "Name"` aliases, and close every `alt`/`loop`/`opt` with `end`.

Tick the item in `plan.md` when the section file is written.

## Phase 4 — Cross-cutting sections

Using all section files plus the extract, write `_fsd_work/sections/common.md` covering: context
diagram (all external systems), integration catalog, data dictionary (from document types),
error catalog, configuration and environment dependencies, scheduling, NFRs that the code
reveals (timeouts, retries, transactions, batch sizes, validation, idempotency), package
dependencies diagram, and common services.

## Phase 4b — Re-implementation notes (when migrating, or audience includes developers)

Write `_fsd_work/sections/reimplementation.md` using the "Re-implementation Notes" section of the
template, targeting the language from Phase 0 (default Java):

1. **Construct mapping** — every webMethods element used (trigger, flow service, Java service,
   adapter service, `pub.*` built-ins, REPEAT, TRY/CATCH, `%var%` substitution) → the behaviour that
   must be reproduced → a target equivalent (e.g. trigger → JMS/Kafka listener with concurrency 1,
   REPEAT → Resilience4j/Spring Retry with N+1 attempts retrying only exceptions).
2. **Behaviour decisions** — one row per confirmed semantic flag or suspected defect: current
   behaviour, "reproduce exactly" vs "fix" options, and who decides. Never silently fix behaviour
   in the spec.
3. **Data types** — everything in the IS pipeline is a string; list each numeric/date field and the
   recommended target type, and call out floating-point money.
4. **Idempotency and transactions** — what happens on redelivery / partial failure, and which
   transaction type it depends on.
5. **Acceptance test cases** — one row per decision-table row, validation and error row, plus
   boundary values (e.g. exactly the threshold) and redelivery: input, expected observable outcome
   (DB rows, outbound calls and counts, service result), source rule.

## Phase 5 — Assemble and verify

1. Build `docs/FSD.md` from `references/fsd-template.md`, pasting section files in order.
2. **Coverage check** — for each service in `inventory.json`: is it referenced in the FSD body or
   listed in Appendix A? For each flow service, does every CASE, EXIT FAILURE and CATCH from its
   pseudocode appear somewhere? Is **every semantic flag** in `inventory.json` addressed (where)?
   Write gaps into Appendix B ("Coverage report") and fix what you can.
3. **Invention check** — re-read every integration, retry and output statement and make sure it is
   backed by the extract; anything that isn't becomes `[TO CONFIRM]`.
4. Lint Mermaid: `python .github/skills/webmethods-fsd/scripts/check_mermaid.py docs/FSD.md` and
   fix every error.
5. Report to the user: capabilities covered, number of open questions, behaviour decisions
   needed, any gaps.

If the user later asks for Word, export the Markdown (e.g. pandoc) and note that Mermaid needs
rendering to images first.
