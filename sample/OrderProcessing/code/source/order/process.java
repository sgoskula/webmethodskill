package order.process;

import com.wm.data.*;
import com.wm.util.Values;
import com.wm.app.b2b.server.ServiceException;

public final class process {

    // --- <<IS-START(validateOrder)>> --- (SERVICE)
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
    // --- <<IS-END>> --- (SERVICE)
}
