## 12. Open Questions
| # | Question | Context / service | Owner |
|---|---|---|---|
| 1 | What HTTP method, headers, auth and timeout should the payment call use? None are set in the flow | `order.process:submitOrder` | Integration team |
| 2 | What is the transaction type of `OrderDB_Conn`? It decides whether the insert is rolled back when payment can't be reached | `order.jdbc:insertOrder` | DBA / IS admin |
| 3 | Should `ORDERS.STATUS` be updated to `CONFIRMED` / `FAILED`? It stays `PENDING` today (D1) | `order.process:submitOrder` | Business owner |
| 4 | Where are orders over 1000 approved? They are neither stored nor published (D4) | `order.process:submitOrder` | Business owner |
| 5 | Should the status or confirmation number reach the storefront or customer? Outputs are discarded (D2) | `order.process:submitOrder` | Business owner |
| 6 | Is treating HTTP 4xx/5xx (e.g. declined payment) as success intended? (D3) | `order.process:submitOrder` | Payments |
| 7 | How does IS evaluate `%amount% > 1000` for strings such as "1000.50", "1,200" or "abc"? | `order.process:submitOrder` | IS developer |
| 8 | What is the trigger's "on retry failure" setting, and does the JDBC adapter report transient errors as retryable? | `order.triggers:orderTrigger` | IS admin |
| 9 | Is `ORDERS.ORDER_ID` unique? Is duplicate delivery possible? (D8) | `order.jdbc:insertOrder` | DBA |
| 10 | Should the gateway URL become an endpoint alias? | `order.process:submitOrder` | Integration team |
| 11 | Are there scheduler tasks, global variables or UM/Broker settings outside the package that affect this flow? | Package-wide | IS admin |

## Appendix A — Service Inventory
| Name | Kind | Capability | Purpose |
|---|---|---|---|
| `order.process:submitOrder` | Flow service | CAP-01 | Validates, saves and charges an order |
| `order.process:validateOrder` | Java service | CAP-01 | Checks `orderId` is present and `amount` is a positive number |
| `order.jdbc:insertOrder` | JDBC adapter service | CAP-01 | Inserts the order into `ORDERS` |
| `order.triggers:orderTrigger` | Trigger | CAP-01 | Subscribes to `OrderDoc` (`status == 'NEW'`) and invokes `submitOrder` |
| `order.docs:OrderDoc` | Document type | Data dictionary | Canonical order document |

## Appendix B — Coverage Report

**Services** — all 5 nodes in `inventory.json` appear in Section 4 and Appendix A. No gaps.

**Branches, exits, catches and retries in `order.process:submitOrder`**
| Construct | Addressed in |
|---|---|
| BRANCH case `%amount% > 1000` | R1 (4.1.6), 4.1.5 step 2 |
| BRANCH `$default` | R2 (4.1.6) |
| `EXIT $flow SUCCESS` after approval | 4.1.5 step 2, flowchart node E |
| TRY around validate + LOOP + insert | 4.1.10 rows 1–2 |
| CATCH + `EXIT $flow FAILURE` | 4.1.10 rows 1–2, flowchart node H |
| LOOP over `order/lines` → `lineAmounts` | 4.1.5 step 3.2, 4.1.8 |
| REPEAT (COUNT 3, back-off 5 s) around `pub.client:http` | 4.1.10 rows 3–4, 11.1, T08–T10 |
| Final `EXIT $flow SUCCESS` | 4.1.5 step 5, flowchart node M |

**Semantic flags from the extract**
| Flag | Addressed in |
|---|---|
| `submitOrder`: `$default` also catches missing / non-numeric values | R2, open question 7, T05 |
| `submitOrder`: `lineAmounts` never used | 4.1.5 step 3.2, 4.1.12, D5 |
| `submitOrder`: `lastError` never logged or rethrown | 4.1.10, 4.1.12, D6 |
| `submitOrder`: `pub.client:http` status never checked | 4.1.10 row 4, 4.1.12, D3, T10 |
| `submitOrder`: `status` changed after insert, never re-saved | 4.1.5 step 5, 4.1.12, D1 |
| `submitOrder`: floating-point money | 4.1.12, 11.3, D7 |
| `submitOrder`: outputs discarded (trigger-invoked) | 4.1.3, 4.1.12, D2 |
| `validateOrder`: floating-point money | 4.1.7, 11.3, D7 |
| `orderTrigger`: trigger retries never happen | 4.1.2, Section 8, open question 8 |

**Needs SME review** — the 11 open questions in Section 12 and the 8 decisions in 11.2.
