---
name: aiscr-review-translations
description: Use when the user asks to review translations in a pull request, release,
  or scoped change. Apply repository terminology, prepare the reviewed ledger, preserve
  unrelated entries on approved writes, and report coverage.
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-review-translations -->
<!-- delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.agents/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-translations — review scoped translation changes

Supplement translations for a PR, correct named texts or review changes before release.
Start with affected keys and callers; unchanged wording needs another language review only when its meaning, caller or applicable authority changes.
Full-catalogue review is an explicit mode.
Every proposed text is recorded and approved before application.
A rename or a proven-dead key is removed within the same approved record.

**When to use vs alternatives:** use for translation additions/corrections and scoped release review.
Codebase review and release notes have their own workflows.
Key migration, sentence consolidation, running-release exports and vocabulary ports are separate, optional operations.

## Phase awareness

This operational skill executes an approved translation revision without requiring an OpenSpec change in the subject.
Planning artifacts do not approve execution or individual texts.
Adding a reusable shared adapter or changing this workflow's contract is governance maintenance above the scoped run; using established project tools for another format is ordinary scoped execution.

Resolve the subject, scope and branch first.
Operator approval of wording remains required even when execution itself was approved.
Never create an OpenSpec change or enroll a repository as a side effect.

## Context to load first

1. The subject's `AGENTS.md`, translation configuration/style guidance, catalogues and affected callers.
   Discover existing configuration before considering a declaration.
2. *(non-file)* Applicable terminology evidence for the selected terms.
   In-repo evidence must be local or operator-supplied and must not depend on access to any other repository.
3. The portable entry point `.agents/scripts/translation_revision_portable.py` (run its help); `.agents/canonical_configs/templates/translation-revision.toml` is an optional shape for repository facts, not a required file to install.

## Steps

### Context and boundaries

The **scope** records mode, languages/catalogues, keys, removals, affected paths/callers and comparison baseline where applicable.
An **authority** supplies established domain wording; a **follower** uses that wording in a compatible context.
The **ledger** records old and proposed texts by language, batch, reason and pre-write values, and the approved removals.

Scope is independent of execution tier.
In-repo execution requires an enrolled standard tree — the delivered `.agents/` skill tree — and uses the portable toolkit.
A subject without the standard tree has no in-repo execution; this workflow does not create that tree.
No run requires a venv, a new declaration or a new native validation pipeline.

<!-- aiscr:ecosystem-only -->
Hub-cockpit execution follows the route precedence owned by `ecosystem/agent-config-distribution` and uses confirmed subject branches; a subject without the standard tree is hub-cockpit only.
<!-- aiscr:ecosystem-end -->

Use `<WORK_DIR>` — `.venv/.cache/translation-revision/<run>/` — for drafts and context JSON; it is bulk and disposable, and placement classification is owned by `workflow/artefact-placement`.
Deliver the approved ledger, review tables and handover as subject-owned run output under `.agents/reports/translation-revision/` where the standard tree exists.

### 1. Establish affected scope and repository context

- Default to **targeted** review: named keys/paths or a PR base/head comparison.
  Resolve paths to affected keys by inspecting their callers.
  **Pre-release** selects changes since a named release or approved commit.
  **Full** language review requires an explicit request; neither a full inventory nor hub tooling implies that request.
- Include new/changed texts, newly missing translations, renamed-away keys and unchanged keys whose callers change meaning, rendering or supplied values.
  Record inspected caller paths/lines and keys.
  An unresolved comparison baseline stops comparison; obtain a baseline or an explicit replacement scope, never fall back to full review.
- Establish language set, format, key/style conventions, placeholder/plural mechanisms, applicable authority and available check coverage from repository evidence.
  The run context can carry these facts; the optional declaration is unnecessary when project configuration already supplies them.
- Preserve unrelated user edits and distinguish them from proposed workflow wording.
  Record pre-write values separately from the named committed comparison baseline.
  Cheap full-catalogue parsing does not require reviewing all wording.

### 2. Inspect affected callers, wording and term evidence

- Read affected callers even when the text did not change.
  Classify texts by actual use; key-pattern, punctuation and capitalisation heuristics remain review signals until their language/style preconditions and caller classification are established.
- Resolve the applicable authority before proposing domain wording.
  A domain's terms remain bound to that domain's own authority; read related entries as evidence without adding them to approved write scope.

<!-- aiscr:ecosystem-only -->
For AMČR, the binding authority is the AMČR web catalogue and help glossary.
<!-- aiscr:ecosystem-end -->

- Correctness outranks frequency.
  Record contextual exceptions with their evidence.
  Missing authority evidence must be visible before approval; never invent the rendering.
