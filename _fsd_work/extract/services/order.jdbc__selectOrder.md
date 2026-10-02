# order.jdbc:selectOrder

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/selectOrder`
- **Used by capabilities:** order.api.orders:_get
- **Developer comment:** JDBC adapter service that reads one order by its identifier.
- **Invoked by:** order.api.orders:_get

## Signature
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `results[]` | record |  |  |
| `  ORDER_ID` | string |  |  |
| `  CUSTOMER_ID` | string |  |  |
| `  AMOUNT` | string |  |  |
| `  STATUS` | string |  |  |


## SQL / statements found
```sql
SELECT
```
```sql
SELECT ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS FROM ORDERS WHERE ORDER_ID = ?
```

## Raw properties (secrets redacted)
| Key | Value |
|---|---|
| `node_type` | adapterService |
| `svc_type` | jdbc |
| `node_comment` | JDBC adapter service that reads one order by its identifier. |
| `connectionName` | OrderDB_Conn |
| `operationType` | SELECT |
| `tableName` | ORDERS |
| `sqlStatement` | SELECT ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS FROM ORDERS WHERE ORDER_ID = ? |
| `svc_sig.sig_in.rec_fields[0].field_name` | orderId |
| `svc_sig.sig_in.rec_fields[0].field_type` | string |
| `svc_sig.sig_in.rec_fields[0].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].field_name` | results |
| `svc_sig.sig_out.rec_fields[0].field_type` | record |
| `svc_sig.sig_out.rec_fields[0].field_dim` | 1 |
| `svc_sig.sig_out.rec_fields[0].rec_fields[0].field_name` | ORDER_ID |
| `svc_sig.sig_out.rec_fields[0].rec_fields[0].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].rec_fields[0].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].rec_fields[1].field_name` | CUSTOMER_ID |
| `svc_sig.sig_out.rec_fields[0].rec_fields[1].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].rec_fields[1].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].rec_fields[2].field_name` | AMOUNT |
| `svc_sig.sig_out.rec_fields[0].rec_fields[2].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].rec_fields[2].field_dim` | 0 |
| `svc_sig.sig_out.rec_fields[0].rec_fields[3].field_name` | STATUS |
| `svc_sig.sig_out.rec_fields[0].rec_fields[3].field_type` | string |
| `svc_sig.sig_out.rec_fields[0].rec_fields[3].field_dim` | 0 |
