# Documentation Hygiene Audit Report

**Repository:** aiscr-webamcr (ARUP-CAS/aiscr-webamcr)  
**Date:** 2026-03-11  
**Files audited:** 18 instruction-bearing files

## Summary

| Check | Status | Findings |
|-------|--------|----------|
| C1 File Discovery | OK | 18 files found |
| C2 Audience Mapping | OK | 0 redundant files; clear ownership |
| C3 Duplication | OK | Acceptable duplication only; 0 contradictory |
| C4 Drift | OK | 0 drift instances (paths, versions consistent) |
| C5 Cross-References | OK | 0 broken refs; section refs exact (§ Generovaná dokumentace a artefakty, § Testování) |
| C6 Token Efficiency | OK | AGENTS.md trimmed per recommendation; ~100 tokens saved |
| C7 Governance | OK | Present (CONTRIBUTING.md § Správa dokumentace repozitáře) |

---

## C1 — File Discovery

| File | Lines | Language | Apparent audience |
|------|-------|----------|-------------------|
| `README.md` | 156 | CS | GitHub visitors |
| `README_en.md` | 154 | EN | GitHub visitors (EN) |
| `CONTRIBUTING.md` | 315 | CS | Developers, AI agents |
| `AGENTS.md` | 257 | EN | AI agents (all) |
| `CLAUDE.md` | 69 | EN | Claude Code / Cursor |
| `CODEOWNERS` | 45 | EN | GitHub (PR approval) |
| `.agents/README.md` | 41 | CS | Agents, developers (structure of .agents) |
| `.agents/prompts/audit_doc_hygiene.md` | 238 | EN | Any agent (portable audit prompt) |
| `.agents/prompts/review_codebase.md` | 771 | EN | Review agent sessions |
| `.agents/prompts/project_conventions.md` | 35 | CS/EN | Agents (short conventions) |
| `.agents/prompts/setup_dev.md` | 33 | CS | Agents, onboarding |
| `.agents/prompts/hooks_reference.md` | 35 | CS | Developers (local hooks config) |
| `.agents/config/review_config.yaml` | 238 | YAML | Review agent runtime |
| `.agents/config/review_cache.json` | 234 | JSON | Review agent state |
| `.agents/reports/automation_recommendations.md` | 138 | CS/EN | Team (MCP, hooks, skills) |
| `.agents/reports/review_reports/README.md` | 19 | — | Humans (report index) |
| `.agents/prompts/prompt_evolution/README.md` | 6 | — | Humans (prompt evolution) |

**Not present (and not required):** `MEMORY.md`, `.cursorrules`, `.github/PULL_REQUEST_TEMPLATE.md`, nested `AGENTS.md`.  
**CODEOWNERS** is at repo root (not `.github/CODEOWNERS`); both patterns are valid.

---

## C2 — Audience & Responsibility

Each file has a distinct audience and responsibility. CONTRIBUTING.md § Správa dokumentace repozitáře defines the mapping explicitly:

- **README.md / README_en.md** — GitHub visitors; overview, quick start (self-contained).
- **CONTRIBUTING.md** — Developers + agents; code conventions, branches, PR, testing, **canonical source** for these.
- **CLAUDE.md** — Claude Code; environment, commands, short reference; defers to AGENTS.md and CONTRIBUTING.md.
- **AGENTS.md** — AI agents; governance, behaviour, scope; defers coding details to CONTRIBUTING.md.
- **.agents/prompts/review_codebase.md** — Review agent; task registry and execution (loads config from YAML).
- **.agents/config/review_config.yaml** — Review runtime; task definitions, limits, tech stack (single source of truth).
- **.agents/config/review_cache.json** — Review state; task status, file hashes (no duplication of task definitions).

No two files share the same audience with the same responsibility. **OK.**

---

## C3 — Content Duplication Detection

