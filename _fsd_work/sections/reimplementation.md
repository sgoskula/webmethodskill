## 11. Re-implementation Notes (target: Java)

**11.1 Construct mapping**
| webMethods element | Behaviour to reproduce | Java equivalent |
|---|---|---|
| `order.triggers:orderTrigger` | Consume `OrderDoc` messages where `status == 'NEW'`, one at a time. Retry only errors classed as transient | JMS/Kafka listener with concurrency 1 and a selector/filter on `status`. Retry only exceptions marked as transient |
| `order.process:submitOrder` | Steps in 4.1.5. Result discarded | `OrderSubmissionService.submit(OrderDoc)` returning `void` (or a result object if decision D2 says so) |
| `order.process:validateOrder` | Three checks in 4.1.7, in order, first failure wins | `OrderValidator.validate(OrderDoc)` throwing `OrderValidationException` |
| BRANCH `%amount% > 1000` / `$default` | Runs before validation. Anything that isn't over 1000 continues | `if (isOver(amount, 1000)) { … return; }`, with the string comparison behaviour from open question 7 |
| LOOP + `pub.math:multiplyFloats` → `lineAmounts` | Per-line `qty × price` as `double`, unused | Drop it, or keep it as `double` math, per decision D5 |
| `order.jdbc:insertOrder` | One INSERT with status `PENDING` | `JdbcTemplate.update("INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS) VALUES (?, ?, ?, ?)", …)` |
| TRY / CATCH + `getLastError` + `EXIT FAILURE` | Validation or insert error → generic failure, original error dropped | `try { … } catch (Exception e) { throw new OrderProcessingException("Order could not be validated or persisted"); }`. Decision D6 covers whether to keep the cause |
| `pub.client:http` | Send `orderId`, `amount`, ignore the response status | `HttpClient` / `RestClient`. Don't fail on non-2xx unless decision D3 says so |
| REPEAT `COUNT=3 BACK-OFF=5 LOOP-ON=FAILURE` | Up to 4 attempts in total, 5 s apart, on transport exceptions only | Resilience4j `Retry` (`maxAttempts=4`, `waitDuration=5s`, `retryExceptions=IOException`) or Spring `@Retryable` |
| Implicit adapter transaction | Depends on the `OrderDB_Conn` transaction type | NO_TRANSACTION → auto-commit insert. LOCAL/XA → `@Transactional` around the whole `submit` |
| `%orderId%-CONF` | Text concatenation | `orderId + "-CONF"` |

**11.2 Behaviour decisions (reproduce exactly or fix)**
| # | Current behaviour | Evidence | Options | Decision owner |
|---|---|---|---|---|
| D1 | `ORDERS.STATUS` stays `PENDING` forever | No UPDATE after insert (4.1.12) | Reproduce, or add an UPDATE to `CONFIRMED` / `FAILED` | Business owner |
| D2 | Status and confirmation number go nowhere | Outputs discarded by trigger (4.1.3) | Reproduce, or publish a result event / store the confirmation number | Business owner |
| D3 | Declined or failed charges (HTTP 4xx/5xx) count as success | `header/status` never read (4.1.10) | Reproduce, or treat non-2xx as failure (and decide whether to retry) | Business + payments |
| D4 | Orders over 1000 are dropped, not queued for approval | R1 ends with nothing stored (4.1.6) | Reproduce, or store/publish them for approval | Business owner |
| D5 | Line totals calculated and ignored | `lineAmounts` unused (4.1.5) | Drop it, or add a check that lines add up to `amount` | Business analyst |
| D6 | Validation and database error details are lost | `lastError` unused (4.1.10) | Reproduce the generic message, or log and keep the cause | Tech lead |
| D7 | Money handled as floating point | `multiplyFloats`, `Double.parseDouble` | Use `double` to match exactly, or switch to `BigDecimal` | Tech lead + finance |
| D8 | Duplicate delivery may insert and charge twice | No idempotency (10) | Reproduce, or de-duplicate on `orderId` | Tech lead |

**11.3 Data types**
| Field | IS type | Meaning | Recommended Java type | Note |
|---|---|---|---|---|
| `orderId` | String | Identifier | `String` | Must be non-blank |
| `customerId` | String | Identifier | `String` | Not validated today |
| `amount` | String | USD total | `BigDecimal` (or `double` to match, D7) | Parsed with `Double.parseDouble` today, so "1e3" and "NaN" parse |
| `lines/qty` | String | Quantity | `int` / `BigDecimal` | Multiplied as float today |
| `lines/price` | String | Unit price | `BigDecimal` | Multiplied as float today |
| `status` | String | Order state | `enum OrderStatus { PENDING, PENDING_APPROVAL, FAILED, CONFIRMED }` | Only `PENDING` is ever stored |

**11.4 Idempotency & transactions** — The flow inserts first and charges second, with no
de-duplication. On redelivery of the same `OrderDoc` (e.g. after a crash), the order is inserted
again (or fails if `ORDER_ID` is unique) and may be charged again. If all payment attempts fail
to connect, the outcome depends on the `OrderDB_Conn` transaction type: with NO_TRANSACTION a
`PENDING` row remains with no charge, with LOCAL/XA the insert is rolled back. Confirm both
before choosing transaction boundaries in Java.

**11.5 Acceptance test cases** (describe current behaviour; update them if a decision in 11.2 changes it)
| ID | Input / precondition | Expected observable outcome | Covers |
|---|---|---|---|
| T01 | `amount = "1500"`, valid order | No INSERT, no HTTP call, service succeeds | R1 |
| T02 | `amount = "1000"`, valid order, gateway returns 200 | 1 INSERT with STATUS `PENDING`, 1 HTTP call, success | R2 boundary |
| T03 | `amount = "250"`, 2 lines, gateway returns 200 | 1 INSERT `PENDING`, 1 HTTP call with `orderId` and `amount = "250"`, success, no UPDATE | R2, 4.1.5 |
| T04 | `orderId = ""` | No INSERT, no HTTP call, failure "Order could not be validated or persisted" | Validation 1 |
| T05 | `amount = "abc"` | Branch result `[TO CONFIRM]`, then validation failure as T04, no INSERT | R2, validation 2 |
| T06 | `amount = "0"` and `amount = "-5"` | Validation failure as T04 | Validation 3 |
| T07 | INSERT throws an SQL error | No HTTP call, failure as T04 | Insert-fails row |
| T08 | Gateway refuses connections every time | 4 HTTP attempts about 5 s apart, then the service fails. Row present or absent per transaction type | Retry, gateway-unreachable row |
| T09 | Gateway refuses twice, then returns 200 | 3 HTTP attempts, success, 1 row `PENDING` | Retry |
| T10 | Gateway returns 402 or 500 | 1 HTTP attempt, success, row `PENDING` | HTTP-error row, D3 |
| T11 | Same `OrderDoc` delivered twice | 2 INSERT attempts and up to 2 charges `[TO CONFIRM: unique key]` | D8 |
| T12 | Document with `status = "PAID"` | Trigger filter skips it, no service run | 4.1.2 |
| T13 | Valid order with empty `lines` | Saved and charged as normal | Missing validation |
