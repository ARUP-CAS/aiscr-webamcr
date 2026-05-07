# Governance by Assistant Product - Canonical Rule Map (aiscr-management hub)

**Purpose:** Map policy topics to the canonical shared rule sources under `.agents/canonical_configs/governance_rules/`, with the reminder that `.cursor/rules/*.mdc` is the full materialized reader for generated governance stems. Non-Cursor generated rule surfaces (`.claude/rules/*.md`, `.gemini/context/*.md`, `.github/instructions/*.instructions.md`, and generated sections in `CODEX.md`) are stub surfaces that route to the matching Cursor reader. This file is a lookup table only.

**Related:** Full vendor × asset matrix, official URLs, and vendor alignment live in `agent_tool_feature_matrix.md` and `mandatory_vendor_doc_urls.toml`.

The routing diagram below is a scanning aid only.

```mermaid
flowchart LR
  topic["Need governance for a topic"] --> table["Find the topic row in this table"]
  table --> stem["Open the canonical stem under .agents/canonical_configs/governance_rules/"]
  stem --> assistant{"Assistant in use?"}
  assistant -->|Cursor| cursor["AGENTS.md + .cursor/rules/<stem>.mdc"]
  assistant -->|Claude| claude["CLAUDE.md + .claude/rules/<stem>.md stub -> Cursor reader"]
  assistant -->|Codex| codex["CODEX.md generated stub -> Cursor reader"]
  assistant -->|Gemini| gemini["GEMINI.md + .gemini/context/<stem>.md stub -> Cursor reader"]
  assistant -->|Other| other["Tool entry doc + matching vendor surface"]
```

## Topic -> Canonical Rule Stem

| Topic | Canonical rule source | Scope |
| --- | --- | --- |
| Planning baseline before non-trivial work | `planning-baseline-upstream.md` | All agents |
| Planning-first execution model and re-plan triggers | `planning-core.md` | All agents |
| Usage-log lifecycle, required fields, close-out prompt | `usage-logging.md` | All agents |
| Model/runtime metadata in usage logs | `model-logging.md` | All agents |
| Agent work-style defaults and pre-presentation self-check Iron Law | `quality-first-execution.md` | All agents |
| Advisory model-setup / config sync reminder | `model-setup-reminder.md` | Advisory |
| Workspace boundary, sibling repos, config protection | `workspace-boundary-safety.md` | All agents |
| Management hub identity and canonical-source reminders | `mgmt-entry.md` | This repo |
| Management durable docs: dynamic sets and counts | `mgmt-doc-dynamic-sets.md` | This repo |
| Management operating basics: ideas, scripts, parity, hygiene | `mgmt-repo-operating-basics.md` | This repo |
| Management hook intents and ownership map | `hook-intents.md` | This repo |
| Ecosystem-wide shared rules (siblings; workflow alignment) | `aiscr-ecosystem-governance.md` | Ecosystem |
| Hub vs sibling workflow routing | `ecosystem-hub-workflow-routing.md` | Ecosystem |
| `port_workspace_safety_config.py` guidance | `port-workspace-safety-config.md` | Port/safety |

**Delivery surfaces:** For any stem above, `.cursor/rules/<stem>.mdc` is the full reader. Non-Cursor generated surfaces are valid stubs when they preserve the stop anchor, topic summary, and Cursor-reader link; follow that link when the rule text is load-bearing for the task.

**Entry-doc pointers (workspace boundary):** `CLAUDE.md`, `CODEX.md`, and `GEMINI.md` each include a short workspace-boundary pointer back to `AGENTS.md` and the relevant canonical rule when needed.

**Three-tier hub model**

| Tier | Meaning | Examples (this hub) |
| --- | --- | --- |
| **1 - Hub-root entry docs** | Committed at repo root; not under `local_configs`; not on `repos.toml` `sync` lists; apply/pull may copy hub root to sibling when the sync layer routes them | `GEMINI.md`, `.pr_agent.toml` |
| **2 - Synced repo-root vendor trees** | Baselined under `.agents/local_configs/<repo>/` for sibling repos; often gitignored on sibling workstations; hub root is the single source of truth for its own assistant trees | `.gemini/`, `.qodo/` |
| **3 - `AGENT_FOLDERS` assistant roots** | Full profile-based sync (rules, skills, agents, settings, ...) per `sync_policy.py` and `repos.toml` repo policy | `.cursor`, `.claude`, `.codex` |

**Repo-root and digest vendors - where governance loads**

| Vendor / product | Primary human entry | Rules / config surface | Notes |
| --- | --- | --- | --- |
| Gemini | `GEMINI.md` | `.gemini/` | Tier 1 + tier 2 |
| Qodo Merge | `.pr_agent.toml` | — | Tier 1 only for PR-agent config; `.qodo/` is tier 2 IDE baseline |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/instructions/*.instructions.md` | Digest-only entry |
| Cursor (incl. BugBot) | `AGENTS.md` | `.cursor/rules/`, `.cursor/BUGBOT.md` | No vendor `CURSOR.md` |

**Drift guard:** This table must list every active canonical governance stem that an entry doc or assistant wrapper is expected to open by topic. After adding, splitting, retiring, or renaming a rule stem, update this table and run the usual governance validation suite.

## Suggested Governance Load Order (Non-Cursor Tools)

1. `AGENTS.md`, `CONTRIBUTING.md`, `.agents/README_en.md`
2. Tool entry doc (`CLAUDE.md`, `CODEX.md`, `GEMINI.md`) and short hub pointers under `local_configs` where applicable
3. Topics in the table above: open the assistant-specific stub for orientation, then load the linked `.cursor/rules/<stem>.mdc` full reader when the task touches that rule's details

**Cursor:** primary project context is `AGENTS.md` plus `.cursor/rules/*.mdc`; use `.cursor/README_en.md` for assistant-specific routing.
