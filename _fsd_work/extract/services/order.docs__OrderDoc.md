# order.docs:OrderDoc

- **Kind:** Document type
- **Package:** OrderProcessing
- **Source dir:** `sample/OrderProcessing/ns/order/docs/OrderDoc`
- **Developer comment:** Canonical order document published by the storefront and consumed by order submission.
- **Referenced by (trigger/REST/WSD/other):** order.process:validateOrder, order.triggers:orderTrigger

## Fields
**Document fields:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  | Unique order identifier generated upstream by the storefront. |
| `customerId` | string |  |  |
| `amount` | string |  | Order total in USD, represented as a decimal string. |
| `status` | string | optional |  |
| `lines[]` | record |  | Order line items. |
| `  sku` | string |  |  |
| `  qty` | string |  |  |
| `  price` | string |  |  |

