# Application wiki

Generated from the webMethods packages. Every page is derived from the code; nothing is guessed. Ask questions with `wm_ask.py` or paste `llm_context.md` into an LLM.

## Packages

- `OrderProcessing` 1.0 (requires: WmPublic, CommonUtils)
- `CommonUtils` 1.0 (requires: WmPublic)
- `FulfillmentEngine` 2.1 (requires: WmPublic, CommonUtils)

## Capabilities (entry points)

- [`fulfil.process:notifyPartner`](capabilities/fulfil.process__notifyPartner.md) - Entry: not invoked by any scanned service (scheduler, manual or external caller?) (1 components)
- [`fulfil.process:orchestrateFulfillment`](capabilities/fulfil.process__orchestrateFulfillment.md) - Entry: trigger fulfil.triggers:fulfilTrigger (6 components)
- [`order.api.orders:_get`](capabilities/order.api.orders___get.md) - Entry: REST GET /rest/order/api/orders (3 components)
- [`order.process:cancelOrder`](capabilities/order.process__cancelOrder.md) - Entry: trigger order.triggers:cancelTrigger (4 components)
- [`order.process:submitOrder`](capabilities/order.process__submitOrder.md) - Entry: trigger order.triggers:orderTrigger (4 components)

## Tables

- [`ORDERS`](tables/ORDERS.md) - used by 4 capabilit(y/ies)

## Other

- [Architecture](architecture.md)
- [Findings](findings.md)
- [Trading Networks usage](trading-networks.md)

## All components

- [`common.util:logEvent`](services/common.util__logEvent.md) - Flow service; Shared utility
- [`fulfil.docs:FulfilDoc`](services/fulfil.docs__FulfilDoc.md) - Document type; Data contract (document type)
- [`fulfil.process:allocateStock`](services/fulfil.process__allocateStock.md) - Flow service; Orchestration (flow)
- [`fulfil.process:notifyPartner`](services/fulfil.process__notifyPartner.md) - Flow service; Entry: not invoked by any scanned service (scheduler, manual or external caller?)
- [`fulfil.process:orchestrateFulfillment`](services/fulfil.process__orchestrateFulfillment.md) - Flow service; Entry: trigger fulfil.triggers:fulfilTrigger
- [`fulfil.triggers:fulfilTrigger`](services/fulfil.triggers__fulfilTrigger.md) - Trigger; Trigger (subscription)
- [`fulfil.util:computeShipping`](services/fulfil.util__computeShipping.md) - Flow service; Shared utility
- [`order.api.orders:_get`](services/order.api.orders___get.md) - Flow service; Entry: REST GET /rest/order/api/orders
- [`order.docs:CancelDoc`](services/order.docs__CancelDoc.md) - Document type; Data contract (document type)
- [`order.docs:OrderDoc`](services/order.docs__OrderDoc.md) - Document type; Data contract (document type)
- [`order.jdbc:insertOrder`](services/order.jdbc__insertOrder.md) - jdbc service; Data access (adapter)
- [`order.jdbc:selectOrder`](services/order.jdbc__selectOrder.md) - jdbc service; Data access (adapter)
- [`order.jdbc:updateOrderStatus`](services/order.jdbc__updateOrderStatus.md) - jdbc service; Data access (adapter)
- [`order.process:cancelOrder`](services/order.process__cancelOrder.md) - Flow service; Entry: trigger order.triggers:cancelTrigger
- [`order.process:submitOrder`](services/order.process__submitOrder.md) - Flow service; Entry: trigger order.triggers:orderTrigger
- [`order.process:validateOrder`](services/order.process__validateOrder.md) - Java service; Business logic (Java)
- [`order.triggers:cancelTrigger`](services/order.triggers__cancelTrigger.md) - Trigger; Trigger (subscription)
- [`order.triggers:orderTrigger`](services/order.triggers__orderTrigger.md) - Trigger; Trigger (subscription)
