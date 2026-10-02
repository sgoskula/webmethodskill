## 13. Open Questions
| # | Question | Context / service | Owner |
|---|---|---|---|
| Q1 | What HTTP method, headers, auth and timeout should the payment call use? None are set in the flow | `order.process:submitOrder` | Integration team |
| Q2 | What are the transaction type and pool size of `OrderDB_Conn`? They decide rollback behaviour for all three capabilities | `order.jdbc:*` | DBA / IS admin |
| Q3 | Should `ORDERS.STATUS` be updated to `CONFIRMED` / `FAILED`? (D1) | `order.process:submitOrder` | Business owner |
| Q4 | Where are orders over 1000 approved? They are neither stored nor published (D4) | `order.process:submitOrder` | Business owner |
| Q5 | Should the CAP-01 status or confirmation number reach anyone? (D2) | `order.process:submitOrder` | Business owner |
| Q6 | Is treating HTTP 4xx/5xx (e.g. declined payment) as success intended? (D3) | `order.process:submitOrder` | Payments |
| Q7 | How does IS evaluate `%amount% > 1000` for strings such as "1000.50", "1,200" or "abc"? | `order.process:submitOrder` | IS developer |
| Q8 | What are the real trigger settings (concurrency, retries, "on retry failure")? Does the JDBC adapter report transient errors as retryable? | `order.triggers:*` | IS admin |
| Q9 | Is `ORDERS.ORDER_ID` unique? (D8, D13) | `ORDERS` | DBA |
| Q10 | Should the gateway URL become an endpoint alias? | `order.process:submitOrder` | Integration team |
| Q11 | Are there scheduler tasks, global variables or UM/Broker settings outside the packages? | Application-wide | IS admin |
| Q12 | What ACL / authentication protects `/rest/order/api/orders`? (D11) | `order.api.orders:_get` | Security |
| Q13 | What does the REST resource return on a database error (status, body, exception text)? Which content types are supported? | `order.api.orders:_get` | IS developer |
| Q14 | Should cancelling a charged order trigger a refund, or be blocked? (D9) | `order.process:cancelOrder` | Business + payments |
| Q15 | Can a `CancelDoc` arrive before its `OrderDoc` is processed? How should early cancels be handled? (D10) | Both triggers | Business + integration |
| Q16 | Which row does CAP-03 return when several match? (D13) | `order.api.orders:_get` | IS developer |
| Q17 | When `reason` is missing, does `%message%` become empty or stay literal in the audit line? | `common.util:logEvent` | IS developer |
| Q18 | Is the server log configured so that `ORDER_AUDIT` Info lines are kept? | `common.util:logEvent` | IS admin |
| Q19 | Should `requestedBy` be recorded for cancellations? (A8) | `order.process:cancelOrder` | Business owner |
| Q20 | Which systems actually publish `OrderDoc` and `CancelDoc`? | Triggers | Integration team |

## Appendix A — Service Inventory
| Name | Package | Kind | Capability | Purpose |
|---|---|---|---|---|
| `order.process:submitOrder` | OrderProcessing | Flow service | CAP-01 | Validates, saves and charges an order |
| `order.process:validateOrder` | OrderProcessing | Java service | CAP-01 | Checks `orderId` is present and `amount` is a positive number |
| `order.jdbc:insertOrder` | OrderProcessing | JDBC adapter service | CAP-01 | Inserts the order into `ORDERS` |
| `order.triggers:orderTrigger` | OrderProcessing | Trigger | CAP-01 | Subscribes to `OrderDoc` (`status == 'NEW'`), invokes `submitOrder` |
| `order.process:cancelOrder` | OrderProcessing | Flow service | CAP-02 | Cancels a `PENDING` order and logs the outcome |
| `order.jdbc:updateOrderStatus` | OrderProcessing | JDBC adapter service | CAP-02 | Conditional status UPDATE on `ORDERS` |
| `order.triggers:cancelTrigger` | OrderProcessing | Trigger | CAP-02 | Subscribes to `CancelDoc`, invokes `cancelOrder` |
| `order.api.orders:_get` | OrderProcessing | Flow service (REST resource) | CAP-03 | `GET /rest/order/api/orders` status lookup |
| `order.jdbc:selectOrder` | OrderProcessing | JDBC adapter service | CAP-03 | Reads one order by id |
| `common.util:logEvent` | CommonUtils | Flow service | CAP-02, CAP-03 | Audit line to the server log |
| `order.docs:OrderDoc` | OrderProcessing | Document type | CAP-01 | New order contract |
| `order.docs:CancelDoc` | OrderProcessing | Document type | CAP-02 | Cancellation request contract |

