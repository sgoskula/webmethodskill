## 4. Capability Summary
| ID | Capability | Entry point | Initiated by | Frequency / volume |
|---|---|---|---|---|
| CAP-01 | Order Submission | `order.process:submitOrder` | Trigger `order.triggers:orderTrigger` on `order.docs:OrderDoc` (filter `status == 'NEW'`) | `[TO CONFIRM]` |
| CAP-02 | Order Cancellation | `order.process:cancelOrder` | Trigger `order.triggers:cancelTrigger` on `order.docs:CancelDoc` | `[TO CONFIRM]` |
| CAP-03 | Order Status Lookup | `order.api.orders:_get` | REST client: `GET /rest/order/api/orders?orderId=` | `[TO CONFIRM]` |

## 5. Capabilities
