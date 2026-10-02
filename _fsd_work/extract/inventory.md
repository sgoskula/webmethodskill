# webMethods inventory

## Package OrderProcessing 1.0
- Requires: WmPublic
- Startup services: none
- Shutdown services: none

## Node counts
- Document type: 1
- Flow service: 1
- Java service: 1
- Trigger: 1
- jdbc service: 1

## Candidate entry points (not invoked by any scanned flow)
- `order.process:submitOrder`

## Services referenced by triggers / REST / WSD / other config nodes
- `order.process:submitOrder` ← order.triggers:orderTrigger

## Integrations detected
- **Adapter service (jdbc)**: order.jdbc:insertOrder
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
- `order.triggers:orderTrigger`: Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried

## All nodes
| Name | Kind | Comment |
|---|---|---|
| `order.docs:OrderDoc` | Document type | Canonical order document published by the storefront and consumed by order submi |
| `order.jdbc:insertOrder` | jdbc service | JDBC adapter service that inserts a new order row into the ORDERS table. |
| `order.process:submitOrder` | Flow service | Validates, persists and confirms a customer order. Triggered by orderTrigger whe |
| `order.process:validateOrder` | Java service | Validates required order fields and that the amount is a positive number. |
| `order.triggers:orderTrigger` | Trigger | Subscribes to new OrderDoc publications from the storefront and invokes order su |
