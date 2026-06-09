---
name: aiscr-plan-from-idea
description: Promote one OpenSpec backlog proposal into the governance-driven planning
  flow by running a governed structured exploration pass before the formal planning
  phase, then produce OpenSpec artifacts (proposal, specs, design, tasks), refresh
  backlog overview, and hard-stop before implementation unless the user explicitly
  starts a separate apply/implementation workflow afterward.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plan-from-idea.md -->

# aiscr-plan-from-idea

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Turn one specific OpenSpec backlog proposal into a formal AIS CR planning flow
that promotes it into a governance-driven OpenSpec change using concrete CLI
commands, keeps the repo's planning-first approval gate, and stops once the
full OpenSpec change is ready for implementation.

**Workflow boundary (read first):** In scope — a governed structured
exploration pass, the formal planning conversation, human approval, promotion
of the same slug to governance-driven `proposal.md` / `specs/` / `design.md` /
`tasks.md`, `openspec status`, and `generate_backlog_overview.py`. Out of
scope for this skill - implementing `tasks.md`, editing application or
non-change product files, running `/opsx:apply` / `openspec-apply-change`, or
continuing "because the change is ready." Those require an **explicit** separate
user request or a different workflow after this skill ends. Earlier approval
for planning or promotion does not carry forward to that later boundary.

## Phase awareness

This skill operates at the **explore/plan boundary** of the OpenSpec lifecycle.
It creates or promotes OpenSpec change artifacts with AIS CR governance gates.
It begins with a governed structured exploration pass that clarifies problem
framing, likely impacts, trade-offs, open questions, and readiness signals
before the formal planning phase.
After completing its workflow, it hands off to `/opsx:*` CLI seeds for execution.
It must not initiate implementation or cross into the apply phase.
Crossing the later `plan -> implement` boundary requires fresh
post-promotion approval specific to the promoted change; earlier approval for
planning or promotion does not carry forward.
Check for an existing OpenSpec change for this slug before promoting a new one.

## Bundled user message — red flag (conversational compression)

If the **same user message** mixes promotion or planning with **implementation**, wiring,
bootstrap, port tooling, or apply-style asks (for example: promote this *and* update
`.agents/scripts`, *and* run the port, *and* start `tasks.md`), treat that as **ambiguous
approval**:

- Complete **only** what this skill owns (exploration, planning, approval, promotion,
  backlog refresh).
- **Do not** treat the bundle as authorization to implement or mutate product or hub
  code in this run.
- A single “OK” does **not** satisfy the **Plan → Implement** boundary. Crossing that
  boundary requires **post-promotion** approval specific to implementation — see
  [§1.5 Iron Law](.agents/canonical_configs/governance_rules/aiscr-planning-core.md)
  (`NEVER TREAT ARTIFACT COMPLETION AS IMPLICIT APPROVAL TO IMPLEMENT`).

**Required behaviour:** finish promotion steps only, then **stop** and emit the
**completion handoff** block below. Ask the user for a **separate** message that
explicitly requests `/opsx:apply <slug>` or another apply workflow **after** promotion
(post-promotion approval).

## Completion handoff (mandatory)

When this skill finishes successfully, end with a short **handoff** so the thread cannot
be read as “everything in one bundle was approved”:

1. **Completed:** slug promoted; governance-driven artifacts exist; backlog refreshed as needed.
2. **Not authorized in this run:** executing `tasks.md`, apply scripts, or unrelated
   implementation — unless the user sends a **clear, separate** post-promotion instruction.
3. **Next step:** user sends a **new message** with `/opsx:apply <slug>` or
   `/opsx:continue <slug>` when ready.

Copyable template:

```text
**Completed:** OpenSpec change `<slug>` promoted; artifacts handed off for implementation planning.
**Not authorized in this run:** Implementation / apply (requires separate post-promotion approval).
**Next:** Send a new message: `/opsx:apply <slug>` or `/opsx:continue <slug>` when ready.
```

