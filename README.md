# webMethods → FSD Kit

A VS Code (GitHub Copilot Agent mode) skill that reverse-engineers a **webMethods Integration Server** application into one detailed, **overall Functional Specification Document (FSD)**. However many flow services and packages there are, you get one document. It covers:
- the **existing architecture**
- business rules and every branch condition
- data mappings, error handling and integrations
- Mermaid diagrams
- **re-implementation notes for migrating to another language** (default Java)

It works in two layers:

1. **A deterministic extractor** (`wm_extract.py`, Python standard library only) parses the IS package files and produces compact facts: signatures, pseudocode with every condition, flowcharts, call graphs, and integrations. Nothing is left to the model's memory or to chance.
2. **A skill + agent** that drive the model through a phased workflow, turning those facts into a traceable, reviewable FSD.

Raw `flow.xml` is huge and easy to misread. Extracting first means no `BRANCH` case, `$default` fall-through, retry, or `CATCH` gets skipped, and it keeps the model's context free for writing.

## What's in the kit

```
.github/
├── agents/
│   ├── wm-fsd.agent.md                  # optional agent persona ("wm-fsd")
│   └── wm-ask.agent.md                  # optional agent persona for wiki Q&A ("wm-ask")
└── skills/
    ├── webmethods-wiki/                 # second skill: wiki + "ask questions about the functionality"
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── wm_wiki.py               # builds _wiki/ (linked pages, search index, llm_context.md)
    │       └── wm_ask.py                # retrieves the relevant facts and prints a grounded LLM prompt
    └── webmethods-fsd/
        ├── SKILL.md                     # the workflow the model follows
        ├── scripts/
        │   ├── wm_extract.py            # extractor: facts, semantic flags, existing architecture
        │   ├── assemble_fsd.py          # joins section files into one overall FSD
        │   └── check_mermaid.py         # offline Mermaid lint for the finished FSD
        └── references/
            ├── fsd-template.md          # FSD structure and per-capability section
            └── webmethods-artifacts.md  # raw IS artifacts + runtime semantics
sample/OrderProcessing/                  # synthetic IS packages used as test fixtures:
sample/CommonUtils/                      #   3 capabilities (2 triggers + 1 REST) and a shared package
sample/FulfillmentEngine/                 #   complex-flow stress sample (not in tests/FSD): nested BRANCH/LOOP/TRY/REPEAT, see its README
tests/test_wm_fsd.py                     # tests for the extractor, lint and sample FSD
docs/FSD.md                              # FSD generated from the sample package
```

## Wiki and questions (`webmethods-wiki` skill)

Besides the FSD, you can build a cross-linked wiki of the application and ask questions about its functionality:

> Build a wiki for `MyPackage`, then tell me what happens when a payment is declined.

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir>...
python .github/skills/webmethods-wiki/scripts/wm_wiki.py --extract _fsd_work/extract --out _wiki
python .github/skills/webmethods-wiki/scripts/wm_ask.py --wiki _wiki "What happens when carrier booking returns 503?"
```

`_wiki/` holds linked pages per capability, service and table, `findings.md`, and `llm_context.md` (the whole
application in one file, no diagrams) to attach to any LLM. `wm_ask.py` ranks the relevant facts, adds the matching
services' own logic and their callees', and prints a prompt that tells the LLM to answer only from them, cite sources
and say "Not in the extracted facts" when it can't. Retrieval is local (BM25, no network, no packages).

## Requirements

- VS Code with GitHub Copilot Chat in **Agent mode**, with a strong model selected (built and tuned for Claude Opus).
- Agent Skills support in your Copilot version/org policy (skills are loaded from `.github/skills/`).
- **Python 3.8+** on the machine (extractor only; no pip packages needed).
- The IS package folders available in the workspace (copied from `IntegrationServer/packages/<PackageName>` or from your source control).

## Quick start

1. Copy the `.github` folder into the root of the workspace that also contains your IS package folders.
2. Open the workspace in VS Code → Copilot Chat → **Agent** mode.
3. Ask:

   > Generate the FSD for package `MyPackage`.

   For several packages: *"Generate one FSD covering packages OrderPkg and CommonUtils."* Many flow services or packages still give **one overall FSD** with an Existing Architecture section. The extractor scans them all in one run, so cross-package calls, shared utilities and shared tables are visible.
4. The agent confirms scope, runs the extractor, shows you a capability plan, then writes the FSD one capability at a time.
5. Final output: **`docs/FSD.md`**.

Optional: pick the **wm-fsd** agent from the agent dropdown for the same workflow as a dedicated persona.

### Run the extractor on its own

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract <pkgDir> [<pkgDir> ...]
```

