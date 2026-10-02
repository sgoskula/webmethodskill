# Capability: fulfil.process:notifyPartner

[← index](../index.md) · Entry: not invoked by any scanned service (scheduler, manual or external caller?)

## Components used

- [`fulfil.process:notifyPartner`](../services/fulfil.process__notifyPartner.md) - Entry: not invoked by any scanned service (scheduler, manual or external caller?)

## Findings in this capability

- `fulfil.process:notifyPartner`: `partnerName` is set but never used afterwards (not read later, not a declared output). Either it is dead logic or a step is missing

## Call graph

```mermaid
flowchart LR
  s_fulfil_process_notifyPartner["fulfil.process:notifyPartner"] --> s_wm_tn_doc_setUserStatus["wm.tn.doc:setUserStatus"]
  s_fulfil_process_notifyPartner["fulfil.process:notifyPartner"] --> s_wm_tn_profile_getProfile["wm.tn.profile:getProfile"]
  s_fulfil_process_notifyPartner["fulfil.process:notifyPartner"] --> s_wm_tn_receive["wm.tn:receive"]
  s_fulfil_process_notifyPartner["fulfil.process:notifyPartner"] --> s_wm_tn_route["wm.tn:route"]
```
