# order.triggers:cancelTrigger

- **Kind:** Trigger
- **Package:** OrderProcessing
- **Role:** Trigger (subscription)
- **Source dir:** `sample/OrderProcessing/ns/order/triggers/cancelTrigger`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** Subscribes to CancelDoc publications and invokes order cancellation.

## Raw properties (secrets redacted)
| Key | Value |
|---|---|
| `node_type` | trigger |
| `node_comment` | Subscribes to CancelDoc publications and invokes order cancellation. |
| `service` | order.process:cancelOrder |
| `documentType` | order.docs:CancelDoc |
| `joinType` | NONE |
| `concurrency` | concurrent |
| `maxThreads` | 4 |
| `maxRetries` | 0 |
| `retryInterval` | 0 |

## Semantic flags (verify, then carry into the FSD)
- Trigger retries only happen when `order.process:cancelOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
