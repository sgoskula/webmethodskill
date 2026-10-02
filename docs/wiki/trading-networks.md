# Trading Networks usage

[← index](index.md)

Calls to Trading Networks, grouped by operation. Partner profiles, document types, processing rules and delivery settings are configured in TN, outside the packages, so they are not in this wiki.

## Partner profile

- [`fulfil.process:notifyPartner`](services/fulfil.process__notifyPartner.md) calls `wm.tn.profile:getProfile`: partnerID ← partnerId

## Receive and recognise a document

- [`fulfil.process:notifyPartner`](services/fulfil.process__notifyPartner.md) calls `wm.tn:receive`: bizdoc/content ← shipNoticeXml; DocumentType = "ShipNotice"; SenderID = "FULFIL-HUB"; ReceiverID ← partnerId; apiPassword = "***redacted***"

## Route a document (processing rules decide the outcome)

- [`fulfil.process:notifyPartner`](services/fulfil.process__notifyPartner.md) calls `wm.tn:route`: bizdoc/InternalID ← bizdocId

## Update document status or attributes

- [`fulfil.process:notifyPartner`](services/fulfil.process__notifyPartner.md) calls `wm.tn.doc:setUserStatus`: InternalID ← bizdocId; userStatus = "SHIPNOTICE_SENT"
