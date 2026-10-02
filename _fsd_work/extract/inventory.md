# webMethods inventory

## Package OrderProcessing 1.0
- Requires: WmPublic, CommonUtils
- Startup services: none
- Shutdown services: none

## Package CommonUtils 1.0
- Requires: WmPublic
- Startup services: none
- Shutdown services: none

## Node counts
- Document type: 2
- Flow service: 4
- Java service: 1
- Trigger: 2
- jdbc service: 3

## Candidate entry points (not invoked by any scanned flow)
- `order.api.orders:_get`
- `order.process:cancelOrder`
- `order.process:submitOrder`

## Services referenced by triggers / REST / WSD / other config nodes
- `order.process:cancelOrder` ← order.triggers:cancelTrigger
- `order.process:submitOrder` ← order.triggers:orderTrigger

## Integrations detected
- **Adapter service (jdbc)**: order.jdbc:insertOrder, order.jdbc:selectOrder, order.jdbc:updateOrderStatus
- **HTTP/REST call**: order.process:submitOrder

## Calls to services outside scanned packages

## Semantic flags (each must be addressed in the FSD)
- `order.process:submitOrder`: BRANCH on `amount`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- `order.process:submitOrder`: `lineAmounts` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- `order.process:submitOrder`: `lastError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- `order.process:submitOrder`: `pub.client:http` does not fail on HTTP 4xx/5xx responses, and the flow never checks `header/status`. Error responses count as success, and REPEAT/TRY never sees them
- `order.process:submitOrder`: `status` is passed to adapter `order.jdbc:insertOrder` and changed afterwards, but no later adapter call saves the new value. The stored value is whatever it was at `order.jdbc:insertOrder`
- `order.process:submitOrder`: Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- `order.process:submitOrder`: Invoked by trigger order.triggers:orderTrigger: Integration Server discards the outputs (confirmationNumber, orderId, status). Only side effects (DB writes, calls, publishes) are visible to anyone
- `order.process:validateOrder`: Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- `order.triggers:cancelTrigger`: Trigger retries only happen when `order.process:cancelOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
- `order.triggers:orderTrigger`: Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried

## Architecture observations (details in architecture.md)
- Table `ORDERS` is shared by 3 capabilities (`order.api.orders:_get` SELECT; `order.process:cancelOrder` UPDATE; `order.process:submitOrder` INSERT). Document its lifecycle across capabilities and check how they interact (ordering, status assumptions, concurrency)
- Logging is inconsistent: `order.api.orders:_get` logs, `order.process:cancelOrder` logs, `order.process:submitOrder` has no logging
- Error handling is inconsistent: `order.api.orders:_get` has no TRY/CATCH, `order.process:cancelOrder` has no TRY/CATCH, `order.process:submitOrder` uses TRY/CATCH
- Hard-coded URL `https://payments.internal/charge` in `order.process:submitOrder` instead of an endpoint alias or configuration value
- All 3 adapter services share connection `OrderDB_Conn`; its transaction type and pool size affect every capability that uses it

## All nodes
| Name | Kind | Comment |
|---|---|---|
| `common.util:logEvent` | Flow service | Writes one audit line to the server log for an order event. |
| `order.api.orders:_get` | Flow service | REST resource: returns the status of one order, identified by the orderId query  |
| `order.docs:CancelDoc` | Document type | Request to cancel an existing order, published by customer service. |
| `order.docs:OrderDoc` | Document type | Canonical order document published by the storefront and consumed by order submi |
| `order.jdbc:insertOrder` | jdbc service | JDBC adapter service that inserts a new order row into the ORDERS table. |
| `order.jdbc:selectOrder` | jdbc service | JDBC adapter service that reads one order by its identifier. |
| `order.jdbc:updateOrderStatus` | jdbc service | JDBC adapter service that changes the status of an order when it has the expecte |
| `order.process:cancelOrder` | Flow service | Cancels a PENDING order and writes an audit log entry. |
| `order.process:submitOrder` | Flow service | Validates, persists and confirms a customer order. Triggered by orderTrigger whe |
| `order.process:validateOrder` | Java service | Validates required order fields and that the amount is a positive number. |
| `order.triggers:cancelTrigger` | Trigger | Subscribes to CancelDoc publications and invokes order cancellation. |
| `order.triggers:orderTrigger` | Trigger | Subscribes to new OrderDoc publications from the storefront and invokes order su |
