# order.triggers:orderTrigger

- **Kind:** Trigger
- **Package:** OrderProcessing
- **Source dir:** `sample/OrderProcessing/ns/order/triggers/orderTrigger`
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
