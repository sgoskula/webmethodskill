## 12. Re-implementation Notes (target: Java)

**12.0 Target structure (proposal)** — All three capabilities share one table and one status
lifecycle, so a single service that owns `ORDERS` is the simplest faithful port. Splitting it
would turn today's shared-table coupling into distributed coordination.

| Today (webMethods) | Proposed Java module / class | Notes |
|---|---|---|
| Package `OrderProcessing` | Spring Boot service `order-service` | Owns `ORDERS` |
| CAP-01 `orderTrigger` + `submitOrder` + `validateOrder` | `OrderIntakeListener` → `OrderSubmissionService`, `OrderValidator` | Messaging adapter + service |
| CAP-02 `cancelTrigger` + `cancelOrder` | `OrderCancellationListener` → `OrderCancellationService` | Messaging adapter + service |
| CAP-03 `order.api.orders:_get` | `OrderQueryController` (`GET /rest/order/api/orders`) | Keep the path so callers don't change |
| `order.jdbc:*` adapters | `OrderRepository` (JdbcTemplate) | One class for the three statements |
| Package `CommonUtils` / `common.util:logEvent` | `AuditLogger` in a small shared library (or a class in the service) | SLF4J logger `ORDER_AUDIT` |
| `order.docs:*` | `OrderDoc`, `OrderLine`, `CancelDoc` records + JSON/message mapping | Data contracts |

**12.1 Construct mapping**
| webMethods element | Behaviour to reproduce | Java equivalent |
|---|---|---|
| `orderTrigger` (serial, filter `status == 'NEW'`) | One document at a time, only `NEW`. Ordinary failures not retried | JMS/Kafka listener, concurrency 1, selector/filter on `status`. Retry only exceptions marked as transient |
| `cancelTrigger` (concurrent, 4) | Up to 4 in parallel, no retries | Listener with concurrency 4, no retry |
| REST resource `_get` | `GET /rest/order/api/orders?orderId=`, outputs as body | `@GetMapping("/rest/order/api/orders")` with `@RequestParam(required = false) String orderId` |
| `pub.flow:setResponseCode` | 400 / 404 with `{ "error": … }`, otherwise 200 with `{ "order": … }` | `ResponseEntity.status(…).body(…)` |
| `submitOrder` | Steps in 5.1.5. Result discarded | `OrderSubmissionService.submit(OrderDoc)` returning `void` (or a result per D2) |
| `cancelOrder` | Steps in 5.2.5 | `OrderCancellationService.cancel(CancelDoc)` |
| `validateOrder` | Three checks in 5.1.7, first failure wins | `OrderValidator.validate(OrderDoc)` throwing `OrderValidationException` |
| BRANCH `%amount% > 1000` / `$default` | Runs before validation. Anything not over 1000 continues | `if (isOver(amount, 1000)) { … return; }`, string comparison per Q7 |
| BRANCH `$null` (CAP-03) | Only a *missing* parameter → 400. Empty → continue | `if (orderId == null)` (not `isBlank`) to match today |
| BRANCH on row count `"0"` | Zero vs any other count | `if (count == 0)` |
| LOOP + `pub.math:multiplyFloats` | Per-line `qty × price` as `double`, unused | Drop it, or keep it, per D5 |
| `pub.list:sizeOfList` | Row count | `results.size()` |
| `order.jdbc:insertOrder` / `updateOrderStatus` / `selectOrder` | SQL in 5.1.9 / 5.2.9 / 5.3.9 | `OrderRepository.insert / updateStatus(id, expected, new) → int / findById → List` |
| TRY/CATCH + `getLastError` + `EXIT FAILURE` (CAP-01) | Validation or insert error → generic failure, cause dropped | `catch (Exception e) { throw new OrderProcessingException("Order could not be validated or persisted"); }`. D6 covers keeping the cause |
| `EXIT FAILURE` (CAP-02) | Fail with "Order not found or not cancellable" | `throw new OrderNotCancellableException(…)`, not retried |
| `pub.client:http` + REPEAT `COUNT=3` | Up to 4 attempts, 5 s apart, transport exceptions only. Ignore HTTP status | `RestClient` + Resilience4j `Retry` (`maxAttempts=4`, `waitDuration=5s`, `retryExceptions=IOException`). Don't fail on non-2xx unless D3 says so |
| `common.util:logEvent` / `pub.flow:debugLog` | `"<eventType> order=<id> <message>"` at Info | `auditLog.info("{} order={} {}", eventType, orderId, message)` |
| Implicit adapter transaction | Depends on `OrderDB_Conn` | NO_TRANSACTION → auto-commit. LOCAL/XA → `@Transactional` per service method |
| `%orderId%-CONF` | Text concatenation | `orderId + "-CONF"` |

