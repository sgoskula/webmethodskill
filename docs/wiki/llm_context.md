# Application context for LLM questions

Facts extracted from webMethods Integration Server packages. Answer only from this text.

## Capabilities
- fulfil.process:orchestrateFulfillment: Entry: trigger fulfil.triggers:fulfilTrigger
- order.api.orders:_get: Entry: REST GET /rest/order/api/orders
- order.process:cancelOrder: Entry: trigger order.triggers:cancelTrigger
- order.process:submitOrder: Entry: trigger order.triggers:orderTrigger

## Findings
- fulfil.process:allocateStock: REPEAT with `COUNT=-1` on FAILURE has no upper bound: if the body keeps failing the flow never gives up and never reaches its error handling. A re-implementation needs an explicit maximum or timeout, so ask what it should be
- fulfil.process:allocateStock: BRANCH on `httpStatus` has no `$default`: values matching no case skip the branch silently
- fulfil.process:orchestrateFulfillment: BRANCH on `orderStatus` has no `$default`: values matching no case skip the branch silently
- fulfil.process:orchestrateFulfillment: `EXIT $flow FAILURE` ("Stock allocation failed") sits inside TRY [allocation], so it is caught by that TRY's CATCH and does not reach the caller as written. What the caller sees depends on what the CATCH does (swallow, rethrow, or its own EXIT)
- fulfil.process:orchestrateFulfillment: BRANCH on `lastAllocated` has no `$default`: values matching no case skip the branch silently
- fulfil.process:orchestrateFulfillment: BRANCH on `needsSpecialCarrier` has no `$default`: values matching no case skip the branch silently
- fulfil.process:orchestrateFulfillment: `allocations` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- fulfil.process:orchestrateFulfillment: `allocError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- fulfil.process:orchestrateFulfillment: Invoked by trigger fulfil.triggers:fulfilTrigger: Integration Server discards the outputs (fulfilStatus, trackingNumber). Only side effects (DB writes, calls, publishes) are visible to anyone
- fulfil.util:computeShipping: BRANCH on `priority` has no `$default`: values matching no case skip the branch silently
- fulfil.util:computeShipping: BRANCH on `weightKg`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- fulfil.util:computeShipping: `priority` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- order.process:submitOrder: BRANCH on `amount`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- order.process:submitOrder: `lineAmounts` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- order.process:submitOrder: `lastError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- order.process:submitOrder: `pub.client:http` does not fail on HTTP 4xx/5xx responses, and the flow never checks `header/status`. Error responses count as success, and REPEAT/TRY never sees them
- order.process:submitOrder: `status` is passed to adapter `order.jdbc:insertOrder` and changed afterwards, but no later adapter call saves the new value. The stored value is whatever it was at `order.jdbc:insertOrder`
- order.process:submitOrder: Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- order.process:submitOrder: Invoked by trigger order.triggers:orderTrigger: Integration Server discards the outputs (confirmationNumber, orderId, status). Only side effects (DB writes, calls, publishes) are visible to anyone
- order.process:validateOrder: Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- order.triggers:cancelTrigger: Trigger retries only happen when `order.process:cancelOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
- order.triggers:orderTrigger: Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
- Package `FulfillmentEngine` calls `OrderProcessing` (1 call(s)) but doesn't declare it in manifest.v3 `requires`, so load order isn't guaranteed
- Table `ORDERS` is shared by 4 capabilities (`fulfil.process:orchestrateFulfillment` SELECT; `order.api.orders:_get` SELECT; `order.process:cancelOrder` UPDATE; `order.process:submitOrder` INSERT). Document its lifecycle across capabilities and check how they interact (ordering, status assumptions, concurrency)
- Logging is inconsistent: `fulfil.process:orchestrateFulfillment` logs, `order.api.orders:_get` logs, `order.process:cancelOrder` logs, `order.process:submitOrder` has no logging
- Error handling is inconsistent: `fulfil.process:orchestrateFulfillment` uses TRY/CATCH, `order.api.orders:_get` has no TRY/CATCH, `order.process:cancelOrder` has no TRY/CATCH, `order.process:submitOrder` uses TRY/CATCH
- Hard-coded URL `http://wms.internal/stock/reserve` in `fulfil.process:allocateStock` instead of an endpoint alias or configuration value
- Hard-coded URL `https://carrier.example/api/book` in `fulfil.process:orchestrateFulfillment` instead of an endpoint alias or configuration value
- Hard-coded URL `https://payments.internal/charge` in `order.process:submitOrder` instead of an endpoint alias or configuration value
- All 3 adapter services share connection `OrderDB_Conn`; its transaction type and pool size affect every capability that uses it

