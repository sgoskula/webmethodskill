---
name: webmethods-fsd
description: Reverse-engineer a webMethods Integration Server application (one or many IS packages with flow services, Java services, adapter services, document types, triggers, REST/SOAP descriptors) into one complete, overall Functional Specification Document (FSD) with the existing (as-is) architecture, business rules, every branch condition, data mappings, error handling, integrations, Mermaid diagrams, and re-implementation notes for migrating to another language such as Java. Use this whenever the user asks to document, reverse-engineer, analyse, explain, migrate, re-platform, describe the architecture of, or write an FSD/functional spec/technical spec/design doc for a webMethods, wM, Integration Server, IS package, flow service or Designer project, even if they don't say "FSD".
---

# webMethods → FSD

You produce **one overall FSD** for the whole application, however many flow services and
packages it has. A business analyst can sign it off, an architect can see how the pieces fit
together, and a developer could re-implement it in another language without opening Designer.
Accuracy beats prose: every rule must be traceable to a service, and every statement must
describe what the code **actually does at runtime**, not what it seems meant to do.

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
6. **One application, one FSD.** Many flow services or packages still produce a single overall
   `docs/FSD.md`, with one section per capability and a shared Existing Architecture section.
   Split into separate documents only if the user asks, and even then write an overall FSD that
   holds the architecture and links to the parts.
7. **Work from the extract, not raw XML.** Raw `flow.xml` is huge and burns context. Only open raw
   files for things the extract flags as unclear (adapter config, Java, odd node types).
8. **Persist progress to disk.** Context will run out on real packages. Keep `_fsd_work/plan.md`
   as a checklist and tick items as you go, so a new chat can resume with "continue the FSD".
9. **No secrets.** Never copy passwords, keys or tokens into any output, even if found.

## Phase 0 — Scope (ask once, then proceed)

Confirm: which package folder(s) are in scope (default: every package folder in the workspace
that belongs to the application), the FSD audience (business / technical / both), output path
(default `docs/FSD.md`), and **whether the FSD will drive a migration** (and to which
language/stack, default Java). Ask whether they also have these, which live outside packages and
change the spec: scheduler task export, global variables, JDBC/JMS connection settings
(especially transaction type), REST/SOAP endpoint aliases, trigger "on retry failure" settings,
Trading Networks processing rules, UM/Broker config, and any existing architecture diagrams.
Missing ones become Open Questions; don't block on them.

## Phase 1 — Extract (deterministic)

