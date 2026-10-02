# Functional Specification — <Application name>

| Item | Value |
|---|---|
| Source packages | <list + versions from manifest.v3> |
| Generated from | Code as of <date / commit> |
| Status | Draft — reverse-engineered, pending SME review |

## 1. Introduction
1.1 Purpose · 1.2 Scope (in/out) · 1.3 Glossary (business terms, acronyms, wM terms used)

## 2. System Context
- Short narrative of what the application does for the business.
- **Context diagram** (flowchart LR): this application in the middle, every source/target
  system around it, edges labelled with protocol and message (e.g. "JMS: OrderCreated").

## 3. Capability Summary
| ID | Capability | Entry point | Initiated by | Frequency / volume |
|---|---|---|---|---|

## 4. Capabilities (repeat 4.x per capability)

### 4.x <CAP-xx Name>

**4.x.1 Overview** — business purpose in 3–5 sentences, plus one sentence on what actually
results (rows stored, calls made), including surprising outcomes.

**4.x.2 Trigger** — what starts it (trigger + document type + filter, REST verb + path, SOAP
operation, schedule, manual). Include subscription filters verbatim, concurrency, and the
*effective* retry behaviour (trigger retries need an ISRuntimeException).

**4.x.3 Inputs / Outputs**
| Direction | Field | Type | Mandatory | Description / allowed values | Source |
|---|---|---|---|---|---|
State who receives the outputs. For trigger-invoked services: "discarded by Integration Server".

**4.x.4 Sequence diagram** (```mermaid sequenceDiagram```, with `alt` for branches, `loop` for
loops/retries, error path shown, real persisted values shown)

**4.x.5 Processing logic** — numbered steps in business language. Sub-number nested logic
(3.1, 3.2). Each step ends with its source service in backticks. Say where computed values go,
or that they are unused.

**4.x.6 Business rules & decision tables**
| Rule ID | Condition | Outcome | Source |
|---|---|---|---|
Include an explicit "Any other value" row on every decision, worded literally (it includes
missing, empty and non-numeric values), never as the numeric opposite of the other cases.

**4.x.7 Validations**
| Field | Check | On failure | Source |
|---|---|---|---|
Also list fields that are *not* validated but are used.

**4.x.8 Data mappings**
| Target | Source | Transformation / default | Source service |
|---|---|---|---|

**4.x.9 Integrations used**
| System | Protocol / adapter | Operation / SQL / endpoint | Direction | Sync/async | Source |
|---|---|---|---|---|---|
Only state method, headers, auth, timeout if the code sets them; otherwise `[TO CONFIRM]`.

**4.x.10 Error handling & retries**
| Scenario | Detection | Action | Retry policy | Message / code | Final outcome |
|---|---|---|---|---|---|
Retry policy = total attempts and interval, and what counts as a failure. Final outcome = the
state of every system touched (rows, charges, messages), including dependencies on transaction
type. Include "error response that is not detected" rows.

**4.x.11 Process flowchart** (```mermaid flowchart TD```, business-level)

**4.x.12 Notes** — disabled steps, hard-coded values, suspected defects, dead code, every
confirmed semantic flag.

## 5. Common Services
Shared utilities (logging, auditing, error framework) — purpose and who calls them.

## 6. Data Dictionary
One table per document type: field, type, cardinality, description. Mermaid `classDiagram` for
document relationships where helpful.

## 7. Integration Catalog
All external touchpoints across capabilities: system, protocol, connection alias / endpoint
alias (no credentials), operations, capabilities using it.

## 8. Error Catalog
Every error message / code the application can produce, where, and resulting behaviour.

## 9. Configuration & Environment Dependencies
Global variables, endpoint aliases, adapter connections (and transaction type), JMS/UM aliases,
scheduler tasks, package dependencies (Mermaid diagram), startup/shutdown services, file paths.

## 10. Non-Functional Characteristics Observed in Code
Timeouts, retries, transactions, batching, concurrency (trigger settings), idempotency /
duplicate handling, logging/audit, security (auth on endpoints, ACLs if visible).

## 11. Re-implementation Notes (target: <language/stack>)

**11.1 Construct mapping**
| webMethods element | Behaviour to reproduce | Target equivalent |
|---|---|---|

**11.2 Behaviour decisions (reproduce exactly or fix)**
| # | Current behaviour | Evidence | Options | Decision owner |
|---|---|---|---|---|

**11.3 Data types**
| Field | IS type | Meaning | Recommended target type | Note |
|---|---|---|---|---|

**11.4 Idempotency & transactions** — redelivery, partial failure, transaction boundaries.

**11.5 Acceptance test cases**
| ID | Input / precondition | Expected observable outcome | Covers |
|---|---|---|---|
One per decision row, validation, error row, retry path, boundary value and redelivery.

## 12. Open Questions
| # | Question | Context / service | Owner |
|---|---|---|---|

## Appendix A — Service Inventory
Every service: name, kind, capability, one-line purpose.

## Appendix B — Coverage Report
Services not referenced, branches not described, semantic flags and where each is addressed,
items needing SME review.
