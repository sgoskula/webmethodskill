# order.jdbc:insertOrder

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/insertOrder`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** JDBC adapter service that inserts a new order row into the ORDERS table.
- **Invoked by:** order.process:submitOrder

## Signature
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderRecord` | record |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `rowsInserted` | string |  |  |


## SQL / statements found
```sql
INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS) VALUES (?, ?, ?, ?)
```

## Raw properties (secrets redacted)
| Key | Value |
|---|---|
| `node_type` | adapterService |
| `svc_type` | jdbc |
| `node_comment` | JDBC adapter service that inserts a new order row into the ORDERS table. |
| `connectionName` | OrderDB_Conn |
| `operationType` | INSERT |
| `tableName` | ORDERS |
| `sqlStatement` | INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS) VALUES (?, ?, ?, ?) |
| `password` | ***redacted*** |
| `svc_sig.sig_in.rec_fields[0].field_name` | orderRecord |
| `svc_sig.sig_in.rec_fields[0].field_type` | record |
| `svc_sig.sig_in.rec_fields[0].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].field_name` | rowsInserted |
| `svc_sig.sig_out.rec_fields[0].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].field_dim` | 0 |
