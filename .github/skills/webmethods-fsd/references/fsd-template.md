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

**4.x.1 Overview** — business purpose in 3–5 sentences.

**4.x.2 Trigger** — what starts it (trigger + document type + filter, REST verb + path, SOAP
operation, schedule, manual). Include subscription filters verbatim.

**4.x.3 Inputs / Outputs**
| Direction | Field | Type | Mandatory | Description / allowed values | Source |
|---|---|---|---|---|---|

**4.x.4 Sequence diagram** (```mermaid sequenceDiagram```, with `alt` for branches, `loop` for
loops/retries, error path shown)

**4.x.5 Processing logic** — numbered steps in business language. Sub-number nested logic
(3.1, 3.2). Each step ends with its source service in backticks.

**4.x.6 Business rules & decision tables**
| Rule ID | Condition | Outcome | Source |
|---|---|---|---|
Include an explicit row for "any other value" on every decision.

**4.x.7 Validations**
| Field | Check | On failure | Source |
|---|---|---|---|

**4.x.8 Data mappings**
| Target | Source | Transformation / default | Source service |
|---|---|---|---|

**4.x.9 Integrations used**
| System | Protocol / adapter | Operation / SQL / endpoint | Direction | Sync/async | Source |
|---|---|---|---|---|---|

**4.x.10 Error handling & retries**
| Scenario | Detection | Action | Retry policy | Message / code | Final outcome |
|---|---|---|---|---|---|

**4.x.11 Process flowchart** (```mermaid flowchart TD```, business-level)

**4.x.12 Notes** — disabled steps, hard-coded values, suspected defects, dead code.

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
Global variables, endpoint aliases, adapter connections, JMS/UM aliases, scheduler tasks,
package dependencies (Mermaid diagram), startup/shutdown services, file paths.

## 10. Non-Functional Characteristics Observed in Code
Timeouts, retries, transactions, batching, concurrency (trigger settings), logging/audit,
security (auth on endpoints, ACLs if visible).

## 11. Open Questions
| # | Question | Context / service | Owner |
|---|---|---|---|

## Appendix A — Service Inventory
Every service: name, kind, capability, one-line purpose.

## Appendix B — Coverage Report
Services not referenced, branches not described, items needing SME review.
