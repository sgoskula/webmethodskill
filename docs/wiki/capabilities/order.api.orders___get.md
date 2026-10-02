# Capability: order.api.orders:_get

[← index](../index.md) · Entry: REST GET /rest/order/api/orders

## Components used

- [`common.util:logEvent`](../services/common.util__logEvent.md) - Shared utility
- [`order.api.orders:_get`](../services/order.api.orders___get.md) - Entry: REST GET /rest/order/api/orders
- [`order.jdbc:selectOrder`](../services/order.jdbc__selectOrder.md) - Data access (adapter)

## Findings in this capability

- none

## Call graph

```mermaid
flowchart LR
  s_order_api_orders__get["order.api.orders:_get"] --> s_common_util_logEvent["common.util:logEvent"]
  s_order_api_orders__get["order.api.orders:_get"] --> s_order_jdbc_selectOrder["order.jdbc:selectOrder"]
```
