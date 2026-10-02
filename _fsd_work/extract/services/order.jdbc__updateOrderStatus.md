# order.jdbc:updateOrderStatus

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/updateOrderStatus`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** JDBC adapter service that changes the status of an order when it has the expected current status.
- **Invoked by:** order.process:cancelOrder

## Signature
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `newStatus` | string |  |  |
| `orderId` | string |  |  |
| `expectedStatus` | string |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `updateCount` | string |  |  |


## SQL / statements found
```sql
UPDATE
```
```sql
UPDATE ORDERS SET STATUS = ? WHERE ORDER_ID = ? AND STATUS = ?
```

## Raw properties (secrets redacted)
| Key | Value |
|---|---|
| `node_type` | adapterService |
| `svc_type` | jdbc |
| `node_comment` | JDBC adapter service that changes the status of an order when it has the expected current status. |
| `connectionName` | OrderDB_Conn |
| `operationType` | UPDATE |
| `tableName` | ORDERS |
| `sqlStatement` | UPDATE ORDERS SET STATUS = ? WHERE ORDER_ID = ? AND STATUS = ? |
| `svc_sig.sig_in.rec_fields[0].field_name` | newStatus |
| `svc_sig.sig_in.rec_fields[0].field_type` | string |
| `svc_sig.sig_in.rec_fields[0].field_dim` | 0 |
| `svc_sig.sig_in.rec_fields[1].field_name` | orderId |
| `svc_sig.sig_in.rec_fields[1].field_type` | string |
| `svc_sig.sig_in.rec_fields[1].field_dim` | 0 |
| `svc_sig.sig_in.rec_fields[2].field_name` | expectedStatus |
| `svc_sig.sig_in.rec_fields[2].field_type` | string |
| `svc_sig.sig_in.rec_fields[2].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].field_name` | updateCount |
| `svc_sig.sig_out.rec_fields[0].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].field_dim` | 0 |