## Context to load first

1. `AGENTS.md`
2. `.agents/README_en.md`
3. `openspec/specs/openspec-requirement-governance/spec.md`
4. `.agents/canonical_configs/governance_rules/planning-core.md`

## Using the idea file structure

Read `openspec/changes/<slug>/proposal.md` first. Its header block seeds the
planning pass:

- **Title:** use it as the working title for the planning conversation.
- **Scope:** maps directly to Impacts (hub-only vs siblings vs external); name repos explicitly when `sibling:...` or `hub+siblings`.
- **Primary artefacts:** treat them as the initial path list; extend only after analysis shows missing dependencies.
- **Status:** if `partially addressed`, favour Defer or Reconsider unless the user confirms what remains.
- **Priority:** use it as a human ordering hint, not as an automatic mandate.
- **Expected size:** use it as an initial effort signal; confirm or revise it in the plan when analysis shows otherwise.
- **Before / After:** treat them as sequencing hints only. You may inspect the
  directly related backlog proposal when that extra context is genuinely needed.

Legacy backlog proposals without a full header block are still valid: infer only
what is needed for the current planning pass and flag uncertainty explicitly.

## Steps

1. Ask the user which backlog slug to use when it is not already clear.
2. Read `openspec/changes/<slug>/proposal.md` and the change metadata first.
   If needed for effective planning, you may also inspect directly related
   backlog proposals named in `Before` / `After` or explicitly named by the
   user. Do not drift into unrelated backlog browsing.
3. Run one governed structured exploration pass after reading the backlog
   proposal and before entering the formal planning phase. The pass must:

   - clarify the problem framing and intended outcome
   - surface likely impacted files, rules, and dependencies
   - capture trade-offs, risks, and open questions
   - record readiness signals that help decide whether the promoted change
     should hand off to `/opsx:continue <slug>` or `/opsx:apply <slug>`

   The generated `openspec-explore` / `/opsx:explore` surfaces may inform this
   thinking, but they remain reference-only generated stances. This governed
   exploration pass is owned by `aiscr-plan-from-idea`.

4. Enter one planning phase using that backlog proposal and the structured
   exploration output as the seed. The plan must include:

   - **Goals and steps** - what will be done and how.
   - **SWOT** - minimal SWOT is required, per `planning-core.md`.
   - **Impacts** - files and directories touched, repos affected, dependencies, and risks.
   - **Evaluation and recommendation** - either Recommend to proceed, Defer, or Reconsider scope/approach.
   - **Artifact mapping** - make it clear how the approved plan will become
     `proposal.md`, `specs/`, `design.md`, and `tasks.md` in the
     governance-driven flow. The plan's analysis and proposed changes are
     design input for the OpenSpec change — they feed into `design.md` and
     `tasks.md` during promotion.

   Plan todos must cover only plan-from-idea workflow steps (promotion,
   verification, backlog refresh). Implementation steps belong exclusively
   in `tasks.md` inside the OpenSpec change, not in planning-phase todos.

5. Present the plan with the recommendation to the user and wait for explicit
   approval before creating or regenerating any governance-driven artifacts.
6. After approval, promote the backlog item into the governance-driven flow
   under the same slug using the following CLI sequence:

   ```bash
   # 1. Detect current schema
   npx openspec status --change "<slug>" --json

   # 2. If schema is "backlog", switch .openspec.yaml to governance-driven
   #    (edit schema field or recreate under the same slug)

   # 3. Get per-artifact authoring guidance
   npx openspec instructions proposal --change "<slug>" --json
   # Write proposal.md in governance-driven format, carrying forward
   # the approved backlog intent rather than rewriting from scratch

   npx openspec instructions specs --change "<slug>" --json
   # Create specs/ with delta specs

   npx openspec instructions design --change "<slug>" --json
   # Write design.md

   npx openspec instructions tasks --change "<slug>" --json
   # Write tasks.md

   # 4. Verify no regressions
   npx openspec validate --all
   ```

   If the runtime cannot switch schemas in place, recreate the change under the
   same slug using the `governance-driven` schema and immediately carry the
   approved backlog proposal forward into the new artifact set.