## Components

### common.util:logEvent
**Overview**
# common.util:logEvent

- **Kind:** Flow service
- **Package:** CommonUtils
- **Role:** Shared utility
- **Source dir:** `sample/CommonUtils/ns/common/util/logEvent`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment, order.api.orders:_get, order.process:cancelOrder
- **Developer comment:** Writes one audit line to the server log for an order event.
- **Invoked by:** fulfil.process:orchestrateFulfillment, order.api.orders:_get, order.process:cancelOrder

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `eventType` | string |  |  |
| `orderId` | string |  |  |
| `message` | string | optional |  |

**Outputs:** _(none)_

**Invokes**
- `pub.flow:debugLog`

**Logic (pseudocode, generated from flow.xml)**
```text
# Build one audit line: EVENT order=ID message.
MAP: set logLine = "%eventType% order=%orderId% %message%" (with %var% substitution)
INVOKE pub.flow:debugLog
  input: message ← logLine; set function = "ORDER_AUDIT"; set level = "Info"
```

### fulfil.docs:FulfilDoc
**Overview**
# fulfil.docs:FulfilDoc

- **Kind:** Document type
- **Package:** FulfillmentEngine
- **Role:** Data contract (document type)
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/docs/FulfilDoc`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Published when an order is ready to be fulfilled.
- **Referenced by (trigger/REST/WSD/other):** fulfil.triggers:fulfilTrigger

**Fields**
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

### fulfil.process:allocateStock
**Overview**
# fulfil.process:allocateStock

- **Kind:** Flow service
- **Package:** FulfillmentEngine
- **Role:** Orchestration (flow)
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/process/allocateStock`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Allocates stock for one SKU. Returns allocated=true/false.
- **Invoked by:** fulfil.process:orchestrateFulfillment

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `sku` | string |  |  |
| `qty` | string |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `allocated` | string |  |  |
| `warehouse` | string |  |  |

**Invokes**
- `pub.client:http` — HTTP/REST call

**Logic (pseudocode, generated from flow.xml)**
```text
MAP: set allocated = "false"
# Poll the warehouse service until it answers without an exception (no upper bound).
REPEAT on FAILURE: re-run until it stops failing, 2s apart
  INVOKE pub.client:http   ⟵ HTTP/REST call
    input: set url = "http://wms.internal/stock/reserve"; data/sku ← sku; data/qty ← qty
    output: httpStatus ← header/status; warehouse ← warehouseCode
BRANCH on httpStatus
  CASE 200:
    SEQUENCE [200]
      MAP: set allocated = "true"
  CASE 409:
    # Out of stock: allocated stays false.
    SEQUENCE [409]
  (no $default: unmatched values fall through)
```

**Semantic flags (verify, then carry into the FSD)**
- REPEAT with `COUNT=-1` on FAILURE has no upper bound: if the body keeps failing the flow never gives up and never reaches its error handling. A re-implementation needs an explicit maximum or timeout, so ask what it should be
- BRANCH on `httpStatus` has no `$default`: values matching no case skip the branch silently

### fulfil.process:orchestrateFulfillment
**Overview**
# fulfil.process:orchestrateFulfillment

