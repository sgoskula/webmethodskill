# Findings

[← index](index.md)

Automatic leads from the extractor: verify before relying on them.

## Per service

### [`fulfil.process:allocateStock`](services/fulfil.process__allocateStock.md)
- REPEAT with `COUNT=-1` on FAILURE has no upper bound: if the body keeps failing the flow never gives up and never reaches its error handling. A re-implementation needs an explicit maximum or timeout, so ask what it should be
- BRANCH on `httpStatus` has no `$default`: values matching no case skip the branch silently

### [`fulfil.process:orchestrateFulfillment`](services/fulfil.process__orchestrateFulfillment.md)
- BRANCH on `orderStatus` has no `$default`: values matching no case skip the branch silently
- `EXIT $flow FAILURE` ("Stock allocation failed") sits inside TRY [allocation], so it is caught by that TRY's CATCH and does not reach the caller as written. What the caller sees depends on what the CATCH does (swallow, rethrow, or its own EXIT)
- BRANCH on `lastAllocated` has no `$default`: values matching no case skip the branch silently
- BRANCH on `needsSpecialCarrier` has no `$default`: values matching no case skip the branch silently
- `allocations` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- `allocError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- Invoked by trigger fulfil.triggers:fulfilTrigger: Integration Server discards the outputs (fulfilStatus, trackingNumber). Only side effects (DB writes, calls, publishes) are visible to anyone

### [`fulfil.util:computeShipping`](services/fulfil.util__computeShipping.md)
- BRANCH on `priority` has no `$default`: values matching no case skip the branch silently
- BRANCH on `weightKg`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- `priority` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing

### [`order.process:submitOrder`](services/order.process__submitOrder.md)
- BRANCH on `amount`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- `lineAmounts` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- `lastError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- `pub.client:http` does not fail on HTTP 4xx/5xx responses, and the flow never checks `header/status`. Error responses count as success, and REPEAT/TRY never sees them
- `status` is passed to adapter `order.jdbc:insertOrder` and changed afterwards, but no later adapter call saves the new value. The stored value is whatever it was at `order.jdbc:insertOrder`
- Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- Invoked by trigger order.triggers:orderTrigger: Integration Server discards the outputs (confirmationNumber, orderId, status). Only side effects (DB writes, calls, publishes) are visible to anyone

### [`order.process:validateOrder`](services/order.process__validateOrder.md)
- Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type

### [`order.triggers:cancelTrigger`](services/order.triggers__cancelTrigger.md)
- Trigger retries only happen when `order.process:cancelOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried

### [`order.triggers:orderTrigger`](services/order.triggers__orderTrigger.md)
- Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried

## Across services

- Package `FulfillmentEngine` calls `OrderProcessing` (1 call(s)) but doesn't declare it in manifest.v3 `requires`, so load order isn't guaranteed
- Table `ORDERS` is shared by 4 capabilities (`fulfil.process:orchestrateFulfillment` SELECT; `order.api.orders:_get` SELECT; `order.process:cancelOrder` UPDATE; `order.process:submitOrder` INSERT). Document its lifecycle across capabilities and check how they interact (ordering, status assumptions, concurrency)
- Logging is inconsistent: `fulfil.process:orchestrateFulfillment` logs, `order.api.orders:_get` logs, `order.process:cancelOrder` logs, `order.process:submitOrder` has no logging
- Error handling is inconsistent: `fulfil.process:orchestrateFulfillment` uses TRY/CATCH, `order.api.orders:_get` has no TRY/CATCH, `order.process:cancelOrder` has no TRY/CATCH, `order.process:submitOrder` uses TRY/CATCH
- Hard-coded URL `http://wms.internal/stock/reserve` in `fulfil.process:allocateStock` instead of an endpoint alias or configuration value
- Hard-coded URL `https://carrier.example/api/book` in `fulfil.process:orchestrateFulfillment` instead of an endpoint alias or configuration value
- Hard-coded URL `https://payments.internal/charge` in `order.process:submitOrder` instead of an endpoint alias or configuration value
- All 3 adapter services share connection `OrderDB_Conn`; its transaction type and pool size affect every capability that uses it