7. Verify the promoted change is complete enough for implementation hand-off:

   - `proposal.md`, `specs/`, `design.md`, and `tasks.md` exist and are coherent
   - `npx openspec status --change "<slug>" --json` reflects the expected artifact state
   - the tasks clearly define the intended implementation scope

8. Refresh the generated backlog inventory so the promoted item is removed from
   the backlog report when it no longer uses the `backlog` schema:

   ```bash
   python .agents/scripts/generate_backlog_overview.py
   ```

9. Stop there. Offer the valid continuations based on the promoted change's
   readiness:

   - `/opsx:continue <slug>` when the promoted change still needs artifact
     refinement or decision capture before implementation
   - `/opsx:apply <slug>` when the promoted change is implementation-ready
   - end the session with the OpenSpec change prepared if the user only wanted
     planning/promotion

   **Hard stop.** Do not begin implementation, run apply workflows, or execute
   `tasks.md` in this same skill invocation. If the user wants implementation
   next, they must ask for it explicitly (e.g. `/opsx:apply <slug>` or a new task);
   treat any unsolicited continuation into code changes as a violation of this
   skill. A front-loaded or earlier broad instruction to implement the plan
   does not satisfy this later boundary unless it is restated after promotion
   as approval to implement this specific change.

## Hard stop — end of this skill

When steps 1–9 and verification below are satisfied, **terminate the workflow
here**. Do not continue into:

- Checking off or executing lines from `tasks.md`
- Editing source trees “because the plan implies it”
- Running apply/archive automation unless the user **clearly** starts that
  **different** workflow after promotion

Promotion is **complete** when the slug is governance-driven and the next step
is explicit. Offer `/opsx:continue <slug>` when artifact refinement remains and
`/opsx:apply <slug>` when the change is implementation-ready. Never silently
implement or reuse earlier approval as the implementation gate.

## Iron Law

**IRON LAW:** `NEVER TREAT A BACKLOG PROPOSAL AS IMPLICIT APPROVAL TO EXECUTE OR IMPLEMENT.`

No exceptions. The backlog proposal is the seed for planning, not a bypass around the AIS CR approval model.

**EXTENSION:** Completing OpenSpec artifacts (`proposal.md`, `specs/`, `design.md`,
`tasks.md`) does **not** authorize implementing those tasks or mutating product
code in the same run. Only an explicit user instruction to apply or implement
(after this skill ends) opens that scope.

**EXTENSION:** Approval is phase-local. A prior request to "implement this
plan" or similar broad instruction does **not** authorize the later
`plan -> implement` transition unless it is restated after promotion as
approval to implement this specific change.

**EXTENSION:** Planning-phase todos must not contain implementation steps.
Implementation steps belong exclusively in the OpenSpec change's `tasks.md`.

