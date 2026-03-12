# Documentation Hygiene Audit — Portable Prompt

You are auditing the documentation and configuration files of a software repository
for **duplication, drift, and structural hygiene**. This prompt is platform-agnostic
and can be used on any codebase that uses instruction files for AI agents, contributors,
or tooling.

---

## HOW TO USE

1. Copy this file into any repository at `.agents/prompts/audit_doc_hygiene.md`
   (or wherever your agent prompts live).
2. Open a new AI agent session and say:

   ```plain
   Read .agents/prompts/audit_doc_hygiene.md and run the audit.
   ```

3. The agent will produce a structured report with findings and fix suggestions.
4. Optionally pass `--fix` in your message to have the agent apply safe fixes directly.

---

## WHAT THIS AUDITS

The audit checks for seven categories of problems in documentation and config files.
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

**Action:** List every file found with its line count, language, and apparent audience.

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

## C1 — File Discovery
<details>

## C2 — Audience & Responsibility
<details>

...

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

### Require confirmation

- Restructuring a file (moving sections between files).
- Deleting a file entirely (merging into another).
- Adding a governance section to CONTRIBUTING.md or equivalent.
- Modifying README files (they're user-facing, higher risk).

### Never auto-fix

- Changing rules or conventions (only the human decides what the rules are).
- Modifying generated files or build artifacts.
- Changing anything in migration files.

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
