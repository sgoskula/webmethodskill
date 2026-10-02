# order.docs:CancelDoc

[← index](../index.md) · kind: **Document type** · role: Data contract (document type)

## Overview


- **Kind:** Document type
- **Package:** OrderProcessing
- **Role:** Data contract (document type)
- **Source dir:** `sample/OrderProcessing/ns/order/docs/CancelDoc`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** Request to cancel an existing order, published by customer service.
- **Referenced by (trigger/REST/WSD/other):** order.triggers:cancelTrigger

## Fields

**Document fields:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  |  |
| `reason` | string | optional |  |
| `requestedBy` | string |  | User or system that asked for the cancellation. |