**12.2 Behaviour decisions (reproduce exactly or fix)**
| # | Current behaviour | Evidence | Options | Decision owner |
|---|---|---|---|---|
| D1 | `ORDERS.STATUS` stays `PENDING` after CAP-01, whatever the payment result | 5.1.12, 3.6 | Reproduce, or UPDATE to `CONFIRMED` / `FAILED` | Business owner |
| D2 | CAP-01 status and confirmation number go nowhere | 5.1.3 | Reproduce, or publish a result event / store the confirmation number | Business owner |
| D3 | Declined or failed charges (HTTP 4xx/5xx) count as success | 5.1.10 | Reproduce, or treat non-2xx as failure | Business + payments |
| D4 | Orders over 1000 are dropped, not queued for approval | 5.1.6 | Reproduce, or store/publish them for approval | Business owner |
| D5 | Line totals calculated and ignored | 5.1.5 | Drop it, or check that the lines add up to `amount` | Business analyst |
| D6 | CAP-01 error details are lost | 5.1.10 | Reproduce the generic message, or log and keep the cause | Tech lead |
| D7 | Money handled as floating point | `multiplyFloats`, `Double.parseDouble` | `double` to match, or `BigDecimal` | Tech lead + finance |
| D8 | Duplicate `OrderDoc` delivery may insert and charge twice | 11 | Reproduce, or de-duplicate on `orderId` | Tech lead |
| D9 | Charged orders can be cancelled with no refund | 3.6, finding 1 | Reproduce, block cancel after charge, or trigger a refund | Business + payments |
| D10 | A cancel processed before its order exists is lost. A cancel during payment still charges | 3.6, findings 4–5 | Reproduce, park and retry early cancels, or lock/check status before charging | Tech lead + business |
| D11 | REST lookup has no visible security | 3.8, A7 | Reproduce (if secured outside the package), or add authentication | Security |
| D12 | Logging and error handling differ per capability | 3.7 | Reproduce per capability, or apply one audit/error policy | Tech lead |
| D13 | Multiple rows for one `ORDER_ID` give an unclear lookup result | 3.6, finding 6 | Reproduce (first row?), or enforce a unique key | DBA + tech lead |

**12.3 Data types**
| Field | IS type | Meaning | Recommended Java type | Note |
|---|---|---|---|---|
| `orderId` | String | Identifier | `String` | Non-blank in CAP-01. Unchecked in CAP-02/03 |
| `customerId` | String | Identifier | `String` | Not validated |
| `amount` / `AMOUNT` | String | USD total | `BigDecimal` (or `double` to match, D7) | `Double.parseDouble` accepts "1e3" and "NaN" today |
| `lines/qty`, `lines/price` | String | Quantity, unit price | `int`/`BigDecimal`, `BigDecimal` | Multiplied as float today |
| `status` / `STATUS` | String | Order state | `enum OrderStatus { PENDING, PENDING_APPROVAL, FAILED, CONFIRMED, CANCELLED }` | Only `PENDING` and `CANCELLED` are ever stored |
| `updateCount`, `resultCount` | String | Row counts | `int` | Compared with the string `"0"` today |
| `reason`, `requestedBy` | String | Free text, actor | `String` | `requestedBy` unused today |

**12.4 Idempotency, transactions and concurrency** — CAP-01 inserts first and charges second,
with no de-duplication: redelivery can insert twice and charge twice (D8). If every payment
attempt fails to connect, whether the `PENDING` row survives depends on the `OrderDB_Conn`
transaction type. CAP-02's conditional UPDATE is safe to repeat, but a repeat counts as a failure.
The two listeners must keep today's independence (or fix it on purpose, D10): CAP-02 at
concurrency 4 can overtake CAP-01. CAP-03 is read-only.

