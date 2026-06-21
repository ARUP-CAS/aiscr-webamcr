# Documentation Hygiene Audit — Portable Prompt

This prompt can be used directly or via the **aiscr-doc-hygiene-audit** skill; the accompanying plan is `doc-hygiene-audit.plan.md` in `aiscr-management/.agents/plans/`.

Generated audit reports and suggested fixes must **not** include real secrets, PII, or production data; use placeholders where needed.

You are auditing the documentation and configuration files of a software repository
for **duplication, drift, and structural hygiene**. This prompt is platform-agnostic
and can be used on any codebase that uses instruction files for AI agents, contributors,
or tooling.

---

## Prerequisites (script-first flow)

Before running this audit with an agent, run these **deterministic scripts** (if available in the repo) and attach their output to the session so that C1 (file discovery) and C5 (cross-reference integrity) are reproducible and CI can run the same checks without an agent:

1. **Doc discovery** — e.g. `python .agents/scripts/doc_discovery.py --output json`  
   Produces a list of instruction-bearing files with line counts. Attach the JSON or text output.
2. **Link check** — e.g. `python .agents/scripts/link_check.py --output json`  
   Produces a list of broken same-repo links (file and section anchors). Attach the output; fix any broken refs before or during the audit. By default the link check covers governance docs, assistant trees (`.cursor/`, `.claude/`, `.codex/`, `.gemini/`), `.agents/**`, OpenSpec specs, and active OpenSpec change artifacts. Archived OpenSpec change artifacts under `openspec/changes/archive/` are **excluded from default scope** as historical records; pass an archive path explicitly to opt into ad-hoc checks (handled in C8 instead).

The agent should use the discovery output as the canonical file list for C1 and should treat link-check results as the baseline for C5. Remaining checks (C2–C4, C6–C8) remain agent-driven.

---

## HOW TO USE

1. Copy this file into any repository at `.agents/prompts/audit_doc_hygiene.md`
   (or wherever your agent prompts live).
2. **(Recommended)** Run the doc discovery and link-check scripts (see Prerequisites) and attach their output.
3. Open a new AI agent session and say:

   ```plain
   Read .agents/prompts/audit_doc_hygiene.md and run the audit.
   ```

4. The agent will produce a structured report with findings and fix suggestions.
5. Optionally pass `--fix` in your message to have the agent apply safe fixes directly.

---

## WHAT THIS AUDITS

The audit checks for eight categories of problems in documentation and config files.
Each check produces findings rated: **OK**, **WARN**, or **FAIL**.

### C1 — File Discovery

Locate all instruction-bearing files in the repository. Typical candidates:

- `README.md`, `README_en.md` (or other language variants)
- `CONTRIBUTING.md`
- `CLAUDE.md`, `AGENTS.md`, `CODEX.md`, `COPILOT.md`, `.cursorrules`
- `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`
- Any `AGENTS.md` in subdirectories (nested overrides)
- Agent prompt files (e.g. `.agents/prompts/*.md`)
- Agent config files (e.g. `.agents/config/*.yaml`, `.agents/config/*.json`)
- Auto-memory files (e.g. `MEMORY.md`, `.claude/memory/*.md`)
- **OpenSpec capability specs** under `openspec/specs/**/*.md` (durable requirement
  owners for migrated workflow domains)
- **OpenSpec active change artifacts** under `openspec/changes/<slug>/**/*.md`
  (proposal, design, tasks, delta specs — change-local context, not durable specs)
- **OpenSpec archived change artifacts** under `openspec/changes/archive/**/*.md`
  (historical records; treat as report-like assets for C8/C9, not current operating
  requirements)

`doc_discovery.py --output json` emits a `category` field per entry so OpenSpec
specs (`openspec_specs`), active changes (`openspec_active_changes`), and archived
changes (`openspec_archived_changes`) stay distinguishable from governance docs,
plans, prompts, references, reports, rules, and tool entry pointers.

**Action:** List every file found with its line count, classification category,
language, and apparent audience.

### C2 — Audience & Responsibility Mapping

For each file found in C1, determine:

1. **Primary audience** — who reads this file? (GitHub visitors, human developers,
   AI agents, specific tooling like Claude Code, review system, etc.)
2. **Responsibility** — what is this file's unique purpose? What information
   should ONLY live here?

**Check:** Does every file have a clear, distinct audience? If two files serve
the same audience with the same responsibility, flag as **FAIL — redundant file**.

### C3 — Content Duplication Detection

For each pair of files from C1, scan for duplicated content blocks. Focus on:

