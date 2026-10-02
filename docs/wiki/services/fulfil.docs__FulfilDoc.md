# fulfil.docs:FulfilDoc

[← index](../index.md) · kind: **Document type** · role: Data contract (document type)

## Overview


- **Kind:** Document type
- **Package:** FulfillmentEngine
- **Role:** Data contract (document type)
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/docs/FulfilDoc`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Published when an order is ready to be fulfilled.
- **Referenced by (trigger/REST/WSD/other):** fulfil.triggers:fulfilTrigger

## Fields

**Document fields:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  |  |
| `priority` | string | optional |  |
| `region` | string | optional |  |
| `weightKg` | string |  |  |
| `items[]` | record |  |  |
| `  sku` | string |  |  |
| `  qty` | string |  |  |
| `  hazmat` | string | optional |  |
