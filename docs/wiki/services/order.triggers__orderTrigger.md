# order.triggers:orderTrigger

[← index](../index.md) · kind: **Trigger** · role: Trigger (subscription)

## Overview


- **Kind:** Trigger
- **Package:** OrderProcessing
- **Role:** Trigger (subscription)
- **Source dir:** `sample/OrderProcessing/ns/order/triggers/orderTrigger`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** Subscribes to new OrderDoc publications from the storefront and invokes order submission.

## Raw properties (secrets redacted)

| Key | Value |
|---|---|
| `node_type` | trigger |
| `node_comment` | Subscribes to new OrderDoc publications from the storefront and invokes order submission. |
| `service` | order.process:submitOrder |
| `documentType` | order.docs:OrderDoc |
| `filterCondition` | status == 'NEW' |
| `joinType` | NONE |
| `concurrency` | serial |
| `maxRetries` | 3 |
| `retryInterval` | 5 |

## Semantic flags (verify, then carry into the FSD)

- Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