- **Kind:** Flow service
- **Package:** FulfillmentEngine
- **Role:** Entry: trigger fulfil.triggers:fulfilTrigger
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/process/orchestrateFulfillment`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Orchestrates fulfilment: stock allocation per item, shipping cost, carrier booking with retry, notification. Triggered by fulfilTrigger.
- **Referenced by (trigger/REST/WSD/other):** fulfil.triggers:fulfilTrigger

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `doc` | record → fulfil.docs:FulfilDoc |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `fulfilStatus` | string |  |  |
| `trackingNumber` | string |  |  |

**Invokes**
- `common.util:logEvent`
- `fulfil.process:allocateStock`
- `fulfil.util:computeShipping`
- `order.jdbc:selectOrder`
- `pub.client:http` — HTTP/REST call
- `pub.client:smtp` — Email (SMTP)
- `pub.flow:getLastError`
- `pub.flow:throwExceptionForRetry`

**Logic (pseudocode, generated from flow.xml)**
```text
# Seed pipeline from the FulfilDoc.
MAP: orderId ← doc/orderId; region ← doc/region; weightKg ← doc/weightKg; priority ← doc/priority; set fulfilStatus = "RECEIVED"
# Cross-package call into OrderProcessing (not declared in manifest requires).
INVOKE order.jdbc:selectOrder
  input: orderId ← orderId
  output: orderStatus ← orderRecord/status
# Only confirmed orders are fulfilled; no $default, so any other status silently continues.
BRANCH on orderStatus
  CASE CANCELLED:
    SEQUENCE [CANCELLED]
      INVOKE common.util:logEvent
        input: set eventType = "FULFIL_SKIPPED"; orderId ← orderId
      EXIT from $flow signal SUCCESS
  CASE PENDING_APPROVAL:
    SEQUENCE [PENDING_APPROVAL]
      EXIT from $flow signal FAILURE message "Order still awaiting approval"
  (no $default: unmatched values fall through)
# Allocate stock for every line item; any hazmat item diverts to special handling.
TRY [allocation]
  LOOP over doc/items → collect allocations
    SEQUENCE [perItem]
      BRANCH on doc/items/hazmat
        CASE Y:
          SEQUENCE [Y]
            INVOKE common.util:logEvent
              input: set eventType = "HAZMAT_ITEM"; message ← doc/items/sku
            MAP: set needsSpecialCarrier = "true"
            EXIT from $loop signal SUCCESS
        CASE $default:
          SEQUENCE [$default]
            INVOKE fulfil.process:allocateStock
              input: sku ← doc/items/sku; qty ← doc/items/qty
              output: allocations/allocated ← allocated; lastAllocated ← allocated
            BRANCH on lastAllocated
              CASE false:
                SEQUENCE [false]
                  MAP: set fulfilStatus = "BACKORDER"
                  EXIT from $flow signal FAILURE message "Stock allocation failed"  → caught by the CATCH of TRY [allocation]
              (no $default: unmatched values fall through)
CATCH
  INVOKE pub.flow:getLastError
    output: allocError ← lastError
  # Rethrown as ISRuntimeException so the trigger redelivers the document.
  INVOKE pub.flow:throwExceptionForRetry
    input: set message = "Allocation failed, retrying"
INVOKE fulfil.util:computeShipping
  input: region ← region; weightKg ← weightKg; priority ← priority
  output: shippingCost ← shippingCost; carrier ← carrier
BRANCH on needsSpecialCarrier
  CASE true:
    SEQUENCE [true]
      MAP: set carrier = "HAZMAT-LOGISTICS"
  (no $default: unmatched values fall through)
TRY [booking]
  # Book the carrier; retry twice on exception.
  REPEAT on FAILURE: re-run up to 2 more time(s) (max 3 attempts), 10s apart
    SEQUENCE [bookOnce] (exit on FAILURE)
      INVOKE pub.client:http   ⟵ HTTP/REST call
        input: set url = "https://carrier.example/api/book"; data/orderId ← orderId; data/carrier ← carrier
        output: bookingStatus ← header/status; trackingNumber ← trackingId
      BRANCH on bookingStatus
        CASE 503:
          SEQUENCE [503]
            EXIT from bookOnce signal FAILURE message "Carrier unavailable"
        CASE $default:
          SEQUENCE [$default]
  # Legacy notification, replaced by the email step below.
  (INVOKE pub.publish:publish DISABLED — not executed)
CATCH
  MAP: set fulfilStatus = "BOOKING_FAILED"
  EXIT from $flow signal FAILURE message "Carrier booking failed"