- Check the whole revised text for spelling, meaning, applicable rules, placeholders, markup and links in every selected language.
  Record defects that cannot be resolved.
  Length limits are repository-owned review signals, never automatic shortening rules.

### 3. Prepare the scoped ledger and review

For supported PO/ngx JSON, supply a context JSON containing `format`, `catalogues` and either inline `proposed_texts` (`{language: {key: text}}`) or optional `proposed` paths by language, `mode` (default `targeted`), `keys`, `removals`, `paths`, `changed_callers`, and applicable `authority`/`conventions`.
Comparison adds a **resolved** `baseline` (a PR `baseRefOid` or a named tag, never a local branch tip), `head`, `comparison: true` and materialised `baseline_catalogues`; pre-release requires the baseline.
Keep these materialisations in `<WORK_DIR>`.

Run from the subject root with its available Python runtime:

```bash
python .agents/scripts/translation_revision_portable.py --context <context.json> --work-dir <WORK_DIR> prepare
```

- Proposed files are drafts in `<WORK_DIR>`, never the subject catalogues.
  Inline `proposed_texts` prepares a record without any proposed file.
  A proposed file takes precedence only for its language; other languages retain inline proposals or their pre-write values.
  Prepare produces `ledger.json` and `review.md` with only scoped keys.
  Fill concrete batch/reason and authority/context evidence before presenting the record.
- A rename or a proven-dead key is a **removal**, listed separately under `removals` with a `reason` and the `unused`-evidence that established no remaining caller emits the id.
  A removal whose key is absent from the snapshot, or that lacks either field, is refused at preparation or write.
  A rename is an added key plus a removal of the old key in one record.
  Explicit removals stay outside text scope in every review mode, including full and comparison-derived scope; caller and diff selection cannot turn them back into missing-text findings during post-write verification.
- For an applied record rebuild, use `prepare --previous <ledger.json>`; original texts remain recorded and the current pre-write snapshot remains distinct.
  Existing dirty differences do not become approved merely because they were discovered.
- For an unfamiliar format, a suitable existing project parser can supply normalised `texts`, `proposed_texts` and `baseline_texts` by language for portable record preparation.
  Inspect its real format and preservation behaviour.
  Without a verified writer, prepare wording and hand over application; do not add a hub adapter merely to complete this run.
- Give the independent `aiscr-verify` reader the scoped record, affected context and authority evidence for the term pass.
  Resolve its findings before operator text review.
- Present the old/proposed tables and explicit limits.
  Obtain approval of every text and any separately proposed source/structural edit — including each removal — before application.
  Revised wording invalidates its earlier text approval.

### 4. Apply only approved changes

Confirm the subject branch before its first write.
For each supported catalogue use:

```bash
python .agents/scripts/translation_revision_portable.py --context <context.json> --work-dir <WORK_DIR> write --target <catalogue> --language <language> --approve
```

- Pass `--approve` only after approval of the exact ledger.
  The writer rejects targets or keys outside that record, conflicting edits since the snapshot, unsupported placeholder grammar (including positional width/precision and compound fields), ambiguous dotted JSON paths and failed byte-for-byte round-trips.
  A removal deletes the entry (it is not obsoleted) in every recorded language; an already-absent key is a no-op.
- Preserve unrelated values, metadata, order, PO wrapping, JSON indentation and line endings.
  Supported JSON needs only Python's standard library; PO needs an already available `polib` dependency.
  Missing dependencies are reported, never installed silently.
  Changed PO plurals need an established plural-aware writer and separate preservation evidence; unchanged plurals remain intact.
- A verified native writer may apply other formats after the same scope/approval and preservation checks.
  Its existence alone does not establish preservation.
  Inspect the exact diff and refuse unexplained churn.
- Keep keys that remaining callers emit, including bare or obsolete entries.
  New keys follow the repository's existing convention and lookup/extraction mechanism.
  Use its safe interpolation/plural formatter, retaining displayed values on missing translations and avoiding failures on mismatched placeholders.
- Consolidate affected broken sentences only when necessary or explicitly approved: one key with named values lets translators control word order.
  Lists may keep labelled fragments.
  Prove removed keys unused and record each as a removal.
  Routine work does not migrate unrelated keys or replace a working native formatter with another stack's helper.

### 5. Verify with explicit coverage and hand over gaps

Run the portable `verify` operation with the same context/work directory.
Inspect the post-write diff against the approved record.
Its report separates approved-text comparison, catalogue integrity, source integration, build and rendering, each with scope, method and `passed`/`failed`/`unverified` outcomes.

- The approved-text layer compares the selected values with the scoped ledger, retaining recorded keys even if their values revert to the comparison baseline.
  Missing or different approved texts fail verification; unavailable scoped approval evidence remains unverified.
  Each approved removal must be **absent from every recorded language**; a key that survives its removal fails the catalogue layer.
