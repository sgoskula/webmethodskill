# FSD plan
- [x] CAP-01 Order submission — entry `order.process:submitOrder` (trigger `order.triggers:orderTrigger`)
- [x] CAP-02 Order cancellation — entry `order.process:cancelOrder` (trigger `order.triggers:cancelTrigger`)
- [x] CAP-03 Order status lookup — entry `order.api.orders:_get` (REST GET /rest/order/api/orders)
- [x] Existing architecture
- [x] Cross-cutting: data dictionary, integrations, errors, config, NFRs
- [x] Re-implementation notes (target: Java)
- [x] Assembly + coverage check
