# Review Update Agent — AMČR (aiscr-webamcr)

Incremental update follow-up to `review_codebase.md` (full T01–T11 audit).
Assumes the initial audit cycle is completed and all artifacts exist.

**PURPOSE:** Detect and document gaps, inconsistencies, drifts, and code
changes since the last review — without repeating the full audit.

---

## IMPORTANT RULES

1. **Output language:** All outputs MUST be in Czech (changelog, tables,
   bugs.md, refactoring_backlog.md). Same rule as `review_codebase.md`.
2. Before performing any other action, read `AGENTS.md` in the repository root.
3. **Datetime values** must be set from a verifiable source (git or Python),
   never guessed — same rule as `review_codebase.md` rule 4.
4. This prompt does NOT replace `review_codebase.md`. It produces a delta
   changelog entry in `final_audit.md` and refreshes existing artifacts. A
   full re-review requires the original prompt.
5. Do not modify `review_codebase.md` — it is maintained by human reviewers
   via the prompt evolution process.

---

## INITIALIZATION SEQUENCE

At the start of every update session, execute in this exact order:

1. Read `AGENTS.md` — repository-specific agent instructions take precedence.
2. Read `.agents/config/review_config.yaml` — load configuration.
3. Read `.agents/config/review_cache.json` — load progress state and file hashes.
4. Read `.agents/reports/bugs.md` — load known bugs.
5. Read `.agents/reports/refactoring_backlog.md` — load known backlog items.
6. Read `.agents/reports/review_reports/final_audit.md` — load the synthesis.
7. Proceed to Phase U01.

---

## PHASE U01 — CHANGE DETECTION

**Purpose:** Identify what changed in the repository since the last review.

### Steps

1. Run `review_tools.py hash` (optionally `status`) to detect changed and
   missing files. Use the output as the starting point for the table below.

2. Scan for **new files** not yet tracked in the cache:
   - New `*.py` files in `webclient/` (especially `models.py`, `views.py`,
     `forms.py`, `signals.py`, `managers.py`, `tasks.py`, `urls.py`).
   - New Dockerfiles or `docker-compose*.yml` files.
   - New scripts in `scripts/`.
   - New workflows in `.github/workflows/`.
   - New JS/SCSS files in `webclient/static/`.
   - New or modified templates in `webclient/templates/`.

3. Determine which tasks (T01–T10) are affected by the changes.

### Output

Record in the update report under `## U01 — Detekce změn`:

```markdown
### Změněné soubory

| Soubor | Task | Starý hash (prvních 12) | Nový hash (prvních 12) |
|--------|------|-------------------------|------------------------|
| ...    | T0X  | abc123...               | def456...              |

### Smazané soubory
- ...

### Nové soubory (nesledované)
- ...

### Dotčené tasky
- T0X: důvod (N souborů změněno / nové soubory v scope)
```

---

## PHASE U02 — COVERAGE AUDIT

**Purpose:** Find files, apps, or directories that were missed or insufficiently
covered by the initial review cycle.

### Steps

0. Run `.agents/scripts/review_tools.py coverage-gaps` and
   `review_tools.py repo-structure` to detect uncovered files and
   structural changes mechanically. Use the output as the starting point
   for the coverage audit below.

1. **Django apps vs T03 coverage:**
   - Review `[T03]` gaps from the `coverage-gaps` output — these are apps
     with `models.py` not found in `orm_analysis.json`.
   - Compare against T03 sub-task scopes in `review_cache.json` to
     identify which sub-tasks covered which apps.
   - For each uncovered app: check if it has `models.py` with actual models
     (not just empty or pass-through files).

2. **Frontend coverage (T07):**
   - Review `[T07]` gaps from the `coverage-gaps` output — these are
     custom JS files not in `frontend_analysis.json`.
   - Verify the vendored-vs-custom classification is correct.

3. **Scripts coverage (T10):**
   - Review `[T10]` gaps from the `coverage-gaps` output.
   - Config files (e.g. `crontab.txt`, `uwsgi_site.ini`) may appear as
     gaps; they are not analysed as scripts — verify they are documented
     in `scripts_analysis.json` → `config_notes` and tracked in
     `review_cache.json`. If so, they are not a coverage gap.

4. **Repository map freshness (T01):**
   - Review `repo-structure` output for new directories not in
     `repository_map.json`.
   - Flag new or removed directories.