- Branch workflow rules / branch naming conventions
- Code style rules (formatters, linters, line length)
- Docstring / documentation style rules
- Testing commands and requirements
- Directory structure descriptions / key path tables
- "Do not" rules (migrations, generated files, security notes)
- Tech stack listings
- Pre-commit hook descriptions
- Generated artifact instructions
- Security notes (e.g. self-signed certs, secret management)

**Method:**

1. Extract key phrases (5+ words) from each file.
2. Search for those phrases across all other files.
3. For each match, classify as:
   - **Acceptable duplication** — self-contained README repeating essential info
     for external visitors (common and intentional).
   - **Redundant duplication** — same rule stated in two files that share an
     audience, or in a file that could use a cross-reference instead.
   - **Contradictory duplication** — same topic with different details in
     different files (this is **drift** — always FAIL).

**Output:** A duplication matrix showing which topics appear in which files,
with classification for each occurrence.

### C4 — Drift Detection

Specifically check for inconsistencies between files that should agree:

1. **Embedded config vs live config** — if a prompt file contains an inline
   YAML/JSON block that is supposed to represent a config file, compare the
   inline block against the actual file. Any difference is drift.

2. **Task/status definitions** — if task status is defined in multiple places
   (e.g. a config file AND a cache file), check that the definitions don't
   contradict each other.

3. **Path references** — if one file says `manage.py` is at the repo root
   and another says it's in `webclient/`, that's drift.

4. **Version numbers** — if a tech stack version (e.g. "Django 5.2") is
   mentioned in multiple files, check they all agree.

5. **Rule conflicts** — if one file says "do X" and another says "don't do X"
   on the same topic.

**Output:** List each drift instance with:

- The two conflicting files and line numbers
- What they say differently
- Which one is likely correct (based on proximity to the actual code/config)

### C5 — Cross-Reference Integrity

For every cross-reference (e.g. "see CONTRIBUTING.md §Testing"), verify:

