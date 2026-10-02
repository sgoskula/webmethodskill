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

## 3. Existing Architecture
Written after all capabilities, from `_fsd_work/extract/architecture.md`, for an architect.

**3.1 Overview** — architectural style in plain words, the packages and what each is for, main
design choices.

**3.2 Package and dependency view** — package dependency diagram (flowchart LR) and a table:
package, purpose, components, depends on. Call out undeclared or circular dependencies.

**3.3 Component view** — component diagram (flowchart with a subgraph per package/folder; folder
level or split when over ~40 nodes) and a table by layer:
| Layer | Components | Responsibility |
|---|---|---|
Layers: entry/channel, orchestration, business logic, data access, shared utility, data contracts.

**3.4 Runtime and integration view**
| Channel / system | Direction | Protocol | Sync/async | Components | Capabilities |
|---|---|---|---|---|---|
Plus an end-to-end sequence diagram if the capabilities form a business chain.

**3.5 Capability-to-component matrix**
| Component | CAP-01 | CAP-02 | … |
|---|---|---|---|

**3.6 Data ownership and entity lifecycle** — per shared table/document: create/read/update/delete
by capability, a `stateDiagram-v2` of its status values (each transition labelled with the
capability that causes it), and the **combined behaviour** findings: ordering and races,
assumed-but-never-set states, dead-end states.

**3.7 Cross-cutting patterns**
| Concern | CAP-01 | CAP-02 | … | Consistent? |
|---|---|---|---|---|
Concerns: error handling, logging/audit, retries, transactions, configuration, security.

**3.8 Architecture observations and risks**
| # | Observation | Evidence | Impact | Related question / decision |
|---|---|---|---|---|

## 4. Capability Summary
| ID | Capability | Entry point | Initiated by | Frequency / volume |
|---|---|---|---|---|

## 5. Capabilities (repeat 5.x per capability)

### 5.x <CAP-xx Name>

**5.x.1 Overview** — business purpose in 3–5 sentences, plus one sentence on what actually
results (rows stored, calls made), including surprising outcomes.

**5.x.2 Trigger** — what starts it (trigger + document type + filter, REST verb + path, SOAP
operation, schedule, manual). Include subscription filters verbatim, concurrency, and the
*effective* retry behaviour (trigger retries need an ISRuntimeException).

**5.x.3 Inputs / Outputs**
| Direction | Field | Type | Mandatory | Description / allowed values | Source |
|---|---|---|---|---|---|
State who receives the outputs. For trigger-invoked services: "discarded by Integration Server".

**5.x.4 Sequence diagram** (```mermaid sequenceDiagram```, with `alt` for branches, `loop` for
loops/retries, error path shown, real persisted values shown)

**5.x.5 Processing logic** — numbered steps in business language. Sub-number nested logic
(3.1, 3.2). Each step ends with its source service in backticks. Say where computed values go,
or that they are unused.

**5.x.6 Business rules & decision tables**
| Rule ID | Condition | Outcome | Source |
|---|---|---|---|
Include an explicit "Any other value" row on every decision, worded literally (it includes
missing, empty and non-numeric values), never as the numeric opposite of the other cases.

**5.x.7 Validations**
| Field | Check | On failure | Source |
|---|---|---|---|
Also list fields that are *not* validated but are used.

**5.x.8 Data mappings**
| Target | Source | Transformation / default | Source service |
|---|---|---|---|

**5.x.9 Integrations used**
| System | Protocol / adapter | Operation / SQL / endpoint | Direction | Sync/async | Source |
|---|---|---|---|---|---|
Only state method, headers, auth, timeout if the code sets them; otherwise `[TO CONFIRM]`.

**5.x.10 Error handling & retries**
| Scenario | Detection | Action | Retry policy | Message / code | Final outcome |
|---|---|---|---|---|---|
Retry policy = total attempts and interval, and what counts as a failure. Final outcome = the
state of every system touched (rows, charges, messages), including dependencies on transaction
type. Include "error response that is not detected" rows.

**5.x.11 Process flowchart** (```mermaid flowchart TD```, business-level)

**5.x.12 Notes** — disabled steps, hard-coded values, suspected defects, dead code, every
confirmed semantic flag.

## 6. Common Services
Shared utilities (logging, auditing, error framework) — purpose and who calls them.

## 7. Data Dictionary
One table per document type: field, type, cardinality, description. Mermaid `classDiagram` for
document relationships where helpful.

## 8. Integration Catalog
All external touchpoints across capabilities: system, protocol, connection alias / endpoint
alias (no credentials), operations, capabilities using it.

## 9. Error Catalog
Every error message / code the application can produce, where, and resulting behaviour.

## 10. Configuration & Environment Dependencies
Global variables, endpoint aliases, adapter connections (and transaction type), JMS/UM aliases,
scheduler tasks, package dependencies (Mermaid diagram), startup/shutdown services, file paths.

## 11. Non-Functional Characteristics Observed in Code
Timeouts, retries, transactions, batching, concurrency (trigger settings), idempotency /
duplicate handling, logging/audit, security (auth on endpoints, ACLs if visible).

## 12. Re-implementation Notes (target: <language/stack>)

**12.0 Target structure (proposal)** — packages/capabilities → target modules or services; shared
components → libraries.

**12.1 Construct mapping**
| webMethods element | Behaviour to reproduce | Target equivalent |
|---|---|---|

**12.2 Behaviour decisions (reproduce exactly or fix)**
| # | Current behaviour | Evidence | Options | Decision owner |
|---|---|---|---|---|

**12.3 Data types**
| Field | IS type | Meaning | Recommended target type | Note |
|---|---|---|---|---|

**12.4 Idempotency & transactions** — redelivery, partial failure, transaction boundaries.

**12.5 Acceptance test cases**
| ID | Input / precondition | Expected observable outcome | Covers |
|---|---|---|---|
One per decision row, validation, error row, retry path, boundary value, redelivery, and
cross-capability scenario from 3.6.

## 13. Open Questions
| # | Question | Context / service | Owner |
|---|---|---|---|

## Appendix A — Service Inventory
Every service: name, kind, capability, one-line purpose.

## Appendix B — Coverage Report
Services not referenced, branches not described, semantic flags and architecture observations
and where each is addressed,
items needing SME review.