MAP: set fulfilStatus = "SHIPPED"; set body = "Order %orderId% shipped via %carrier%, tracking %trackingNumber%, cost %shippingCost%" (with %var% substitution)
INVOKE pub.client:smtp   ⟵ Email (SMTP)
  input: set to = "ops@example.com"; body ← body
```

**Semantic flags (verify, then carry into the FSD)**
- BRANCH on `orderStatus` has no `$default`: values matching no case skip the branch silently
- `EXIT $flow FAILURE` ("Stock allocation failed") sits inside TRY [allocation], so it is caught by that TRY's CATCH and does not reach the caller as written. What the caller sees depends on what the CATCH does (swallow, rethrow, or its own EXIT)
- BRANCH on `lastAllocated` has no `$default`: values matching no case skip the branch silently
- BRANCH on `needsSpecialCarrier` has no `$default`: values matching no case skip the branch silently
- `allocations` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- `allocError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- Invoked by trigger fulfil.triggers:fulfilTrigger: Integration Server discards the outputs (fulfilStatus, trackingNumber). Only side effects (DB writes, calls, publishes) are visible to anyone

### fulfil.triggers:fulfilTrigger
**Overview**
# fulfil.triggers:fulfilTrigger

- **Kind:** Trigger
- **Package:** FulfillmentEngine
- **Role:** Trigger (subscription)
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/triggers/fulfilTrigger`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Subscribes to FulfilDoc and starts fulfilment orchestration.

**Raw properties (secrets redacted)**
| Key | Value |
|---|---|
| `node_type` | trigger |
| `node_comment` | Subscribes to FulfilDoc and starts fulfilment orchestration. |
| `service` | fulfil.process:orchestrateFulfillment |
| `documentType` | fulfil.docs:FulfilDoc |
| `joinType` | NONE |
| `concurrency` | concurrent |
| `maxThreads` | 8 |
| `maxRetries` | 3 |
| `retryInterval` | 30 |

### fulfil.util:computeShipping
**Overview**
# fulfil.util:computeShipping

- **Kind:** Flow service
- **Package:** FulfillmentEngine
- **Role:** Shared utility
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/util/computeShipping`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Computes shipping cost from region, weight and priority.
- **Invoked by:** fulfil.process:orchestrateFulfillment

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `region` | string |  |  |
| `weightKg` | string |  |  |
| `priority` | string |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `shippingCost` | string |  |  |
| `carrier` | string |  |  |

**Logic (pseudocode, generated from flow.xml)**
```text
# Carrier and base rate depend on region; unknown regions are quoted manually.
BRANCH on region
  CASE EU:
    SEQUENCE [EU]
      MAP: set carrier = "DHL"; set shippingCost = "12.50"
      # Express upgrade within EU.
      BRANCH on priority
        CASE EXPRESS:
          SEQUENCE [EXPRESS]
            MAP: set shippingCost = "29.90"
        CASE $null:
          SEQUENCE [$null]
            # Priority missing: treated as standard, rate unchanged.
            MAP: set priority = "STANDARD"
        (no $default: unmatched values fall through)
  CASE US:
    SEQUENCE [US]
      MAP: set carrier = "FEDEX"
      BRANCH on weightKg
        WHEN %weightKg% > 30:
          SEQUENCE [%weightKg% > 30]
            MAP: set shippingCost = "85.00"
        WHEN %weightKg% > 10:
          SEQUENCE [%weightKg% > 10]
            MAP: set shippingCost = "40.00"
        WHEN $default:
          SEQUENCE [$default]
            MAP: set shippingCost = "18.00"
  CASE $default:
    SEQUENCE [$default]
      MAP: set carrier = "MANUAL"; set shippingCost = "0"
```

**Semantic flags (verify, then carry into the FSD)**
- BRANCH on `priority` has no `$default`: values matching no case skip the branch silently
- BRANCH on `weightKg`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- `priority` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing

### order.api.orders:_get
**Overview**
# order.api.orders:_get

