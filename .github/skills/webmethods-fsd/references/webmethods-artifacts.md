# Reading raw webMethods IS artifacts

Use this when the extractor output is unclear, a node type isn't recognised, or Python is not
available. Formats vary slightly across IS versions; read defensively.

## Package layout
```
<Package>/
  manifest.v3          version, requires (package deps), startup/shutdown services
  ns/<folder>/<sub>/<node>/node.ndf    one per element; folders map to "folder.sub:node"
  ns/.../<service>/flow.xml            flow service logic
  code/source/<folder path>.java       Java services (between <<IS-START(name)>> and <<IS-END>>)
  config/              package config files (custom properties, often environment-specific)
  pub/                 web content
```
Fully qualified name: path under `ns/` with dots, last segment after a colon:
`ns/order/process/submitOrder` → `order.process:submitOrder`.

## node.ndf (IData XML)
`<Values>` / `<record>` = map, `<array>` = list, `<value name="...">` = scalar.
Key fields: `node_type` (service, record, trigger types, connection types…), `svc_type`
(flow, java, spec, or adapter-specific), `node_comment`, `svc_sig/sig_in|sig_out/rec_fields`
(each field: `field_name`, `field_type`, `field_dim` 0=single 1=list, `rec_ref` = doc type
reference, `field_opt`, `nillable`).

- **Document types**: `rec_fields` at top level; nested records inside.
- **Adapter services** (JDBC, SAP, MQ…): config nests under adapter-specific keys; look for the
  connection alias, table names, SQL text, operation type, input/output field lists.
- **Adapter connections**: hostnames, schemas, pool settings. Passwords are encrypted
  references; never reproduce them.
- **Triggers**: conditions → document types subscribed, filter expressions, invoked service,
  join type; plus concurrency (serial/concurrent, thread count) and retry/error settings.
- **REST resources / REST API descriptors, Web service descriptors**: map HTTP verbs + paths or
  SOAP operations to services; capture auth/ACL if present.

## flow.xml elements
| Element | Meaning | Key attributes |
|---|---|---|
| `FLOW` | root | |
| `SEQUENCE` | block | `EXIT-ON` (FAILURE/SUCCESS/DONE), `FORM` = TRY/CATCH/FINALLY on newer IS, `NAME` = case label when inside BRANCH |
| `BRANCH` | switch | `SWITCH` = pipeline var; `LABELEXPRESSIONS="true"` → child NAMEs are boolean expressions; `$null`, `$default` special labels |
| `LOOP` | for-each | `IN-ARRAY`, `OUT-ARRAY` |
| `RETRY` / REPEAT | retry loop | `COUNT` (-1 = forever), `BACK-OFF` seconds, `LOOP-ON` FAILURE/SUCCESS |
| `INVOKE` | call service | `SERVICE`, `VALIDATE-IN/OUT`; child `MAP MODE="INPUT"/"OUTPUT"` |
| `MAP` | transformation | children `MAPCOPY FROM→TO`, `MAPSET FIELD` (literal in `DATA/Values/value`), `MAPDELETE FIELD`, `MAPINVOKE SERVICE` (transformer) |
| `EXIT` | exit | `FROM` ($parent, $loop, $flow, or a label), `SIGNAL` SUCCESS/FAILURE, `FAILURE-MESSAGE` |
| `COMMENT` | developer comment | text content |
| any step | | `DISABLED="true"` means not executed |

Field paths look like `/order;4;0/lines;4;1/sku;1;0` → keep only the names: `order/lines/sku`.
`%var%` inside set values means pipeline variable substitution when `VARIABLES="true"`.

## Common built-ins worth noting in an FSD
- `pub.flow:getLastError`, `pub.flow:throwExceptionForRetry` → error handling / retry semantics
- `pub.client:http`, `pub.client:soap*`, `pub.client:ftp`, `pub.client:sftp*`, `pub.client:smtp`
- `pub.jms:send`, `pub.jms:sendAndWait`, `pub.publish:publish*` → async messaging
- `pub.art.transaction:*` → explicit transaction boundaries (commit/rollback)
- `pub.storage:lock` / `pub.cache:*` → concurrency control / caching
- `pub.flow:debugLog`, `pub.flow:tracePipeline` → logging only (omit from business flow)
- `pub.string:*`, `pub.list:*`, `pub.math:*`, `pub.date:*` → mapping detail only

## Outside the package (ask the user for exports)
Scheduler tasks, global variables, endpoint aliases, JDBC/JMS/UM connection settings,
Trading Networks processing rules and partner profiles, MWS/BPM process models.