Run the extractor **once over all packages together**. Cross-package calls, shared utilities and
shared tables only resolve when everything is scanned in the same run:

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir> [<pkgDir>...]
```

It writes:
- `inventory.md` / `inventory.json`: packages, counts, entry points, integrations, semantic flags,
  architecture observations.
- `architecture.md`: the **existing architecture facts**: package dependency diagram, component
  roles, component diagram (folder level when there are too many components), capabilities and
  their components, shared components, external systems and channels, data access by
  capability, document type usage, and observations.
- `callgraphs.md`: call graph per entry point.
- `services/<name>.md`: signature, role, capabilities using it, pseudocode, flowchart, invokes /
  invoked-by, Java body, adapter SQL and properties, semantic flags.

If Python is unavailable, read `references/webmethods-artifacts.md` and build the same notes by
hand, one service at a time, including the semantic checks and architecture facts listed there.

**Semantic flags** are automatic findings per service (dead values, swallowed errors including a
`getLastError` result copied to a renamed variable, unchecked HTTP status, values changed after they
were saved, floating-point money, discarded trigger outputs, trigger retries that never happen,
`$default` meaning, `EXIT … FAILURE` inside a TRY that its own CATCH intercepts, unbounded
`REPEAT COUNT=-1`). **Architecture observations** are
automatic findings across services (shared tables, inconsistent logging or error handling,
hard-coded endpoints, undeclared package dependencies, shared connections, Trading Networks use). Both are leads, not
conclusions: confirm each one, then carry it into the FSD.

## Phase 2 — Plan

Read `_fsd_work/extract/inventory.md` and `architecture.md`. Group services into **business
capabilities**, each rooted at an entry point: trigger-subscribed services, REST resources / API
descriptors, web service descriptors, scheduler tasks, startup services, and remaining "not
invoked" services. Several entry points can form one capability if they serve one business
purpose; say so in the plan. Utility services (logging, formatting) are not capabilities;
document them once in "Common Services".

Write `_fsd_work/plan.md`:

```
# FSD plan
- [ ] CAP-01 Order submission — entry order.process:submitOrder (trigger orderTrigger)
- [ ] CAP-02 ...
- [ ] Existing architecture
- [ ] Cross-cutting: data dictionary, integrations, errors, config, NFRs
- [ ] Re-implementation notes (if migrating)
- [ ] Assembly + coverage check
```

Show the plan to the user and continue unless they change it. For large applications (more than
about 10 capabilities), do one capability per turn and report progress.

## Phase 3 — One capability at a time

For each capability, walk its call graph depth-first from `callgraphs.md`. For every service
in it, read `services/<name>.md`. Then write `_fsd_work/sections/3N-CAP-xx.md` (e.g.
`30-CAP-01.md`, `31-CAP-02.md`) using the capability section of `references/fsd-template.md`.
Translate technical steps into business language, but keep the exact values (status codes,
literals, field names, SQL table names).

How to turn extract content into FSD content:

| In the extract | In the FSD |
|---|---|
| `BRANCH on X` + `CASE` labels | Decision table: condition on X → outcome; add "Any other value" row = `$default` or "no action (falls through)" |
| `WHEN <expr>` (label expressions) | Decision table with the expression rewritten in plain words *and* the raw expression; the `$default` row is "any other value, including missing or non-numeric", never "≤ X" |
| `$null` case | Decision row "value missing"; note that an empty string is *not* `$null` |
| `MAP` copy / set / drop, `input:` / `output:` | Data-mapping table: target ← source, transformation, default/literal |
| `transformer X` | Mapping row naming the transformation |
| `LOOP over X → collect Y` | "For each item in X…" processing step; say where Y is used (or that it isn't) |
| `REPEAT on FAILURE: re-run up to N more time(s)` | Retry policy row: total attempts (N+1), interval, what counts as failure (an exception, not an error response) |
| `TRY` / `CATCH` / `EXIT … FAILURE` | Error-handling table: trigger, action, message, outcome; say whether the original error is logged or lost |
| `⟵ HTTP/REST`, JMS, SFTP, adapter SQL… | Integration catalog row + sequence diagram participant; only list method/headers/auth if mapped |
| Role `Entry: REST GET /rest/...` | Trigger section: HTTP method and path; outputs become the response body; `pub.flow:setResponseCode` sets the status |
| Java body | Read it; describe the algorithm in plain words; flag hard-coded values and numeric types |
| `DISABLED` steps | Mention in "Notes": present but not executed |
| `outside scanned packages` | Dependency row + Open Question if behaviour matters |
| `→ caught by the CATCH of TRY [x]` on an EXIT | Error-handling row: the exit never reaches the caller as written; document what the CATCH does instead (swallow, rethrow, own EXIT) and what the caller or trigger then sees |
| `REPEAT` flagged "no upper bound" | Retry policy row: unbounded; Open Question for the intended maximum or timeout; Behaviour decision when migrating |
| `Trading Networks calls` table, `Trading Networks (partner/document hub)` system | Integration catalog row per operation group (receive, route, deliver, partner profile, status, query, log) and a sequence diagram participant. State the literal document type, sender, receiver and status values mapped. Routing, partners and delivery come from TN processing rules, which are not in the packages: add `[TO CONFIRM: TN processing rule / partner profile for <doc type>]` |
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
`participant A as "Name"` aliases, and close every `alt`/`loop`/`opt`/`subgraph` with `end`.

Tick the item in `plan.md` when the section file is written.

## Phase 4a — Existing architecture (after all capabilities)

Write `_fsd_work/sections/10-architecture.md` using the "Existing Architecture" section of the
template. Start from `architecture.md`, but write it for an architect, not as a dump:

1. **Overview**: architectural style in plain words (e.g. "event-driven order intake plus a
   synchronous REST query"), the packages and what each is for, and the main design choices.
2. **Package and dependency view**: the package diagram plus a table of what each package holds.
   Call out undeclared or circular dependencies.
3. **Component view**: the component diagram (simplify or split it if it's over ~40 nodes), and a
   table of components by layer: entry/channel, orchestration, business logic, data access,
   shared utility, data contracts.
4. **Runtime and integration view**: inbound channels (subscriptions, REST, SOAP, schedules),
   outbound systems, and whether each is synchronous or asynchronous. One summary sequence
   diagram for the end-to-end business flow if the capabilities form a chain.
5. **Capability-to-component matrix**: which components each capability uses; shared ones.
6. **Data ownership and entity lifecycle**: for every table or document that more than one
   capability touches, who creates, reads, updates and deletes it, and a `stateDiagram-v2` of
   its status values with the capability that causes each transition. Then **check how the
   capabilities behave together**: ordering and race conditions (e.g. concurrent triggers),
   states one capability assumes but another never sets, and gaps (states nobody can leave).
   Combined-behaviour findings are often the most important ones in the FSD.
7. **Cross-cutting patterns**: one table comparing every capability on error handling, logging,
   retries, transactions, configuration and security. Inconsistencies are findings.
8. **Architecture observations and risks**: each confirmed observation from the extract plus your
   own, with evidence (service names), impact, and a related Open Question or decision.

## Phase 4 — Cross-cutting sections

Using all section files plus the extract, write `_fsd_work/sections/60-common.md` covering:
common services, data dictionary (from document types), integration catalog, error catalog,
configuration and environment dependencies, scheduling, and NFRs that the code reveals
(timeouts, retries, transactions, batch sizes, validation, idempotency).

## Phase 4b — Re-implementation notes (when migrating, or audience includes developers)

Write `_fsd_work/sections/70-reimplementation.md` using the "Re-implementation Notes" section of
the template, targeting the language from Phase 0 (default Java):

1. **Target structure**: packages and capabilities → modules/services in the target, and which
   shared components become libraries. Keep it a proposal; flag it as such.
2. **Construct mapping**: every webMethods element used (trigger, REST resource, flow service, Java
   service, adapter service, `pub.*` built-ins, REPEAT, TRY/CATCH, `%var%` substitution) → the
   behaviour that must be reproduced → a target equivalent (e.g. trigger → JMS/Kafka listener,
   REPEAT → Resilience4j/Spring Retry with N+1 attempts retrying only exceptions).
3. **Behaviour decisions**: one row per confirmed semantic flag, architecture observation or
   suspected defect: current behaviour, "reproduce exactly" vs "fix" options, and who decides.
   Never silently fix behaviour in the spec.
4. **Data types**: everything in the IS pipeline is a string; list each numeric/date field and the
   recommended target type, and call out floating-point money.
5. **Idempotency and transactions**: what happens on redelivery / partial failure / concurrent
   processing, and which transaction type it depends on.
6. **Acceptance test cases**: one row per decision-table row, validation and error row, plus
   boundary values, redelivery, and **cross-capability scenarios** from Phase 4a (e.g. cancel
   arriving before submit): input, expected observable outcome (DB rows, outbound calls and
   counts, service result or HTTP status), source rule.

## Phase 5 — Assemble and verify

Section files and their order (file-name prefixes decide the order):
`00-intro.md` (sections 1–2) · `10-architecture.md` (3) · `20-summary.md` (4 + the heading of 5) ·
`30-CAP-01.md`, `31-CAP-02.md`, … (5.x) · `60-common.md` (6–11) · `70-reimplementation.md` (12) ·
`90-closing.md` (13 + appendices).

1. Assemble: `python .github/skills/webmethods-fsd/scripts/assemble_fsd.py --out docs/FSD.md`.
2. **Coverage check**: for each node in `inventory.json`: is it referenced in the FSD body or
   listed in Appendix A? For each flow service, does every CASE, EXIT FAILURE and CATCH from its
   pseudocode appear somewhere? Is **every semantic flag and every architecture observation**
   addressed (where)? Write the results into Appendix B and fix what you can.
3. **Invention check**: re-read every integration, retry and output statement and make sure it is
   backed by the extract; anything that isn't becomes `[TO CONFIRM]`.
4. Lint Mermaid: `python .github/skills/webmethods-fsd/scripts/check_mermaid.py docs/FSD.md` and
   fix every error.
5. Report to the user: capabilities covered, architecture findings, number of open questions,
   behaviour decisions needed, any gaps.

If the user later asks for Word, export the Markdown (e.g. pandoc) and note that Mermaid needs
rendering to images first.
