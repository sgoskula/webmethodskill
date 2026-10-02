# order.api.orders:_get

- **Kind:** Flow service
- **Package:** OrderProcessing
- **Role:** Entry: REST GET /rest/order/api/orders
- **Source dir:** `sample/OrderProcessing/ns/order/api/orders/_get`
- **Used by capabilities:** order.api.orders:_get
- **Developer comment:** REST resource: returns the status of one order, identified by the orderId query parameter.

## Signature
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string | optional | Query parameter. |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `order` | record | optional |  |
| `  orderId` | string |  |  |
| `  status` | string |  |  |
| `  amount` | string |  |  |
| `error` | string | optional |  |


## Invokes
- `common.util:logEvent`
- `order.jdbc:selectOrder`
- `pub.flow:setResponseCode`
- `pub.list:sizeOfList`

## Logic (pseudocode, generated from flow.xml)
```text
# Reject requests that have no orderId query parameter.
BRANCH on orderId
  CASE $null:
    SEQUENCE [$null]
      INVOKE pub.flow:setResponseCode
        input: set responseCode = "400"; set reasonPhrase = "Bad Request"
      MAP: set error = "orderId is required"
      EXIT from $flow signal SUCCESS
  CASE $default:
    SEQUENCE [$default]
INVOKE order.jdbc:selectOrder
  input: orderId ← orderId
  output: results ← results
INVOKE pub.list:sizeOfList
  input: fromList ← results
  output: resultCount ← size
BRANCH on resultCount
  CASE 0:
    SEQUENCE [0]
      INVOKE pub.flow:setResponseCode
        input: set responseCode = "404"; set reasonPhrase = "Not Found"
      MAP: set error = "Order not found"
      EXIT from $flow signal SUCCESS
  CASE $default:
    SEQUENCE [$default]
      MAP: order/orderId ← results/ORDER_ID; order/status ← results/STATUS; order/amount ← results/AMOUNT
INVOKE common.util:logEvent
  input: set eventType = "ORDER_QUERY"; orderId ← orderId
```

## Flowchart
```mermaid
flowchart TD
  n1(["Start"])
  n2{"BRANCH on orderId"}
  n1 --> n2
  n3["pub.flow:setResponseCode"]
  n2 -->|"$null"| n3
  n4["MAP: 1 op(s)"]
  n3 --> n4
  n5(["EXIT from $flow signal SUCCESS"])
  n4 --> n5
  n6["order.jdbc:selectOrder"]
  n2 --> n6
  n7["pub.list:sizeOfList"]
  n6 --> n7
  n8{"BRANCH on resultCount"}
  n7 --> n8
  n9["pub.flow:setResponseCode"]
  n8 -->|"0"| n9
  n10["MAP: 1 op(s)"]
  n9 --> n10
  n11(["EXIT from $flow signal SUCCESS"])
  n10 --> n11
  n12["MAP: 3 op(s)"]
  n8 -->|"$default"| n12
  n13["common.util:logEvent"]
  n12 --> n13
  n14(["End"])
  n13 --> n14
```