### Output

Record under `## U02 — Audit pokrytí`:

```markdown
### Django apps bez ORM analýzy
| App | Má models.py | Počet modelů | Doporučení |
|-----|-------------|-------------|------------|

### Neanalyzované soubory
| Soubor | Měl být v tasku | Důvod vynechání |
|--------|----------------|-----------------|

### Mezery v pokrytí
- ...
```

### Resolving gaps

For each coverage gap found, decide:

- **Resolve in-session** if the gap is small (≤ `max_lines_per_task` from
  `review_config.yaml`): follow the COVERAGE GAP RESOLUTION workflow in
  `review_codebase.md` — create sub-tasks, analyse, write reports, update
  all artifacts and body sections.
- **Defer** if the gap is large or requires a full task re-run: document
  the gap in the changelog and recommend re-running the specific task
  using `review_codebase.md`. Do not leave it unresolved without a clear
  action item.

---

## PHASE U03 — CROSS-VALIDATION & CONSISTENCY

**Purpose:** Verify that all review artifacts are internally consistent.

### Automated checks

Run before manual review:

```
review_tools.py cross-validate   # orphan bugs, backlog prefixes, severity mismatches, cache paths
review_tools.py id-inventory     # orphan/duplicate IDs, SEC IDs missing from final_audit
review_tools.py lint-artifacts   # JSON validity, cache schema, bug entry completeness
```

Review script errors and warnings. Focus manual effort on:

- **Final audit accuracy** (script cannot check this): verify TOP 10 list
  references valid IDs, no Vysoka finding is missing, section content matches
  underlying task reports.
- For severity mismatches flagged by the script: if intentional, ensure
  the rationale is documented in the bug entry.

### Output

Record under `## U03 — Křížová validace`:

```markdown
### Osiřelé záznamy
| ID | Artifact | Chybí v |
|----|----------|---------|

### Nekonzistentní závažnosti
| ID | bugs.md | backlog | analysis JSON |
|----|---------|---------|---------------|

### ID problémy
- ...

### Final audit — nesrovnalosti
- ...
```

---

## PHASE U04 — SPOT-CHECK FINDINGS VALIDITY

**Purpose:** Verify that key reported findings still exist in the codebase.
This is NOT a full re-audit — it is a targeted spot-check of the most
important findings.

### Steps

1. **All Vysoka/Kriticka bugs** — for each bug in `bugs.md` with severity
   Vysoká or Kritická:
   - Read the referenced file and line.
   - Confirm the issue is still present.
   - If fixed: note as "opraveno" with the current content.

2. **Sample of Stredni bugs** — pick at least 3 bugs with severity Střední:
   - Read the referenced file and line.
   - Confirm or invalidate.

3. **Architectural findings:**
   - CIRC-01 (projekt ↔ oznameni): check the circular import still exists.
   - CIRC-02 (adb ↔ xml_generator): check the circular import still exists.
   - ARCH-01 (core bloat): verify core still has 77+ Python files.

4. **Fixed-but-not-updated check:**
   - For any bug found to be fixed in code: flag for removal or status
     update in `bugs.md`.

### Output

Record under `## U04 — Ověření nálezů`:

```markdown
### Ověřené bugy

| BUG ID | Závažnost | Stav | Poznámka |
|--------|-----------|------|----------|
| BUG-001 | Střední | ✓ stále přítomen | eval() na řádku 663 |
| BUG-010 | Vysoká  | ✗ opraven | fallback změněn na "False" |

### Architektonické nálezy
| ID | Stav | Poznámka |
|----|------|----------|
```

---

## PHASE U05 — PROMPT EVOLUTION INTEGRATION

**Purpose:** Assess which prompt evolution suggestions from T01–T10 have been
incorporated into `review_codebase.md` and which are still pending.

### Steps

0. Run `review_tools.py prompt-evolution` for a quick integration overview.

1. For each file in `.agents/prompts/prompt_evolution/T*_prompt_update.md`,
   classify each suggestion as: `začleněno` | `čeká na začlenění` |
   `zamítnuto` (conflicts with AGENTS.md) | `částečně začleněno`.

2. Produce a prioritized list of pending suggestions.

3. Also classify proposals from sub-task reports (e.g. T03c.md § 5)
   that may not have separate `prompt_evolution/` files.