- **Kind:** Flow service
- **Package:** OrderProcessing
- **Role:** Entry: REST GET /rest/order/api/orders
- **Source dir:** `sample/OrderProcessing/ns/order/api/orders/_get`
- **Used by capabilities:** order.api.orders:_get
- **Developer comment:** REST resource: returns the status of one order, identified by the orderId query parameter.

**Signature**
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

**Invokes**
- `common.util:logEvent`
- `order.jdbc:selectOrder`
- `pub.flow:setResponseCode`
- `pub.list:sizeOfList`

**Logic (pseudocode, generated from flow.xml)**
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

### order.docs:CancelDoc
**Overview**
# order.docs:CancelDoc

- **Kind:** Document type
- **Package:** OrderProcessing
- **Role:** Data contract (document type)
- **Source dir:** `sample/OrderProcessing/ns/order/docs/CancelDoc`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** Request to cancel an existing order, published by customer service.
- **Referenced by (trigger/REST/WSD/other):** order.triggers:cancelTrigger

**Fields**
**Document fields:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  |  |
| `reason` | string | optional |  |
| `requestedBy` | string |  | User or system that asked for the cancellation. |

### order.docs:OrderDoc
**Overview**
# order.docs:OrderDoc

- **Kind:** Document type
- **Package:** OrderProcessing
- **Role:** Data contract (document type)
- **Source dir:** `sample/OrderProcessing/ns/order/docs/OrderDoc`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** Canonical order document published by the storefront and consumed by order submission.
- **Referenced by (trigger/REST/WSD/other):** order.process:validateOrder, order.triggers:orderTrigger

**Fields**
**Document fields:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  | Unique order identifier generated upstream by the storefront. |
| `customerId` | string |  |  |
| `amount` | string |  | Order total in USD, represented as a decimal string. |
| `status` | string | optional |  |
| `lines[]` | record |  | Order line items. |
| `  sku` | string |  |  |
| `  qty` | string |  |  |
| `  price` | string |  |  |

### order.jdbc:insertOrder
**Overview**
# order.jdbc:insertOrder

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/insertOrder`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** JDBC adapter service that inserts a new order row into the ORDERS table.
- **Invoked by:** order.process:submitOrder

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderRecord` | record |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `rowsInserted` | string |  |  |

**SQL / statements found**
```sql
INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS) VALUES (?, ?, ?, ?)
```

**Raw properties (secrets redacted)**
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

### order.jdbc:selectOrder
**Overview**
# order.jdbc:selectOrder

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/selectOrder`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment, order.api.orders:_get
- **Developer comment:** JDBC adapter service that reads one order by its identifier.
- **Invoked by:** fulfil.process:orchestrateFulfillment, order.api.orders:_get

**Signature**
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

**SQL / statements found**
```sql
SELECT
```
```sql
SELECT ORDER_ID, CUSTOMER_ID, AMOUNT, STATUS FROM ORDERS WHERE ORDER_ID = ?
```

**Raw properties (secrets redacted)**
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

### order.jdbc:updateOrderStatus
**Overview**
# order.jdbc:updateOrderStatus

- **Kind:** jdbc service
- **Package:** OrderProcessing
- **Role:** Data access (adapter)
- **Source dir:** `sample/OrderProcessing/ns/order/jdbc/updateOrderStatus`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** JDBC adapter service that changes the status of an order when it has the expected current status.
- **Invoked by:** order.process:cancelOrder

**Signature**
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

**SQL / statements found**
```sql
UPDATE
```
```sql
UPDATE ORDERS SET STATUS = ? WHERE ORDER_ID = ? AND STATUS = ?
```

**Raw properties (secrets redacted)**
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

### order.process:cancelOrder
**Overview**
# order.process:cancelOrder

- **Kind:** Flow service
- **Package:** OrderProcessing
- **Role:** Entry: trigger order.triggers:cancelTrigger
- **Source dir:** `sample/OrderProcessing/ns/order/process/cancelOrder`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** Cancels a PENDING order and writes an audit log entry.
- **Referenced by (trigger/REST/WSD/other):** order.triggers:cancelTrigger

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `cancel` | record → order.docs:CancelDoc |  |  |

**Outputs:** _(none)_

**Invokes**
- `common.util:logEvent`
- `order.jdbc:updateOrderStatus`

**Logic (pseudocode, generated from flow.xml)**
```text
# Only orders still in PENDING can be cancelled.
INVOKE order.jdbc:updateOrderStatus
  input: orderId ← cancel/orderId; set newStatus = "CANCELLED"; set expectedStatus = "PENDING"
  output: rowsUpdated ← updateCount
