# fulfil.triggers:fulfilTrigger

[← index](../index.md) · kind: **Trigger** · role: Trigger (subscription)

## Overview


- **Kind:** Trigger
- **Package:** FulfillmentEngine
- **Role:** Trigger (subscription)
- **Source dir:** `sample/FulfillmentEngine/ns/fulfil/triggers/fulfilTrigger`
- **Used by capabilities:** fulfil.process:orchestrateFulfillment
- **Developer comment:** Subscribes to FulfilDoc and starts fulfilment orchestration.

## Raw properties (secrets redacted)

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