| Topic | Files | Classification |
|-------|--------|-----------------|
| Django root `webclient/`, manage.py, requirements.txt | AGENTS.md, CLAUDE.md, project_conventions.md, README (structure), review_config.yaml, prompt_evolution | **Acceptable** — CLAUDE/AGENTS/project_conventions target agents; README self-contained; config is data. |
| Branch workflow: branch from `test`, PR to `test` | CONTRIBUTING.md, CLAUDE.md, AGENTS.md, README.md, project_conventions.md | **Acceptable** — CONTRIBUTING is canonical; others reference or minimal repeat for quick scan. |
| black (line 120), isort, flake8, pre-commit | CONTRIBUTING.md, CLAUDE.md, project_conventions.md | **Acceptable** — CONTRIBUTING canonical; CLAUDE/project_conventions are short references. |
| Docstrings: Czech, Sphinx, no Google-style | CONTRIBUTING.md, CLAUDE.md, project_conventions.md | **Acceptable** — same as above. |
| Do not edit migrations / generated docs / cert note | AGENTS.md, CLAUDE.md, CONTRIBUTING.md, project_conventions.md | **Acceptable** — critical “do not” rules; cross-refs used where possible. |
| Generated artifacts & pre-commit | CLAUDE.md (cross-ref to CONTRIBUTING §Generovaná dokumentace and §Testování), CONTRIBUTING | **Acceptable** — CLAUDE points to CONTRIBUTING. |
| Secrets / sensitive paths (local_settings, secrets*.json, webclient_env_var.sh) | AGENTS.md, hooks_reference.md, setup_dev.md, CONTRIBUTING | **Acceptable** — AGENTS and hooks_reference own the rule; others point or list for checklist. |
| Tech stack (Django 5.2, Celery, Redis, etc.) | repository_map.json, review_config.yaml, README, README_en, automation_recommendations.md | **Acceptable** — READMEs self-contained; config/analysis are data; report is descriptive. |

**Redundant duplication:** None that violates “one canonical source + cross-references.”  
**Contradictory duplication:** None. Paths (e.g. `webclient/` as Django root) and versions (Django 5.2) are consistent.

---

## C4 — Drift Detection

- **Embedded config vs live config:** No inline YAML/JSON in prompt files that duplicates `review_config.yaml`; prompts reference the file. **No drift.**
- **Task/status definitions:** Task list lives in `review_config.yaml`; status in `review_cache.json`. No conflicting definitions. **No drift.**
- **Path references:** All instruction files state that `manage.py` and `requirements.txt` are in `webclient/`, not repo root. **Consistent.**
- **Version numbers:** Django 5.2 in README, README_en, repository_map.json, review_config.yaml, automation_recommendations.md. **Consistent.**
- **Rule conflicts:** No “do X” vs “don’t do X” between files.

**Drift instances:** 0.

---

## C5 — Cross-Reference Integrity

| Reference | Source | Target | Result |
|-----------|--------|--------|--------|
| [AGENTS.md](AGENTS.md) | CLAUDE.md, CONTRIBUTING.md, .agents/README.md, setup_dev.md, etc. | `AGENTS.md` | Exists |
| [CLAUDE.md](CLAUDE.md) | AGENTS.md | `CLAUDE.md` | Exists |
| [CONTRIBUTING.md](CONTRIBUTING.md) | AGENTS.md, CLAUDE.md, README.md, README_en.md, .agents/README.md, project_conventions.md, setup_dev.md | `CONTRIBUTING.md` | Exists |
| [.agents/README.md](.agents/README.md) | AGENTS.md, CLAUDE.md, review_codebase.md | `.agents/README.md` | Exists |
| CONTRIBUTING.md §Generovaná dokumentace and §Testování | CLAUDE.md | Sections “Generovaná dokumentace a artefakty”, “Testování” | **OK** — CLAUDE.md updated to exact headings: § Generovaná dokumentace a artefakty, § Testování. |
| CONTRIBUTING.md § Správa dokumentace repozitáře | .agents/README.md | Section “Správa dokumentace repozitáře” | Exists |
| [.agents/prompts/hooks_reference.md](.agents/prompts/hooks_reference.md) | AGENTS.md | File exists | Exists |
| [.agents/prompts/setup_dev.md](.agents/prompts/setup_dev.md) | CLAUDE.md | File exists | Exists |
| [.agents/prompts/project_conventions.md](.agents/prompts/project_conventions.md) | AGENTS.md, setup_dev.md | File exists | Exists |
| [automation_recommendations.md](.agents/reports/automation_recommendations.md) | hooks_reference.md | File exists | Exists |
| `review_config.yaml` → tasks, vendored_exclusions, etc. | review_codebase.md | `.agents/config/review_config.yaml` | Exists |

