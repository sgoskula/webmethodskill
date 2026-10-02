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

## All nodes
| Name | Kind | Comment |
|---|---|---|
| `order.docs:OrderDoc` | Document type | Canonical order document published by the storefront and consumed by order submi |
| `order.jdbc:insertOrder` | jdbc service | JDBC adapter service that inserts a new order row into the ORDERS table. |
| `order.process:submitOrder` | Flow service | Validates, persists and confirms a customer order. Triggered by orderTrigger whe |
| `order.process:validateOrder` | Java service | Validates required order fields and that the amount is a positive number. |
| `order.triggers:orderTrigger` | Trigger | Subscribes to new OrderDoc publications from the storefront and invokes order su |
