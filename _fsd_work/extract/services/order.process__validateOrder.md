# order.process:validateOrder

- **Kind:** Java service
- **Package:** OrderProcessing
- **Source dir:** `sample/OrderProcessing/ns/order/process/validateOrder`
- **Developer comment:** Validates required order fields and that the amount is a positive number.
- **Invoked by:** order.process:submitOrder

## Signature
**Inputs:**

| Field | Type | Flags | Comment |
|---|---|---|---|
| `order` | record → order.docs:OrderDoc |  |  |

**Outputs:** _(none)_


## Java body
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