- Check affected entries for completeness/fuzzy state in each language, supported placeholder parity, markup/link compatibility, caller parameters, resolving references, parsing/compilation and approved-diff preservation.
- Supply inspected source evidence under `evidence`: `sites` with key/params, `source_reviewed`, `source_method`, `source_keys` and explicit `source_limits`.
  Unfamiliar syntax, dynamic references and unsupported placeholder grammars remain unverified until a suitable established check covers them.
- Discover relevant existing native checks and inspect their actual coverage before relying on them.
  Record `native_checks` with method, coverage and status.
  A build can establish build success without proving completeness, caller compatibility or layout.
  Do not provision a new pipeline as a prerequisite to wording review.
- Separate proven old out-of-scope defects from scoped results; change-caused regressions and in-scope failures block a clean result.
  Unavailable checks remain unverified rather than failed or passed.
  Exit zero for a portable operation does not mean fully verified.
- Approved text work can be reported as applied with limits.
  Claim full verification or release readiness only when relevant coverage is established.
  Keep unrun extraction, migrations, compilation, tests, build and rendering distinct in the local handover.
  For issue-linked work prepare that handover in issue text; posting has its own gate.

<!-- aiscr:ecosystem-only -->
Where a key migration follows AMČR terminology, derive field labels from entity-prefixed field paths, split shared labels per field, use entity identifiers for entity titles and English camelCase for other keys.
<!-- aiscr:ecosystem-end -->

An enrolled run requesting unavailable specialised tooling records that limit and hands over the operation; it does not follow an undeclared hub path.

### Execution using subagents

**Posture: registers `verification`, declines `drafting` and `survey`.**

- **Registers `verification`** for the independent scoped authority/term pass, with `aiscr-verify`; supply the record and evidence, receive adjudicated findings.
- **Declines `drafting`** because the operator owns the wording decision; grounds expire if a separately owned draft product is introduced.
- **Declines `survey`** because the caller must inspect the small affected context and toolkit results; grounds expire if independent source acquisition becomes necessary.

Admission and declared return contracts belong to `aiscr-quality-first-execution`.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER WRITE AN UNAPPROVED TEXT OR INVENT AN AUTHORITY RENDERING.`

No exceptions.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "Inventory read everything, so review everything" | Keep affected scope; full language review needs an explicit request. |
| "The baseline is missing, use the whole catalogue" | Resolve the baseline or obtain explicit replacement scope. |
| "Every repository uses the same domain rules" | Establish applicable domain, languages and conventions. |
| "The build passed, translations are verified" | Record demonstrated coverage and leave uncovered checks unverified. |
| "The operator can approve after I write" | Present the ledger and obtain text approval first. |
| "The native writer exists, formatting is safe" | Establish preservation and inspect the exact diff. |
| "The old key will be cleaned up by makemessages" | Record the removal (reason + unused-evidence) and delete it in-run. |
| "The local base branch is the baseline" | Resolve the baseline to a PR `baseRefOid` or tag and read it through the surface. |
| "I'll write the result with my file tools" | Deliver through a sanctioned write route — the digest-bound write surface, or a native write where the runtime records a grant. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Scope/baseline, languages, authority and affected caller context are recorded.
- [ ] Every applied text and source edit received approval on the confirmed branch.
- [ ] Every removal carries a reason and unused-evidence and is absent in every recorded language.
- [ ] Writes preserve unrelated user edits and repository formatting.
- [ ] Relevant checks carry scope/method/outcome; failures and unavailable checks are distinct.
- [ ] Handover states remaining gaps without a claim of unsupported release readiness.
- [ ] A subject without the standard tree received no new tree.

<!-- aiscr:ecosystem-only -->

- [ ] Hub-cockpit delivery went through the sibling surface, on the confirmed branch.

<!-- aiscr:ecosystem-end -->

<!-- aiscr:endgen -->

## Governance

<!-- aiscr:ecosystem-only -->
Execution tiers, sibling writes and untrusted-material handling are governed by `aiscr-ecosystem-governance`.
<!-- aiscr:ecosystem-end -->
Finding admission belongs to `aiscr-review-conduct`.
These obligations do not alter selected scope.

## Valid next steps

- Review the next affected change set with its own scope and approved ledger.
- Complete handed-over native checks in the subject's established environment.
- Read `.agents/canonical_workflows_context.md` and its **Usage** section before another workflow.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/translation_revision_portable.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/translation/__init__.py`
- `.agents/scripts/lib/translation/checks.py`
- `.agents/scripts/lib/translation/ledger.py`
- `.agents/scripts/lib/translation/ngx_catalogue.py`
- `.agents/scripts/lib/translation/po_catalogue.py`
- `.agents/canonical_configs/templates/translation-revision.toml`