**Broken or stale cross-references:** 0.

---

## C6 — Token Efficiency (AI-specific)

Files likely auto-injected into AI sessions: **AGENTS.md**, **CLAUDE.md** (and possibly workspace rules pointing at them).

- **Content also present where the agent is directed to read anyway:**  
  - Branch workflow, “Key Paths” table, “Do Not” list, and formatting rules in CLAUDE.md overlap with CONTRIBUTING.md and AGENTS.md. CLAUDE is already a short summary with cross-refs; the overlap is intentional for quick reference.  
  - AGENTS.md repeats high-level scope (e.g. “Django project root is webclient/”) that also appears in CLAUDE and project_conventions; again, small and by design for agents that read AGENTS first.

- **Estimated token savings:**  
  - If CLAUDE.md were reduced to pure pointers (no Key Paths table, no Do Not list, no formatting line): ~300–500 tokens saved per session, at the cost of losing the quick-reference role.  
  - ~~If AGENTS.md removed the 2–3 sentences that duplicate CONTRIBUTING/CLAUDE (e.g. “manage.py and requirements.txt live in webclient/”): ~100–200 tokens.~~ **Done:** AGENTS.md now points to CLAUDE.md for project root and key paths (~100 tokens saved).  
  - **Total recoverable:** ~500–800 tokens if redundancy were removed; current design favours self-contained quick reference over minimal tokens.

- **Auto-memory:** No MEMORY.md or similar in repo. N/A.

**Recommendation (optional):** Keep current structure; document in governance that CLAUDE.md and AGENTS.md are allowed to repeat minimal “critical reminder” content for agents that may not load CONTRIBUTING in the same session. ~~If token budget becomes an issue, replace duplicated sentences in AGENTS.md with a single pointer to CLAUDE.md for “Django root and key paths”.~~ **Applied:** AGENTS.md now points to CLAUDE.md for project root and key paths; ~100 tokens saved per session.

---

## C7 — Governance Rules Presence

**Present.** CONTRIBUTING.md § **Správa dokumentace repozitáře** defines:

- One target audience and one responsibility per file (table).
- Rules: do not repeat rules (use cross-references); one canonical source per information type; READMEs may be self-contained; keep README.md and README_en.md in sync; when changing a rule, update canonical source and check references.

Current file layout and cross-referencing align with these rules. **OK.**

---

## Recommended Fixes

### Critical (FAIL)

None.

### Important (WARN) — applied 2026-03-11

1. ~~**Token efficiency (optional)**~~ **APPLIED** — **Files:** `AGENTS.md`, `CLAUDE.md` — **Action taken:** In AGENTS.md replaced the sentence “Django project root is `webclient/` — `manage.py` and `requirements.txt` live there, **not** in the repo root” with “Django project root is `webclient/` (see [CLAUDE.md](CLAUDE.md) for key paths and environment).” CLAUDE.md remains the single place for key paths and environment details.

### Optional improvements — applied 2026-03-11

1. ~~**§ section references**~~ **APPLIED** — **File:** `CLAUDE.md` — **Action taken:** Updated “§Generovaná dokumentace” to “§ Generovaná dokumentace a artefakty” and “§ Testování” for exact CONTRIBUTING.md heading match.

### Optional improvements — not applied

2. **PULL_REQUEST_TEMPLATE** — **Path:** `.github/` — **Action:** If the team wants PR template support, add `.github/PULL_REQUEST_TEMPLATE.md` and reference it from CONTRIBUTING.md. Not required by this audit.
3. **CODEOWNERS location** — Repo uses root `CODEOWNERS`; GitHub also supports `.github/CODEOWNERS`. No change needed; document in README or CONTRIBUTING if you want to state the choice explicitly.

---

## Applied fixes summary

| Date | File(s) | Change |
|------|---------|--------|
| 2026-03-11 | AGENTS.md | Repository Overview: replaced duplicate “manage.py and requirements.txt” sentence with pointer to CLAUDE.md for key paths and environment. |
| 2026-03-11 | CLAUDE.md | Generated Artifacts: section refs updated to exact headings “§ Generovaná dokumentace a artefakty” and “§ Testování”. |

---

*Audit performed per `.agents/prompts/audit_doc_hygiene.md`. Fixes applied 2026-03-11.*
