# webMethods → FSD Kit

A VS Code (GitHub Copilot Agent mode) skill that reverse-engineers a **webMethods Integration Server** application into a detailed **Functional Specification Document (FSD)**: business rules, every branch condition, data mappings, error handling, integrations, and Mermaid diagrams.

It works in two layers:

1. **A deterministic extractor** (`wm_extract.py`, Python standard library only) parses the IS package files and produces compact facts: signatures, pseudocode with every condition, flowcharts, call graphs, and integrations. Nothing is left to the model's memory or to chance.
2. **A skill + agent** that drive the model through a phased workflow, turning those facts into a traceable, reviewable FSD.

Raw `flow.xml` is huge and easy to misread. Extracting first means no `BRANCH` case, `$default` fall-through, retry, or `CATCH` gets skipped, and it keeps the model's context free for writing.

## What's in the kit

```
.github/
├── agents/
│   └── wm-fsd.agent.md                  # optional agent persona ("wm-fsd")
└── skills/
    └── webmethods-fsd/
        ├── SKILL.md                     # the workflow the model follows
        ├── scripts/
        │   └── wm_extract.py            # deterministic package extractor
        └── references/
            ├── fsd-template.md          # FSD structure and per-capability section
            └── webmethods-artifacts.md  # how to read raw IS artifacts (fallback)
```

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

   For several packages: *"Generate one FSD covering packages OrderPkg and CommonUtils."*
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
| 0. Scope | Confirms packages, audience, output path; asks for config that lives outside packages | |
| 1. Extract | Runs `wm_extract.py` | `_fsd_work/extract/` |
| 2. Plan | Groups services into business capabilities rooted at entry points | `_fsd_work/plan.md` |
| 3. Capabilities | One section per capability: trigger, I/O, sequence diagram, rules, mappings, integrations, errors, flowchart | `_fsd_work/sections/CAP-xx.md` |
| 4. Cross-cutting | Context diagram, data dictionary, integration and error catalogs, config, NFRs | `_fsd_work/sections/common.md` |
| 5. Assemble | Builds the FSD and runs a coverage check against the inventory | `docs/FSD.md` |

**Resuming:** progress is ticked off in `_fsd_work/plan.md`. If the chat gets long or you start a new one, say *"Continue the FSD"* and it picks up at the first unticked item.

## What the extractor captures

- **Flow logic:** `BRANCH` (switch and label expressions, `$default`, and the *absence* of a default), `LOOP`, `REPEAT`/retry (count, back-off), `TRY`/`CATCH`/`FINALLY`, `EXIT` with signal and message, `MAP` copy/set/drop/transformers, developer comments, and **disabled steps**.
- **Services:** inputs/outputs with types, optional/nillable flags and comments; Java service bodies; adapter service properties and SQL.
- **Structure:** document types, triggers and the services they call, entry points (services nothing else invokes), who-calls-whom, and package dependencies, startup and shutdown services.
- **Integrations:** HTTP/REST, SOAP, FTP/SFTP, SMTP, JMS, pub/sub, file I/O, Trading Networks, remote IS invokes, adapters, plus calls to services **outside the scanned packages**.
- **Safety:** values under keys that look like password, secret, token or credential are redacted.

## What the FSD contains

Introduction and glossary · system context diagram · capability summary · per capability: overview, trigger, inputs/outputs, **sequence diagram**, processing steps, **decision tables**, validations, **data mappings**, integrations used, **error and retry table**, **process flowchart**, notes · common services · data dictionary · integration catalog · error catalog · configuration and environment dependencies · non-functional characteristics seen in code · **open questions** · service inventory · coverage report.

Ground rules baked into the skill:

- **No invented behaviour.** Anything not in the code is marked `[TO CONFIRM: …]` and collected under Open Questions.
- **Traceability.** Every rule and mapping cites its source service.
- **No secrets** are copied into any output.

## Tips for best results

- **Provide what lives outside the packages** if you can: scheduler task export, global variables, endpoint/connection aliases, JMS/UM settings, Trading Networks rules. Missing items become Open Questions rather than guesses.
- **Large applications:** run one package or one capability at a time and let the plan file track progress.
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
| Mermaid diagram fails to render | Ask: *"Fix the Mermaid syntax in section X."* Common causes are unquoted labels with brackets and diagrams with too many nodes. |
| Chat runs out of context | Start a new chat and say *"Continue the FSD."* |

## Security notes

- The extractor only **reads** package files and writes Markdown/JSON; it makes no network calls.
- Copilot will run it in your terminal, so review `wm_extract.py` and get it approved per your organisation's policy before use.
- Secrets in adapter and connection nodes are redacted in the extract, but review `_fsd_work/` before sharing it.

## Customising

- Change the FSD layout in `references/fsd-template.md`.
- Add your organisation's naming conventions, glossary or mandatory sections to `SKILL.md`.
- Extend `INTEGRATION_PREFIXES` in `wm_extract.py` to flag your custom wrapper services as integrations.
