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
| `LOOP` | for-each | `IN-ARRAY`, `OUT-ARRAY` (see runtime semantics) |
| `RETRY` / REPEAT | retry loop | `COUNT` = number of *re*-executions (total attempts = COUNT + 1; -1 = until the LOOP-ON condition stops), `BACK-OFF` seconds, `LOOP-ON` FAILURE/SUCCESS |
| `INVOKE` | call service | `SERVICE`, `VALIDATE-IN/OUT`; child `MAP MODE="INPUT"/"OUTPUT"` |
| `MAP` | transformation | children `MAPCOPY FROM→TO`, `MAPSET FIELD` (literal in `DATA/Values/value`), `MAPDELETE FIELD`, `MAPINVOKE SERVICE` (transformer) |
| `EXIT` | exit | `FROM` ($parent, $loop, $flow, or a label), `SIGNAL` SUCCESS/FAILURE, `FAILURE-MESSAGE` |
| `COMMENT` | developer comment | text content |
| any step | | `DISABLED="true"` means not executed |

Field paths look like `/order;4;0/lines;4;1/sku;1;0` → keep only the names: `order/lines/sku`.
`%var%` inside set values means pipeline variable substitution when `VARIABLES="true"`.

## Runtime semantics (what really happens)

Check each of these when describing behaviour. `wm_extract.py` flags most of them automatically
("Semantic flags"); without Python, apply them by hand. Where your IS version or configuration
might differ, state the assumption as `[TO CONFIRM]`.

| Construct | Runtime behaviour | FSD / migration consequence |
|---|---|---|
| Service invoked by a trigger | Its output pipeline is discarded. Only side effects (DB writes, calls, publishes) persist | Mark outputs "discarded"; a confirmation value nobody publishes is lost |
| Trigger retry settings | Retries happen only when the service throws an ISRuntimeException (`pub.flow:throwExceptionForRetry`, or a transient adapter error). A normal `ServiceException` / `EXIT FAILURE` is not retried. After retries run out, the "on retry failure" setting decides between throwing and suspending the trigger | Don't write "retried N times" unless the call tree raises retryable errors |
| `pub.client:http` | Fails only on transport errors (connection, timeout, bad URL). 4xx/5xx responses return normally with `header/status` | Unless the flow checks `header/status`, error responses (e.g. payment declined) count as success, and REPEAT/TRY doesn't retry them |
| `REPEAT COUNT="n" LOOP-ON="FAILURE"` | Re-runs its children up to n more times while a child step fails (throws) | Total attempts = n + 1; "failure" means an exception, not a bad response |
| `BRANCH` `$default` | Matches every value no other case matched, including null/missing and, with label expressions, values that aren't numbers | Word the row "any other value…", not "≤ X". `$null` is a separate label for missing values |
| Label expressions (`%amount% > 1000`) | Pipeline values are usually strings; how they compare to numbers can depend on the IS version and on the value | `[TO CONFIRM]` behaviour for decimals and non-numeric input, especially when the branch runs before validation |
| `LOOP IN-ARRAY="a/list"` | Inside the loop, `a/list` refers to the *current element*, not the list | Read paths inside a loop as per-item fields |
| `LOOP OUT-ARRAY="xs"` | Each iteration, the pipeline variable named `xs` is appended to the output list | Check whether `xs` is ever used after the loop |
| TRY / CATCH | CATCH runs on any failure in TRY. If CATCH doesn't rethrow or `EXIT … FAILURE`, the service *succeeds*. `pub.flow:getLastError` only reads the error; it doesn't log it | Say whether the original error is logged, returned or lost |
| `EXIT FROM="$flow" SIGNAL="SUCCESS"` | Ends the whole service successfully; later steps don't run | Branch cases that exit early skip everything after them |
| Adapter services on a LOCAL/XA connection | IS starts an implicit transaction and commits or rolls back when the top-level service ends, unless `pub.art.transaction:*` sets explicit boundaries. NO_TRANSACTION commits each statement right away | Whether a saved row survives a later failure depends on the connection's transaction type → `[TO CONFIRM]` |
| Value saved by an adapter, then changed | The database keeps the value from the time of the adapter call | State the stored value; a status set afterwards is never saved unless a later call writes it |
| Pipeline data types | Most values are `String`; `pub.math:*Floats` and Java `double` use binary floating point | List the numeric fields; decide on decimal types for money in a migration |
| `%var%` in MAPSET with `VARIABLES="true"` | Replaced with the pipeline value at runtime, as text | Map to string building in the target |

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