**12.5 Acceptance test cases** (describe current behaviour; update them if a decision in 12.2 changes it)
| ID | Input / precondition | Expected observable outcome | Covers |
|---|---|---|---|
| T01 | `OrderDoc` `amount = "1500"`, valid | No INSERT, no HTTP call, service succeeds | CAP-01-R1 |
| T02 | `amount = "1000"`, gateway 200 | 1 INSERT `PENDING`, 1 HTTP call, success | CAP-01-R2 boundary |
| T03 | `amount = "250"`, 2 lines, gateway 200 | 1 INSERT `PENDING`, 1 HTTP call with `orderId` and `amount = "250"`, no UPDATE | CAP-01 5.1.5 |
| T04 | `orderId = ""` | No INSERT, no HTTP, failure "Order could not be validated or persisted" | CAP-01 validation |
| T05 | `amount = "abc"` | Branch result `[TO CONFIRM]`, then validation failure as T04 | CAP-01-R2, validation |
| T06 | `amount = "0"` and `"-5"` | Validation failure as T04 | CAP-01 validation |
| T07 | INSERT throws | No HTTP, failure as T04 | CAP-01 errors |
| T08 | Gateway refuses connections every time | 4 attempts about 5 s apart, service fails. Row per transaction type | CAP-01 retry |
| T09 | Gateway refuses twice, then 200 | 3 attempts, success, row `PENDING` | CAP-01 retry |
| T10 | Gateway returns 402 or 500 | 1 attempt, success, row `PENDING` | CAP-01, D3 |
| T11 | Same `OrderDoc` delivered twice | 2 INSERT attempts, up to 2 charges `[TO CONFIRM: unique key]` | D8 |
| T12 | `OrderDoc` with `status = "PAID"` | Trigger skips it | CAP-01 trigger |
| T13 | Valid order with empty `lines` | Saved and charged as normal | CAP-01 validation gap |
| T14 | `CancelDoc` for a `PENDING` order | Row → `CANCELLED`, log `ORDER_CANCELLED order=<id> <reason>`, success | CAP-02-R2 |
| T15 | `CancelDoc` for an unknown id | No change, log `CANCEL_REJECTED`, failure "Order not found or not cancellable", not retried | CAP-02-R1 |
| T16 | `CancelDoc` for an already `CANCELLED` order | As T15 | CAP-02-R1 |
| T17 | `CancelDoc` without `orderId` | As T15 `[TO CONFIRM: adapter null handling]` | CAP-02 validation |
| T18 | Database error on the cancel UPDATE | Failure, nothing logged, not retried | CAP-02 errors |
| T19 | Submit (T03) completes, then `CancelDoc` | Row `CANCELLED`, customer stays charged, no gateway call | D9, cross-capability |
| T20 | `CancelDoc` processed before the matching `OrderDoc` | Cancel fails (T15), then order inserted `PENDING` and charged | D10, cross-capability |
| T21 | `CancelDoc` processed between CAP-01's INSERT and charge | Row `CANCELLED`, charge still sent | D10, cross-capability |
| T22 | `GET /rest/order/api/orders` (no parameter) | 400, `{error: "orderId is required"}`, no DB read, no log | CAP-03-R1 |
| T23 | `GET …?orderId=` (empty) | 404, `{error: "Order not found"}`, no log | CAP-03-R2, R3 |
| T24 | `GET …?orderId=<unknown>` | 404, no log | CAP-03-R3 |
| T25 | `GET …?orderId=<existing>` | 200, `{order: {orderId, status, amount}}`, log `ORDER_QUERY order=<id>` | CAP-03-R4 |
| T26 | `GET` for an order submitted and paid (T03) | 200 with `status = "PENDING"` | D1, cross-capability |
| T27 | `GET` for an order over 1000 (T01) | 404 | D4, cross-capability |
| T28 | Database down on `GET` | Error response, HTTP 500 assumed `[TO CONFIRM]`, no log | CAP-03 errors |