**EXTENSION:** Structured exploration clarifies the later planning phase, but
it does **not** replace the formal planning checkpoint or the approval gate
before promotion.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "I can start implementation straight from the backlog proposal" | Stop. Run the planning phase and obtain approval first. |
| "I'll read the whole backlog before planning" | Stop. Start from the named slug and inspect only directly related backlog proposals if needed. |
| "The backlog proposal is short, so I can skip SWOT or Impacts" | Stop. `planning-core.md` still applies. |
| "I'll keep the work in the backlog schema and improvise the rest" | Stop. Promote it cleanly into the governance-driven artifact flow. |
| "Once the OpenSpec files exist, I should archive too" | Stop. This workflow ends with an implementation-ready change, not archive. |
| "`tasks.md` exists, so I'll implement the checklist now" | Stop. This skill ends after promotion; use `/opsx:apply` or a new session only when the user explicitly asks to implement. |
| "The user already said to implement the plan, so I can carry that approval into `/opsx:apply`" | Stop. Implementation needs fresh post-promotion approval tied to the promoted change. |
| "The user attached a plan; I'll execute the whole plan including implementation" | Stop. Unless the user explicitly asked for implementation/apply, execute only the plan-from-idea promotion boundary. |
| "The user **bundled** promotion with implementation, bootstrap, or port work in one message" | Stop after promotion only. Use the **completion handoff**; require a **separate** message with **post-promotion** approval for `/opsx:apply` or apply-class work. |
| "I'll include implementation tasks in my planning-phase todos" | Stop. Todos cover only promotion workflow steps (verify, promote, refresh backlog). Implementation steps belong in `tasks.md`. |
| "The structured exploration pass clarified enough, so I can skip the formal planning phase or approval checkpoint" | Stop. Structured exploration feeds the planning phase; it never replaces the formal plan or approval gate. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] The named backlog slug was used as the source of truth for the planning pass.
- [ ] The governed structured exploration pass was completed and used as input to the formal planning phase.
- [ ] The plan included Goals/steps, SWOT, Impacts, and Evaluation/recommendation.
- [ ] The user explicitly approved the plan before promotion.
- [ ] Governance-driven artifacts were created or refreshed under the same slug.
- [ ] The resulting OpenSpec change is ready for implementation without silent scope expansion.
- [ ] The backlog inventory report was refreshed after promotion.
- [ ] The user was offered `/opsx:apply <slug>` as the next implementation step, or the workflow stopped with planning complete.
- [ ] No front-loaded or earlier broad approval was reused as implementation approval.
- [ ] No implementation work (code edits, `tasks.md` execution, apply scripts) ran as part of this skill unless the user explicitly requested apply **after** promotion in a clear follow-on instruction.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Read `openspec/changes/<slug>/proposal.md` from the named backlog proposal first; run one governed structured exploration pass; run one formal planning phase using that exploration output; wait for approval; promote the same slug into a governance-driven OpenSpec change; refresh `.agents/backlog-overview.md`; stop before implementation and offer `/opsx:continue <slug>` or `/opsx:apply <slug>` based on readiness.

## Governance

- Start from the backlog proposal the user names; read other backlog proposals
  only when they are directly related and needed for the same task.
- Keep the structured exploration pass inside `aiscr-plan-from-idea`; treat
  generated `openspec-explore` / `opsx:explore` surfaces as reference-only
  inputs unless a separate explicit task owns them.
- One planning phase only; re-plan only when documented triggers apply.
- Structured exploration improves the later plan, but it does not replace the
  formal planning phase or approval checkpoint.
- Do not broaden into unrelated backlog review while planning from one idea.
- Do not run high-impact scripts without explicit user approval.
- Scope ends at promotion plus backlog overview refresh; implementation belongs
  to `/opsx:apply` or another explicit workflow, not this skill's continuation,
  and it requires fresh post-promotion approval for the specific promoted
  change.
- After promotion, refresh the generated backlog inventory report unless the
  user explicitly asked not to touch reports.
- Usage logging follows repo-wide governance for significant management work;
  this workflow does not force a usage-log entry merely because promotion was
  completed.
- Self-review gate: before presenting the plan, verify no placeholder text,
  every goal maps to a step, and every impact is named; see
  `.agents/canonical_configs/governance_rules/planning-core.md` section 1.4.
- Requirement surface: `openspec/specs/openspec-requirement-governance/spec.md`.

## Valid next steps

- `/opsx:continue <slug>` -- continue refining the promoted change's artifacts when more decision capture is needed
- `/opsx:apply <slug>` -- start implementing the tasks in the promoted change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive a completed change after implementation
- `/aiscr-note-idea <slug>` -- capture a related idea as a new backlog item