1. The target file exists.
2. The referenced section exists in the target file.
3. The reference is not stale (the section wasn't renamed or removed).

**Output:** List broken or stale cross-references.

### C6 — Token Efficiency (AI-specific)

For files that are auto-injected into AI sessions (e.g. `CLAUDE.md`, `MEMORY.md`,
`.cursorrules`), evaluate token efficiency:

1. **Content that is also in other files the agent will read anyway** — redundant
   tokens. Calculate approximate token waste.
2. **Content that the agent rarely needs** — consider moving to a file that is
   read on-demand rather than auto-injected.
3. **Auto-memory files** — check if they contain only non-obvious information
   that isn't already in the auto-injected instruction files.

**Output:** Estimated token savings if redundancy is eliminated.

### C7 — Governance Rules Presence

Check whether the repository has explicit documentation governance rules
(i.e. a section that defines which file owns which information and prohibits
duplication). If absent, flag as **WARN** and suggest adding one.

If present, verify that the current file structure actually follows the
stated governance rules.

### C8 — Reports & Long-Lived Assets Cleanup

Look specifically at `.agents/reports/*.md` and other large, infrequently updated
instruction-style documents (e.g. long audit reports, automation summaries, usage logs).

For each such file:

1. **Classify lifecycle action** as one of:
   - **Keep** — current, referenced, governance-relevant, or still operational.
   - **Compress** — stale, heavy, superseded, or narrative-heavy, but still carrying durable decisions, conclusions, accountability, or links that need a compact maintained form before any stronger cleanup is considered.
   - **Remove** — no ongoing value after retained decisions and links have been preserved; removal still requires explicit approval and is index-first (see step 4).

2. **Estimate token footprint** — use line count from discovery (roughly 1–2 tokens per line for English Markdown) to approximate size and cost when the file is included in agent context.

3. **Assess** — high token cost + low ongoing value + elevated drift risk (e.g. old snapshot no longer maintained) = good cleanup candidate.

4. **Plan compression before destructive cleanup** — for every compress or
   remove recommendation, state the preserved source path, retained decisions
   or conclusions, omitted-detail category, and follow-up pointer. Apply the
   **index-first** pattern (see `.agents/reports/README_en.md` → *Report
   compression lifecycle*): the default outcome for a stale/superseded/obsolete
   report is to remove it and record it in
   `.agents/reports/historical-index.md` (date, original path, one-line scope),
   leaving the content recoverable from git history. Retain a report in place
   with a short status header *only* when it carries substantive load-bearing
   decisions or reference content. Do **not** recommend per-file stubs.

5. **Usage-log accountability** — old or heavy usage logs are in scope for
   compression, but the compressed record must preserve the required usage-log
   fields (`When`, `Agent / runtime`, `Model / backend`, `What`, `Impacted`,
   `Close-out`) and preserve or point to verification evidence when the
   original carried it. If a compressed usage-log summary remains under
   `.agents/reports/usage/`, it must stay compatible with usage-log validation;
   otherwise recommend a documented placement outside that validator's entry
   scope.

**Output:** A table of candidate files with path, size estimate (lines / ~tokens), lifecycle action (keep / compress / remove), compression mechanism (index-first removal vs retain-in-place status header), traceability fields, and suggested action. Add a short narrative on **expected token and maintenance savings** if recommended cleanups are executed.

### C9 — Prose Ownership Classification (hub extension)

This check applies to **management hub** runs (or any repo whose governance
spec at `openspec/specs/documentation-consistency/spec.md` requires it).
Other repos may skip C9 and rely on C3.

For each finding from C3 (duplication) and any prose block flagged in C4
(drift), classify the prose block on **two independent axes** before
recommending edits:

**Ownership class** (what the prose *means*):

- **`canonical`** — the single home that owns this rule, procedure, or fact.
- **`summary`** — a short pointer or orientation copy in another file that
  may remain because it serves a different audience.
- **`historical`** — retained for audit or migration context, but not
  current operating instruction.
- **`obsolete`** — superseded by a newer canonical home; should be removed
  or archived (with approval).

**Source** (where the durable edit target lives):

- **`hand-written`** — the file itself is the edit target.
- **`generated`** — the file is emitted by a generator script; the durable
  edit target is the generator or its canonical source. Generated files
  are NOT auto-fix candidates regardless of ownership class.

The two axes are orthogonal. A generated file can be `(canonical, generated)`
when the generator output is the public truth, `(summary, generated)` when
the file is a generated pointer (e.g. Claude rule stubs that point to
canonical Cursor rule bodies), or `(obsolete, generated)` when the
generator should stop running.

**Disambiguation:** for any duplicated rule found in C3, exactly one
occurrence SHALL be marked as the `canonical` owner. Secondary occurrences
are classified as `summary`, `historical`, or `obsolete`. Recommended fixes
SHALL replace redundant secondary prose with concise pointers when the
information must remain discoverable to that audience.

**OpenSpec classification rules:**

- Durable OpenSpec capability specs under `openspec/specs/` are usually the
  `canonical` owners for migrated workflow behaviour. Treat duplications
  between an OpenSpec spec and another hub doc as a flag to move the
  authority to the spec and turn the other surface into a `summary` pointer.
- Active OpenSpec change artifacts under `openspec/changes/<slug>/`
  (proposal, design, tasks, delta specs) are change-local context until
  archived or synced into main specs. Do NOT classify them as `canonical`
  for ongoing operating guidance and do NOT flatten them with main specs in
  the C3 duplication matrix; keep the proposal / design / task distinction.
- Archived OpenSpec change artifacts under `openspec/changes/archive/` are
  `historical` records by default. Do not promote them to `canonical` and
  do not recommend deleting them unless a later approved change explicitly
  retires them.

**Generated routing rule:** when `source = generated`, the recommendation
SHALL name the generator or canonical source as the edit target and SHALL
NOT propose hand-editing the emitted file. The ownership class is still
recorded so maintainers can distinguish a generated canonical surface from
a generated summary pointer.

**Output:** Extend the C3 duplication matrix with two extra columns
(`ownership_class`, `source`) for each occurrence. List any cases where the
classification is ambiguous so the maintainer can resolve them.

**Backlog coordination:** when C9 findings touch `.agents/reports/**` or
`.agents/canonical_configs/references/ai-session-learnings.md`, the audit
SHALL consult the active backlog (open `.agents/backlog-overview.md` and
`openspec/changes/` for current proposals) and identify any item that already
owns the cleanup. The audit then explicitly absorbs, sequences, or defers
those items rather than producing a parallel cleanup ritual. If a finding
overlaps with an active proposal, the report SHALL state which proposal owns
the cleanup and stop short of mutating the file unless the user explicitly
approves the in-pass edit. Do not name specific backlog slugs in this prompt
or in generated stubs; the backlog set is dynamic and lives in the registry.

**Session-learning cleanup:** when auditing
`.agents/canonical_configs/references/ai-session-learnings.md`, classify each
reviewed entry as **keep**, **merge**, **distribute**, or **retire** before
recommending edits. `distribute` means the durable lesson belongs in a narrower
contextual owner such as a governance rule, canonical reference, prompt, skill
source, script README, or report pointer. `retire` requires an explicit
rationale. The learnings file remains a compact index, not a dated session
journal.

---

## Report date and filename

Before writing the report, obtain the current date in ISO format (YYYY-MM-DD) by running a **deterministic command**, e.g.:

`python -c "import datetime; print(datetime.date.today().isoformat())"`

Use this value for the **Date** field in the report and for the report filename (e.g. `doc_hygiene_<date>.md`). Do **not** infer or guess the date (e.g. from context or memory).

---

## OUTPUT FORMAT

Produce the report in this structure:

```markdown
# Documentation Hygiene Audit Report

**Repository:** <name>
**Date:** <iso8601>
**Files audited:** <count>

## Summary

| Check | Status | Findings |
|-------|--------|----------|
| C1 File Discovery | OK/WARN/FAIL | <count> files found |
| C2 Audience Mapping | OK/WARN/FAIL | <count> issues |
| C3 Duplication | OK/WARN/FAIL | <count> redundant, <count> contradictory |
| C4 Drift | OK/WARN/FAIL | <count> drift instances |
| C5 Cross-References | OK/WARN/FAIL | <count> broken refs |
| C6 Token Efficiency | OK/WARN/FAIL | ~<count> tokens recoverable |
| C7 Governance | OK/WARN/FAIL | present/absent |
| C8 Reports & long-lived assets cleanup | OK/WARN/FAIL | <count> candidates, ~<count> tokens savings |
| C9 Prose ownership (hub) | OK/WARN/FAIL/SKIPPED | <count> findings classified |

## C1 — File Discovery
<details>

## C2 — Audience & Responsibility
<details>

...

## C8 — Reports & Long-Lived Assets Cleanup
<details>

| Path | Lines (~tokens) | Classification | Suggested action |
|------|-----------------|----------------|------------------|
| ... | ... | keep / compress / archive / remove | mechanism + traceability summary |

**Expected token and maintenance savings:** <short narrative>

</details>

## C9 — Prose Ownership Classification (hub extension)
<details>

| Topic / rule | File | Lines | ownership_class | source | Edit target |
|--------------|------|-------|-----------------|--------|-------------|
| ... | path/to/file.md | start-end | canonical / summary / historical / obsolete | hand-written / generated | <file or generator> |

**Ambiguous cases:** <list cases where the classification needs maintainer judgment>

**Session learnings:** <for `ai-session-learnings.md`, list keep / merge /
distribute / retire decisions and target contextual owners>

</details>

## Recommended Fixes

### Critical (FAIL)
1. <fix description> — **File:** `path` — **Action:** <specific edit>

### Important (WARN)
1. <fix description> — **File:** `path` — **Action:** <specific edit>

### Optional improvements
1. <fix description>
```

---

## FIX MODE

If the user requests fixes (e.g. "run the audit and fix"), apply the following
safe fixes automatically:

### Auto-fixable (apply without asking)

- Remove sections from AGENTS.md / CLAUDE.md that are exact duplicates of
  CONTRIBUTING.md content, replacing with a cross-reference.
- Remove embedded config blocks from prompt files when the live config file exists.
- Remove auto-memory entries that duplicate auto-injected instruction files.
- Fix path references that don't match the actual repo structure.
- Remove contradictory fields from config files (e.g. status fields that belong
  in a separate cache file).
- **Reports cleanup (low-risk only):** Update report headers with compression, protected, archived, or superseded notes (e.g. "Compressed — retained decisions summarized in X"); add cross-references to newer canonical docs; prune duplicate synthetic summaries that are fully covered elsewhere. For usage logs, preserve required compliance fields and verification pointers.

### Require confirmation

- Restructuring a file (moving sections between files).
- Deleting a file entirely (merging into another).
- Adding a governance section to CONTRIBUTING.md or equivalent.
- Modifying README files (they're user-facing, higher risk).
- **Reports:** Deleting or moving report files; collapsing multiple reports into one; any change that might impact incident history, usage-log accountability, or audit trail. **Incident/postmortem reports and formal governance reports are high-sensitivity** — never delete them automatically.

### Never auto-fix

- Changing rules or conventions (only the human decides what the rules are).
- Modifying generated files or build artifacts.
- Changing anything in migration files.
- **Deleting or archiving incident/postmortem reports or formal governance reports** — these require explicit human review.

---

## ADAPTATION NOTES

This prompt works across any repository structure. The specific file names
in C1 are suggestions — the agent should discover what actually exists. Common
variations:

| This prompt says | Your repo might use |
| ------------------ | --------------------- |
| `CLAUDE.md` | `.cursorrules`, `COPILOT.md`, `CODEX.md`, `.windsurfrules` |
| `AGENTS.md` | Root-level or nested agent instructions |
| `.agents/` | `.ai/`, `.codex/`, `.cursor/`, `ai_config/` |
| `CONTRIBUTING.md` | `DEVELOPMENT.md`, `HACKING.md`, `docs/contributing.rst` |
| `MEMORY.md` | Any auto-memory / context persistence file |

The audit logic is the same regardless of naming conventions.