BRANCH on rowsUpdated
  CASE 0:
    SEQUENCE [0]
      INVOKE common.util:logEvent
        input: set eventType = "CANCEL_REJECTED"; orderId ← cancel/orderId; set message = "not found or not PENDING"
      EXIT from $flow signal FAILURE message "Order not found or not cancellable"
  CASE $default:
    SEQUENCE [$default]
      INVOKE common.util:logEvent
        input: set eventType = "ORDER_CANCELLED"; orderId ← cancel/orderId; message ← cancel/reason
```

### order.process:submitOrder
**Overview**
# order.process:submitOrder

- **Kind:** Flow service
- **Package:** OrderProcessing
- **Role:** Entry: trigger order.triggers:orderTrigger
- **Source dir:** `sample/OrderProcessing/ns/order/process/submitOrder`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** Validates, persists and confirms a customer order. Triggered by orderTrigger when a new OrderDoc is published.
- **Referenced by (trigger/REST/WSD/other):** order.triggers:orderTrigger

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `order` | record → order.docs:OrderDoc |  |  |

**Outputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `orderId` | string |  |  |
| `status` | string |  |  |
| `confirmationNumber` | string | optional |  |

**Invokes**
- `order.jdbc:insertOrder`
- `order.process:validateOrder`
- `pub.client:http` — HTTP/REST call
- `pub.flow:getLastError`
- `pub.math:multiplyFloats`

**Logic (pseudocode, generated from flow.xml)**
```text
# Seed working pipeline variables from the incoming order document.
MAP: orderId ← order/orderId; customerId ← order/customerId; amount ← order/amount; set status = "PENDING"
# High value orders require manager approval before fulfillment.
BRANCH on amount
  WHEN %amount% > 1000:
    SEQUENCE [%amount% > 1000]
      MAP: set status = "PENDING_APPROVAL"
      EXIT from $flow signal SUCCESS
  WHEN $default:
    SEQUENCE [$default]
# Validate the order and persist it; any failure is handled in the CATCH block below.
TRY
  INVOKE order.process:validateOrder
    input: order ← order
  LOOP over order/lines → collect lineAmounts
    # Compute the extended amount for each line (qty * price).
    MAP: transformer pub.math:multiplyFloats [num1 ← order/lines/qty; num2 ← order/lines/price; lineAmounts ← value]
  INVOKE order.jdbc:insertOrder
    input: orderRecord/orderId ← orderId; orderRecord/customerId ← customerId; orderRecord/amount ← amount; orderRecord/status ← status
# Persistence or validation failed: log the error, mark the order failed and abort the flow.
CATCH
  INVOKE pub.flow:getLastError
    output: lastError ← lastError
  MAP: set status = "FAILED"
  EXIT from $flow signal FAILURE message "Order could not be validated or persisted"
# Charge the payment gateway; retry up to 3 times with a 5s back-off on failure.
REPEAT on FAILURE: re-run up to 3 more time(s) (max 4 attempts), 5s apart
  INVOKE pub.client:http   ⟵ HTTP/REST call
    input: set url = "https://payments.internal/charge"; data/orderId ← orderId; data/amount ← amount