## How the workflow runs

| Phase | What happens | Output |
|---|---|---|
| 0. Scope | Confirms packages, audience, output path, migration target; asks for config that lives outside packages | |
| 1. Extract | Runs `wm_extract.py` once over all packages: facts, semantic flags, architecture | `_fsd_work/extract/` (incl. `architecture.md`) |
| 2. Plan | Groups services into business capabilities rooted at entry points | `_fsd_work/plan.md` |
| 3. Capabilities | One section per capability: trigger, I/O, sequence diagram, rules, mappings, integrations, errors, flowchart | `_fsd_work/sections/30-CAP-01.md`, `31-CAP-02.md`, … |
| 4a. Existing architecture | Package and component views, runtime/integration view, capability-to-component matrix, data ownership and entity lifecycle, how capabilities behave together, cross-cutting patterns, observations and risks | `_fsd_work/sections/10-architecture.md` |
| 4. Cross-cutting | Common services, data dictionary, integration and error catalogs, config, NFRs | `_fsd_work/sections/60-common.md` |
| 4b. Re-implementation | Target structure, construct mapping, behaviour decisions (reproduce or fix), data types, idempotency/transactions/concurrency, acceptance test cases | `_fsd_work/sections/70-reimplementation.md` |
| 5. Assemble | `assemble_fsd.py` joins the sections in file-name order. Checks coverage of services, branches, semantic flags and architecture observations. Checks for invented details. Lints Mermaid | `docs/FSD.md` |

**Resuming:** progress is ticked off in `_fsd_work/plan.md`. If the chat gets long or you start a new one, say *"Continue the FSD"* and it picks up at the first unticked item.

## What the extractor captures

- **Flow logic:** `BRANCH` (switch and label expressions, `$default`, and the *absence* of a default), `LOOP`, `REPEAT`/retry (total attempts, back-off), `TRY`/`CATCH`/`FINALLY`, `EXIT` with signal and message, `MAP` copy/set/drop/transformers, developer comments, and **disabled steps**.
- **Services:** inputs/outputs with types, optional/nillable flags and comments; Java service bodies; adapter service properties and SQL.
- **Structure:** document types, triggers and the services they call, entry points (services nothing else invokes), who-calls-whom, and package dependencies, startup and shutdown services.
- **Integrations:** HTTP/REST, SOAP, FTP/SFTP, SMTP, JMS, pub/sub, file I/O, Trading Networks, remote IS invokes, adapters, plus calls to services **outside the scanned packages**.
- **Semantic flags:** runtime behaviour that differs from what the code seems to intend: values computed but never used, errors swallowed in `CATCH`, `pub.client:http` status never checked, values changed after they were saved by an adapter, floating-point money, outputs discarded because a trigger invokes the service, trigger retries that can never happen, and what `$default` really matches.
- **Existing architecture** (`architecture.md`):
  - package dependency diagram, with undeclared dependencies flagged
  - role of every component (entry, orchestration, business logic, data access, shared utility, data contract)
  - component diagram, which drops to folder level for large applications
  - capabilities and their components, and shared components
  - external systems and channels, including REST resources (`_get`, `_post`, …)
  - table × capability data-access matrix, and document type usage
  - observations: shared tables, inconsistent logging or error handling, hard-coded URLs, one shared connection
- **Safety:** values under keys that look like password, secret, token or credential are redacted.

## What the FSD contains

Introduction and glossary · system context diagram · **existing architecture** (package, component and runtime views, capability-to-component matrix, entity lifecycle state diagrams, cross-capability findings, cross-cutting patterns, risks) · capability summary · per capability: overview, trigger, inputs/outputs, **sequence diagram**, processing steps, **decision tables**, validations, **data mappings**, integrations used, **error and retry table**, **process flowchart**, notes · common services · data dictionary · integration catalog · error catalog · configuration and environment dependencies · non-functional characteristics seen in code · **re-implementation notes** (construct mapping, behaviour decisions, data types, idempotency, acceptance test cases) · **open questions** · service inventory · coverage report.

