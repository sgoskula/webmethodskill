# Functional Specification — Order Management (OrderProcessing + CommonUtils)

| Item | Value |
|---|---|
| Source packages | OrderProcessing 1.0, CommonUtils 1.0 |
| Generated from | Sample packages in `sample/` (synthetic test fixture for the `wm-fsd` agent/skill) |
| Status | Draft — reverse-engineered, pending SME review |

## 0. Summary in Plain English

*For readers who just want to know what this system does, what is wrong with it, and what to decide. Technical detail starts at Section 1.*

**What the system does.** It looks after customer orders. It receives new orders and cancellation
requests from other systems, keeps the orders in one database table, asks the payment gateway to
charge new orders, and lets other systems look up an order's status over the web. It sends nothing
back to the systems that gave it the orders.

**How a normal order goes through** (an order of 1000 or less):
1. A new order arrives from the storefront.
2. The system checks the order is valid.
3. It saves the order in the database with the status "PENDING".
4. It asks the payment gateway to charge the customer. If the gateway cannot be reached, it tries again, up to 4 attempts in total, 5 seconds apart.
5. It works out a "CONFIRMED" status and a confirmation number, but then throws them away. Nothing stores or sends them.

**What happens to the other requests**
- **A bigger order (over 1000)** is marked "needs approval" and then the system stops. It is not saved, not checked and not charged.
- **A cancellation** changes a saved "PENDING" order to "CANCELLED". If no such order exists, it is rejected and logged.
- **A status lookup** returns the order's number, status and amount. It answers "bad request" if no order number was given and "not found" if there is no such order.

**The five things you most need to know**
1. **Orders never show the real outcome.** Every saved order stays "PENDING" for ever, whether the payment worked or not. "CONFIRMED" and "FAILED" are never stored, so a status lookup cannot tell a paid order from an unpaid one.
2. **A paid order can be cancelled with no refund.** A cancellation only changes the status in the database. It never contacts the payment gateway. A cancellation that arrives while the payment is in progress does not stop the charge either.
3. **Orders over 1000 disappear.** They are never saved, so nobody can look them up, and a cancellation for them is rejected. The "needs approval" status is lost.
4. **A cancellation can get lost.** If the cancellation is processed before its order has been saved, it is rejected and is not tried again. The order is then created and stays active.
5. **A declined payment looks like a success.** The system only retries when the gateway cannot be reached. If the gateway answers with an error such as "payment declined", the system treats that as a success.

Failed requests are generally **not** retried automatically, and the original reason for a failure is mostly not recorded.

**What we could not find out from the code.** Who publishes the orders and cancellations, how the database connection handles failures, what the trigger does after its retries run out, and who is allowed to call the status lookup. These are listed in Section 13 (Open Questions).

**Decisions needed before a rewrite.** For each of the five issues above, decide whether the new system should copy the current behaviour exactly or fix it. They are listed with options in Section 12.2.

## Capabilities in plain English

**5.1 CAP-01 Order Submission.** When a new order arrives, this checks it, saves it as "PENDING" and asks the payment gateway to charge the customer. Orders over 1000 are only marked "needs approval" and then ignored. The "confirmed" status it works out at the end is never saved or sent anywhere, so the stored order always says "PENDING".

**5.2 CAP-02 Order Cancellation.** When a cancellation request arrives, this changes the matching order from "PENDING" to "CANCELLED". If there is no such order, it logs a rejection and fails. It does not refund the customer, and it does not record who asked for the cancellation.

**5.3 CAP-03 Order Status Lookup.** Other systems can ask "what is the status of order X?" over the web. The answer is the order number, status and amount, or "not found", or "bad request" when no order number was given. The status is always "PENDING" or "CANCELLED", because nothing ever stores any other value.

_Full detail, diagrams and open questions are in the complete FSD._