MAP: set status = "CONFIRMED"; set confirmationNumber = "%orderId%-CONF" (with %var% substitution)
EXIT from $flow signal SUCCESS
```

**Semantic flags (verify, then carry into the FSD)**
- BRANCH on `amount`: `$default` also catches missing, empty and non-numeric values. Describe it as "any other value", never as the numeric opposite of the other cases
- `lineAmounts` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing
- `lastError` from `pub.flow:getLastError` is never logged, returned or rethrown, so the original error is lost
- `pub.client:http` does not fail on HTTP 4xx/5xx responses, and the flow never checks `header/status`. Error responses count as success, and REPEAT/TRY never sees them
- `status` is passed to adapter `order.jdbc:insertOrder` and changed afterwards, but no later adapter call saves the new value. The stored value is whatever it was at `order.jdbc:insertOrder`
- Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type
- Invoked by trigger order.triggers:orderTrigger: Integration Server discards the outputs (confirmationNumber, orderId, status). Only side effects (DB writes, calls, publishes) are visible to anyone

### order.process:validateOrder
**Overview**
# order.process:validateOrder

- **Kind:** Java service
- **Package:** OrderProcessing
- **Role:** Business logic (Java)
- **Source dir:** `sample/OrderProcessing/ns/order/process/validateOrder`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** Validates required order fields and that the amount is a positive number.
- **Invoked by:** order.process:submitOrder

**Signature**
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `order` | record → order.docs:OrderDoc |  |  |

**Outputs:** _(none)_

**Java body**
Source: `sample/OrderProcessing/code/source/order/process.java`
```java
public static void validateOrder(IData pipeline) throws ServiceException {
        IDataCursor cursor = pipeline.getCursor();
        IData order = (IData) IDataUtil.get(cursor, "order");
        cursor.destroy();

        IDataCursor orderCursor = order.getCursor();
        String orderId = IDataUtil.getString(orderCursor, "orderId");
        String amountStr = IDataUtil.getString(orderCursor, "amount");
        orderCursor.destroy();

        if (orderId == null || orderId.trim().length() == 0) {
            throw new ServiceException("orderId is required");
        }

        double amount;
        try {
            amount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            throw new ServiceException("amount must be numeric");
        }

        if (amount <= 0) {
            throw new ServiceException("amount must be greater than zero");
        }
    }
```

**Semantic flags (verify, then carry into the FSD)**
- Uses floating-point arithmetic (`double`/`float`) on values that may be money. A re-implementation must decide whether to copy that exactly or use a decimal type

### order.triggers:cancelTrigger
**Overview**
# order.triggers:cancelTrigger

- **Kind:** Trigger
- **Package:** OrderProcessing
- **Role:** Trigger (subscription)
- **Source dir:** `sample/OrderProcessing/ns/order/triggers/cancelTrigger`
- **Used by capabilities:** order.process:cancelOrder
- **Developer comment:** Subscribes to CancelDoc publications and invokes order cancellation.

**Raw properties (secrets redacted)**
| Key | Value |
|---|---|
| `node_type` | trigger |
| `node_comment` | Subscribes to CancelDoc publications and invokes order cancellation. |
| `service` | order.process:cancelOrder |
| `documentType` | order.docs:CancelDoc |
| `joinType` | NONE |
| `concurrency` | concurrent |
| `maxThreads` | 4 |
| `maxRetries` | 0 |
| `retryInterval` | 0 |

**Semantic flags (verify, then carry into the FSD)**
- Trigger retries only happen when `order.process:cancelOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried

### order.triggers:orderTrigger
**Overview**
# order.triggers:orderTrigger

- **Kind:** Trigger
- **Package:** OrderProcessing
- **Role:** Trigger (subscription)
- **Source dir:** `sample/OrderProcessing/ns/order/triggers/orderTrigger`
- **Used by capabilities:** order.process:submitOrder
- **Developer comment:** Subscribes to new OrderDoc publications from the storefront and invokes order submission.

**Raw properties (secrets redacted)**
| Key | Value |
|---|---|
| `node_type` | trigger |
| `node_comment` | Subscribes to new OrderDoc publications from the storefront and invokes order submission. |
| `service` | order.process:submitOrder |
| `documentType` | order.docs:OrderDoc |
| `filterCondition` | status == 'NEW' |
| `joinType` | NONE |
| `concurrency` | serial |
| `maxRetries` | 3 |
| `retryInterval` | 5 |

**Semantic flags (verify, then carry into the FSD)**
- Trigger retries only happen when `order.process:submitOrder` throws an ISRuntimeException (for example via `pub.flow:throwExceptionForRetry` or a transient adapter error). Its call tree never does this explicitly, so ordinary failures are not retried