## Appendix B — Coverage Report

**Services** — all 12 nodes in `inventory.json` appear in Sections 3 and 5 and in Appendix A. No gaps.

**Branches, exits, catches and retries**
| Service | Construct | Addressed in |
|---|---|---|
| `submitOrder` | BRANCH `%amount% > 1000` / `$default` | CAP-01-R1 / R2 (5.1.6) |
| `submitOrder` | `EXIT $flow SUCCESS` after approval | 5.1.5 step 2 |
| `submitOrder` | TRY + CATCH + `EXIT $flow FAILURE` | 5.1.10 rows 1–2 |
| `submitOrder` | LOOP `order/lines` → `lineAmounts` | 5.1.5 step 3.2 |
| `submitOrder` | REPEAT (COUNT 3, back-off 5 s) | 5.1.10 rows 3–4, 12.1 |
| `submitOrder` | Final `EXIT $flow SUCCESS` | 5.1.5 step 5 |
| `cancelOrder` | BRANCH on `rowsUpdated`: CASE `0` / `$default` | CAP-02-R1 / R2 (5.2.6) |
| `cancelOrder` | `EXIT $flow FAILURE` "Order not found or not cancellable" | 5.2.10 row 1 |
| `_get` | BRANCH on `orderId`: `$null` / `$default` | CAP-03-R1 / R2 (5.3.6) |
| `_get` | BRANCH on `resultCount`: CASE `0` / `$default` | CAP-03-R3 / R4 (5.3.6) |
| `_get` | `EXIT $flow SUCCESS` after 400 and after 404 | 5.3.5 steps 1 and 4 |
| `logEvent` | MAP + `pub.flow:debugLog` | Section 6 |

**Semantic flags from the extract**
| Flag | Addressed in |
|---|---|
| `submitOrder`: `$default` also catches missing / non-numeric values | CAP-01-R2, Q7, T05 |
| `submitOrder`: `lineAmounts` never used | 5.1.5, 5.1.12, D5 |
| `submitOrder`: `lastError` never logged or rethrown | 5.1.10, 5.1.12, D6 |
| `submitOrder`: `pub.client:http` status never checked | 5.1.10, D3, T10 |
| `submitOrder`: `status` changed after insert, never re-saved | 5.1.12, 3.6, D1 |
| `submitOrder`: floating-point money | 5.1.12, 12.3, D7 |
| `submitOrder`: outputs discarded (trigger-invoked) | 5.1.3, D2 |
| `validateOrder`: floating-point money | 5.1.7, 12.3, D7 |
| `orderTrigger`: trigger retries never happen | 5.1.2, Q8 |
| `cancelTrigger`: trigger retries never happen | 5.2.2, Q8 |

**Architecture observations from the extract**
| Observation | Addressed in |
|---|---|
| `ORDERS` shared by 3 capabilities | 3.6 (lifecycle + 7 combined findings), A1, D1, D9, D10, D13 |
| Logging inconsistent | 3.7, A3, D12 |
| Error handling inconsistent | 3.7, A4, D12 |
| Hard-coded payment URL | A5, Q10 |
| All adapters share `OrderDB_Conn` | A6, Q2 |

**Needs SME review** — the 20 open questions in Section 13 and the 13 decisions in 12.2.