Ground rules baked into the skill:

- **No invented behaviour.** Anything not in the code is marked `[TO CONFIRM: …]` and collected under Open Questions.
- **Runtime semantics over intent.** The FSD says what Integration Server actually does (e.g. "the database row stays `PENDING`"), not what the code appears to aim for.
- **Traceability.** Every rule and mapping cites its source service.
- **No secrets** are copied into any output.

## Tips for best results

- **Provide what lives outside the packages** if you can: scheduler task export, global variables, endpoint/connection aliases, JMS/UM settings, Trading Networks rules. Missing items become Open Questions rather than guesses.
- **Large applications:** still scan all packages in one extractor run (so the architecture is complete), then write one capability per turn and let the plan file track progress. The result is still one overall FSD.
- **Add `_fsd_work/` to `.gitignore`** if you don't want intermediate files committed. Keep `docs/FSD.md`.
- **Rendering Mermaid:** GitHub renders Mermaid in Markdown natively. In VS Code, use a Mermaid-capable Markdown preview extension. For Word or PDF, render diagrams to images first (for example with mermaid-cli), then convert with pandoc.
- **Review with an SME.** The FSD is reverse-engineered from code and is a strong draft, not a sign-off. Check the Open Questions and the coverage report first.

## Limitations

- Developed and tested against a small **synthetic** package, not a production application. IS versions differ in `node.ndf` details; on your first run, spot-check adapter services and triggers in the extract (the "Raw properties" section) against Designer.
- Static analysis only: it cannot see runtime data, environment-specific values stored outside packages, or behaviour inside external systems.
- Very large flows may exceed the diagram size limit; the extractor then skips the auto-diagram and the skill draws one per top-level sequence.
- Components such as BPM/MWS process models and Trading Networks configuration are not parsed; they surface as dependencies or open questions.

## Troubleshooting

| Symptom | Try |
|---|---|
| Skill isn't picked up | Confirm the path is `.github/skills/webmethods-fsd/SKILL.md` in the workspace root, you're in Agent mode, and Agent Skills are allowed by your Copilot version/org policy. Mention "webMethods FSD" in your prompt. |
| `python` not found | Install Python 3.8+, or try `python3`/`py`. Without Python the skill falls back to reading raw files via `references/webmethods-artifacts.md` (slower). |
| Extract reports 0 nodes | Point at the package folder itself (the one containing `ns/` and `manifest.v3`), not its parent. |
| Mermaid diagram fails to render | Run `python .github/skills/webmethods-fsd/scripts/check_mermaid.py docs/FSD.md`, then ask *"Fix the Mermaid syntax in section X."* Common causes are unquoted labels with brackets, `;` in sequence diagrams, missing `end`, and too many nodes. In VS Code, also check a Mermaid preview extension is installed. |
| Chat runs out of context | Start a new chat and say *"Continue the FSD."* |

## Security notes

- The extractor only **reads** package files and writes Markdown/JSON; it makes no network calls.
- Copilot will run it in your terminal, so review `wm_extract.py` and get it approved per your organisation's policy before use.
- Secrets in adapter and connection nodes are redacted in the extract, but review `_fsd_work/` before sharing it.

## Testing the kit

```
python3 -m unittest discover -s tests -v
```

The tests run the extractor on both sample packages and check that it:
- finds the 3 entry points and redacts secrets
- extracts Java and SQL, and draws the REPEAT loop correctly
- raises the expected semantic flags, with no false positives
- builds the right architecture: roles, shared components, the cross-package call, the `ORDERS` data-access matrix and observations
- falls back to a folder-level diagram for large applications, and flags undeclared package dependencies

They also cover `assemble_fsd.py` and `check_mermaid.py`, and check that `docs/FSD.md` is one overall FSD with valid diagrams and resolvable cross-references. After changing the samples, regenerate the FSD with the agent and run the tests again.

## Customising

- Change the FSD layout in `references/fsd-template.md`.
- Add your organisation's naming conventions, glossary or mandatory sections to `SKILL.md`.
- Extend `INTEGRATION_PREFIXES` in `wm_extract.py` to flag your custom wrapper services as integrations.
