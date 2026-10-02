# Table ORDERS

[← index](../index.md)

## Capabilities and operations

- [`fulfil.process:orchestrateFulfillment`](../capabilities/fulfil.process__orchestrateFulfillment.md): SELECT
- [`order.api.orders:_get`](../capabilities/order.api.orders___get.md): SELECT
- [`order.process:cancelOrder`](../capabilities/order.process__cancelOrder.md): UPDATE
- [`order.process:submitOrder`](../capabilities/order.process__submitOrder.md): INSERT

## Adapter services touching it

- [`order.jdbc:insertOrder`](../services/order.jdbc__insertOrder.md) (INSERT, connection `OrderDB_Conn`)
- [`order.jdbc:selectOrder`](../services/order.jdbc__selectOrder.md) (SELECT, connection `OrderDB_Conn`)
- [`order.jdbc:updateOrderStatus`](../services/order.jdbc__updateOrderStatus.md) (UPDATE, connection `OrderDB_Conn`)