### Who applies pending proposals

Agents must **not** self-modify `review_codebase.md` during an update
session (rule 5 of this prompt). The agent's responsibility is to:

- accurately classify each proposal,
- record the classification in the changelog, and
- provide a concrete, copy-pasteable diff or instruction so the human
  reviewer can apply changes quickly.

If the human explicitly asks the agent to apply pending proposals
(outside of a `review_update.md` session), the agent may do so.

### Output

Record under `## U05 — Prompt evolution`:

```markdown
### Stav návrhů

| Task | Návrh (zkrácený) | Stav | Priorita |
|------|-----------------|------|----------|
| T01  | Django project root note | začleněno | — |
| T03  | __init__ initial value pattern | čeká | Vysoká |

### Doporučení k začlenění
- ...
```

---

## PHASE U06 — ARTIFACT REFRESH

**Purpose:** Update all review artifacts with findings from U01–U05.

### Steps

1. **`review_cache.json`:**
   - Update `file_hashes` for all changed files detected in U01.
   - Update `last_updated` timestamp.
   - For tasks affected by changes: set status to indicate re-validation
     was performed (add a `last_validated` field if needed).

2. **Analysis JSONs:**
   - For any task affected by file changes (U01): update the relevant
     analysis JSON with delta findings.
   - Do NOT overwrite existing entries — append or update in place.

3. **`bugs.md`:**
   - Append new bugs found during U02–U04.
   - Update status of bugs confirmed as fixed in U04.
   - Follow the existing bug format and numbering.

4. **`refactoring_backlog.md`:**
   - Add new items if coverage gaps (U02) reveal significant issues.
   - Update priorities if the update review changes the assessment.

5. **`final_audit.md`:** Update in two passes:
   a) **Body sections (§1–§14):** For every new finding (bug, N+1 candidate,
      security issue, backlog item, architectural observation), update the
      relevant body section so it reflects the current consolidated state.
      Do not leave new findings only in the changelog.
   b) **Changelog:** Add a dated entry per the OUTPUT section template,
      summarising what changed and why.
   If the TOP 10 ranking changed, update section 12. If new items enter the
   refactoring plan, update section 13.

### Constraints

- Preserve all existing content — do not remove or overwrite.
- Follow the existing format and language (Czech).
- Cross-reference new bugs with GitHub Issues (same procedure as
  `review_codebase.md` BUG TRACKING section).

---

## OUTPUT

**Do NOT create a separate update report file.** All findings from U01–U06
are recorded directly in `final_audit.md` by updating it.

**Two-pass update rule:** When U06 updates `final_audit.md`:

1. **Body sections (§1–§14)** must be updated to reflect the current
   consolidated state of all findings. A reader of §1–§14 alone must get
   the complete picture without needing to read changelogs.
2. **Changelog (§ Changelog)** must receive a new dated entry summarising
   *what changed and when*. The changelog serves as the audit trail.

Template for a changelog entry:

```markdown
### <YYYY-MM-DD> — <stručný popis>

**Zdroj:** <typ review — inkrementální aktualizace / křížová validace / ...>

**Detekce změn:** <počet souborů změněno, smazáno, přidáno>.

**Opravené nekonzistence:**
- ...

**Mezery v pokrytí:**
- ...

**Ověření bugů:** <kolik potvrzeno / zneplatněno>.

**Nové nálezy:** <bugy, backlog položky, nebo "žádné">.

**Prompt evolution:** <stav začlenění>.
```

---

## TASK EXECUTION RULES

1. Always read `AGENTS.md` first.
2. Always load cache, bugs, backlog, and final audit before starting.
3. Phases U01–U06 must be executed in order — each builds on prior results.
4. Do not re-run the full T01–T11 audit. Focus on deltas and validation.
5. Use the Read tool to verify findings — do not rely on summaries or
   sub-agent output for spot-checks (same "done means done" principle as
   `review_codebase.md`).
6. If a phase reveals a problem large enough to warrant a full task re-run,
   note it in the report and recommend re-running the specific task using
   `review_codebase.md` — do not attempt it within this update session.
7. Respect task size limits from `review_config.yaml`.
8. Update all artifacts at the end (U06), not during earlier phases —
   collect findings first, write once.
9. After U06 is complete, run `review_tools.py all` to validate that the
   updated artifacts are consistent. Fix any errors before finishing.
