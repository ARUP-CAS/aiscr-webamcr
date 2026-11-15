# Tasks

This checklist prepares and verifies the complete pack. It does not authorize live
imports, maintenance changes, fault injection, cleanup or git operations. Those session
boundaries remain as specified in `design.md` and the capability requirements.

## 1. Pack structure and coverage accounting

- [x] 1.1 Establish pack-owned files under `.agents/testing/imports-391-3527/`, a portable export layout and local exclusions for generated/evidence data; verify no path overlaps the delivered manifest and no application/vendor surface changes.
- [x] 1.2 Implement static inventory of CSV classes, fields, keys, operation permissions and relevant model constraints, pinned to source hashes; verify the inspected revision yields 46 classes, 33 allowed UPDATEs and the 13 named rejections.
- [x] 1.3 Define coverage/scenario/batch/evidence schemas and independent expected-effect records; verify every baseline class-operation cell has inputs, assertions and evidence, with a negative control that removes a required cell and must fail completeness.
- [x] 1.4 Populate class-specific branch coverage for every ownership/reference path, FK reassignment, constraint and failure boundary listed in design section 2; verify a source-to-ledger audit accounts for each branch and identifies unresolved acceptance rules explicitly.
- [x] 1.5 Document inventory and status semantics alongside these tools; verify prepared/blocked/unexecuted and simulated results cannot be rendered as executed passes.

## 2. Terminology and environment preflight

- [x] 2.1 Build the PO-backed glossary/control-label mapping with message keys and catalog hashes; verify the listed Fieldwork events, Sites, Spatial unit, Archaeological documentation point, elevation and unidentified-fieldwork terms against both catalogs and detect missing/changed entries.
- [x] 2.2 Provide preflight inputs and read-only queries for deployment revision, schema/reference identities, unused valid identifiers, import-volume/report paths and available read access; verify unknown values block dependent checks without assuming local/deployed equivalence.
- [x] 2.3 Implement session-only credentials and bounded, service-confined read clients for Digiarchiv/OAI/Fedora; verify redirects cannot forward authorization elsewhere and portable exports, logs and URLs contain no credentials.
- [x] 2.4 Implement feature-based seed discovery and sanitized frozen recipes; verify positive/negative query controls, actual nested feature presence, OAI pagination/empty payload handling and synthetic fallback for inaccessible cases.
- [x] 2.5 Document preflight ownership and exported-query fallback; verify an agent can consume the resulting files without requesting browser access or a copied secret configuration.

## 3. Complete behaviour datasets and operation batches

- [x] 3.1 Generate synthetic foundations, vocabulary variants, organisations/persons, users and all user relationships with verified reference types; verify natural/composite/prefixed/FK-as-key mappings and required/prohibited operations across these classes.
- [x] 3.2 Generate project, Individual find, Fieldwork event, Site, spatial unit, documentation unit, archaeological documentation point and elevation-point variants; verify geometry/constraint boundaries, both fieldwork types, automatic spatial-unit reuse/creation and complete expected target graphs.
- [x] 3.3 Generate documents, flights, extra data, authors/languages/persons/reviews/shapes, document parts and unidentified fieldwork/managers; verify all relationship alternatives, wrong subtype/companion cases and partial/full-update semantics.
- [x] 3.4 Generate both component-owner routes, activities, object/artefact finds, external sources/authors/editors/links and all supported history owners; verify affected and unaffected records, old/new parents and history/metadata multiplicity for every operation.
- [x] 3.5 Generate original/replacement binaries for document/project/Individual find plus distribution/paradata lifecycle fixtures; verify deterministic contents, MIME/name expectations, synthetic GPS metadata, thumbnails/backfill, nested/reserved/conflicting paths, tombstones and same-parent grouping expectations.
- [x] 3.6 Generate malformed/invalid inputs and supported field-boundary variants, covering each class's required fields/lookups/constraints and ZIP/CSV parser families; verify each negative assertion identifies its actual expected rejection and cannot be satisfied by an earlier unrelated error.
- [x] 3.7 Implement compatible single-operation batch assembly, header-sensitive UPDATE separation and dependency-aware child/root deletion graphs; verify every coverage item maps to an observable step and publish the actual upload/checkpoint count.
- [x] 3.8 Implement deterministic late binding from XLSX/query outputs to numeric DB keys and repository paths; verify mismatches, missing keys and guessed offsets are rejected and missing state cannot silently generate executable inputs.
- [x] 3.9 Add meaningful generator/ledger tests with synthetic input mutations, plus regeneration instructions; verify offline builds reproduce identical content and at least one adversarial test per structural/key/constraint family detects the intended failure.

## 4. Read-only assertions, evidence and session state

- [x] 4.1 Generate runnable scoped read-only SQL for before/after snapshots, expected values, relationships, constraints, geometry, history and controls across all classes; verify statements are read-only and equivalent exported results can be consumed without agent DB access.
- [x] 4.2 Implement paginated Fedora discovery and direct metadata/status/content/version checks with credential-free links; verify leading-slash/path variants, import-key-versus-UUID distinction, index-lag handling and content/XML comparisons with altered-result negative controls.
- [x] 4.3 Implement history and side-effect assertions, including deduplication, actors/notes, both former/new parents, file replacement/deletion and paradata-only unchanged DB/XML; verify a missing target or extra change fails despite matching aggregate counts.
- [x] 4.4 Implement immutable evidence ingestion, hashes, provenance and separate normalized views for XLSX, SQL exports, screenshots/observations and API results; verify incomplete/stale evidence is identified without overwriting originals or exposing unrelated personal fields.
- [x] 4.5 Implement per-suite run manifests, event/checkpoint records, restart handoff and evidence reports; verify a fresh session resolves the last checkpoint and does not repeat an already executed mutation.
- [x] 4.6 Generate phase-specific stop/failure/recovery and exact run-owned cleanup recipes; verify recovery uses reconciled actual state, simulations remain separate, and unauthorized injections/cleanup stay blocked.
- [x] 4.7 Document and test evidence retention rules; verify dataset cleanup cannot delete evidence and missing mandatory DB/Fedora/human evidence prevents a completeness verdict.

## 5. Human instructions and agent handoff

- [x] 5.1 Write `START-HERE.md` and the behaviour runbook with agent/human ownership for every step; verify all browser actions belong to the human and there is no alternate API import-submission route.
- [x] 5.2 Render batch instruction cards with exact full ZIP path/checksum, operation, PO-based controls, expected state, wait/stop criteria and next checkpoint; verify every card is actionable without inferring a filename, control or destination.
- [x] 5.3 Write the report retrieval/evidence guide covering `Stáhnout log importu`, task-ID lookup in `Reporty hromadného importu`, server/container paths, local downloads and shared-workspace/attachment handoff; verify each required artifact has a filename, destination and retrieval route.
- [x] 5.4 Make agents perform safe discovery, preparation, binding, comparisons, supplied-screenshot inspection and report extraction; verify human instructions request only irreducible manual actions or access-dependent fallbacks, with no bulk manual comparison/transcription.
- [x] 5.5 Conduct a local handoff rehearsal from the exported pack and synthetic retained evidence; verify a fresh agent can find inputs, identify the next human action, distinguish visible screenshot evidence from unobserved behaviour and produce a correct status report without browser use.

## 6. Independent load suite

- [x] 6.1 Build the independently provisionable 50,000-row relational workload and expected results; verify exact row/parent/dependency counts, available identifiers, ZIP expansion size and complete machine assertions.
- [x] 6.2 Build the separate workload with 20,000 distributions and 20,000 paradata rows across 10,000 synthetic files and 5,000 parent records; verify setup is outside measured inputs and expected binaries/bytes/history/transaction groups are explicit.
- [x] 6.3 Write `operator/load.md`, independent namespaces/run state, timing/monitoring templates and recovery instructions; verify neither suite starts or depends on execution of the other and each load window requires its own recorded approval.
- [x] 6.4 Implement load evidence analysis for phase times, counts/throughput, polling/report volumes, available service metrics and human-observed responsiveness; verify absent metrics remain unmeasured and load evidence cannot satisfy behaviour/UX checks automatically.
- [x] 6.5 Validate full-size generation offline and document exact load-session steps; verify both measured packs meet their declared sizes without submitting them to a live service.

## 7. Integration and delivery readiness

- [x] 7.1 Run the pack's focused tests and full offline preparation/verification workflow with both suites; verify incomplete coverage, mutated evidence, source drift and missing human observations all prevent false success.
- [x] 7.2 Review and export the complete pack with ready behaviour inputs, independent load inputs, portable definitions/checksums and explicit late-bound checkpoints; verify all 46 classes and named complex branches are accounted for and no secret or machine-only path is required to start a new session.
- [x] 7.3 Run `npm run openspec:validate`, strict change validation and `git diff --check` after artifact edits; verify no application or delivered-governance changes and update the rolling usage entry with actual preparation evidence and remaining live-session prerequisites.

## 8. Verification remediation

- [x] 8.1 Repair W1 by placing helper sources in a Git-visible package, updating consumers and verifying a clean source-only checkout can run the CLI and focused tests without changing ignore controls.
- [x] 8.2 Repair W2 with immutable content-addressed evidence retention; test distinct validation/terminal reports, snapshots and later tasks while preserving earlier checkpoints.
- [x] 8.3 Repair W3 by binding load verdicts to the retained run, deployment, selected manifest/input and terminal task evidence; test missing/mismatched/stale/altered provenance, update instructions, rebuild portable materials and rerun focused/OpenSpec checks.

## 9. Pre-session remediation

These tasks implement design decisions 10 and 11. They do not change application code. The `VazbaLookupImportField` defect stays for the developer to fix.

- [x] 9.1 Compute source and generator identity from LF-normalised text content (binary fixtures keep raw-byte hashes) and refresh the frozen inventory; verify the same Git content in CRLF and LF checkouts yields identical hashes, and a real one-line content change is still reported as drift.
- [x] 9.2 Replace exact commit equality in `preflight`, `report` and `load-analyse` with a recorded `source-equivalent` deployment: verified deployed commit plus per-file normalised parity of every pinned source; verify against `v2.0.0-alpha.2` that only `repository_connector.py` and the PO catalogs differ, that a differing pinned file withholds its dependent coverage, and that an unknown deployment still blocks.
- [x] 9.3 Add a frozen known-defects definition for the `VazbaLookupImportField` fallback (source path/lines/hash, trigger conditions, coverage IDs, batches, prerequisite). Mark the affected coverage `blocked`, move N07's three `MISSING-REFERENCE-*` owner rows into a deferred negative batch, and make V17–V19 deferred batches. Verify with a mechanical classifier over the generated inputs and batch order that no non-deferred batch contains a triggering row, and that the remaining N07 checks are unchanged. Also verify that rendering refuses a deferred batch until its prerequisite is recorded as met, and that blocked items prevent a completeness claim.
- [x] 9.4 Build the two-import relational substitute (`L01a` with 30,000 project/Fieldwork event/documentation unit rows, then `L01b` with 20,000 component/find rows), keeping `L01-relational-50000` blocked. Verify exact row and parent counts, that `L01b` owners exist only via `L01a`, that load reports label both imports as a substitute, and that the original workload can never yield a measured verdict while blocked.
- [x] 9.5 Add the known-defects section to report output and update `operator/known-source-risks.md` and `operator/load.md`: both defects, all four trigger conditions, whole-job abort, deferred items/batches, the substitute run and the absence of #4493 on `v2.0.0-alpha.2`. Verify the section renders as source-confirmed and never as a live failure or pass.
- [x] 9.6 Restore the pack to `.agents/testing/imports-391-3527/` as declared in this change (it currently sits under `.agents/local_scratch/_import/`) and remove the stale `tools/lib/__pycache__`; list superseded `generated/` iterations and exports without deleting them. Verify the documented commands run from the restored path and the pack still overlaps no delivered asset.
- [x] 9.7 Rebuild delivery r4 and the portable export with a new checksum, rerun the focused tests, run `npm run openspec:validate` and strict change validation, and check `git diff --check`. Verify that the preparation report records r4, the deferred counts and the substitute workload, and that no application or delivered-governance file changed. Update the rolling usage entry.
- [x] 9.8 Select ZM map-sheet categories (`KLADYZM10`, `KLADYZM50`) and spatial-unit geometry types (`GEOMETRY_LINIE`, `GEOMETRY_PLOCHA`, configured value first, source default second, PIAN type family only) in the reference SQL from application source constants pinned in the inventory, after the live preflight showed null `zm10`/`zm50`/`pian_polygon_type` on TEST. Verify that the new tests fail against the previous SQL, rebuild delivery r5 and the portable export, and confirm that only `sql/references.sql` and manifest hashes changed against r4.
- [x] 9.9 Let `fedora-read`, `fedora-search` and `capture` read a read-only Fedora login from a Windows Credential Manager generic entry (`--credential-target`, mutually exclusive with the interactive `--user` prompt), so an agent shell can collect evidence without the password entering a command, file or chat. Verify reading a real temporary entry, refusal of a missing entry and of both login routes, rebuild delivery r6 and the export, and confirm the inputs are byte-identical to r5.
- [x] 9.10 Add a mechanical recipe audit of all generated apply-insert rows against the inventory (required values, lookup target model including primary-key identity, vocabulary family) after the live B02 validation rejected rows; fix the empty `Oznamovatel.telefon`, the `dokumenty_posudky.posudek` vocabulary (replacing the non-existent self-reference variant with wrong-vocabulary) and supply S-JTSK companions for spatial units. Verify that the audit reports each live defect class on a mutated build and nothing on r7, rebuild r7 and the export. Add `revise-run`, which moves an existing run to a fixed pack revision with a recorded reason and reviewer only when every executed batch keeps its exact input (batches with only a failed or blocked validation may change); verify refusal of changed or removed executed batches, of a checked validation and of a changed source identity, and continue the live run on r7.

## 10. Live-run remediation and handoff

The behaviour run `behaviour-2026-11-14-live` ended on 2026-11-15 with every batch run, decided or deferred; its findings are reported on the two issues and the run starts over on the fixed deployment.

- [x] 10.1 Record operator decisions on gated and deferred batches as hash-chained events bound to the batch input (`resolve-gate`: accepted, record-behaviour, known-defect, not-executed, removed-by-setup, retry); verify that checkpoints of gated batches need a live decision, that voiding or an input change closes the gate again, and that not-executed and removed-by-setup close a batch without a checkpoint.
- [x] 10.2 Extend known-defect deferral: case-bound defects, the post-commit delete defects (`delete-history-target` kind), controlled procedures inheriting their preparing batch's deferral, and cleanup layers split into a runnable part and a deferred companion that blocks later layers through RESTRICT/PROTECT keys read from the inventory; verify with builds that reproduce the live D02 RestrictedError dependency and the D04/D05 split.
- [x] 10.3 Keep executed batches on the input and prerequisites they ran with (read from their checkpoints) in `revise-run`, `advance` and plain input registration; verify refusal of a stale-references rebuild and acceptance of a revision that restores the executed input.
- [x] 10.4 Add `record-batch` (oracle, Fedora change audit, optional direct reads, snapshot and setup/restore diffs, both checkpoints; refuses missing evidence, never overwrites) and `assess` (coverage assessments from checkpoints); `report` reads effective checkpoints; verify with focused tests.
- [x] 10.5 Change the behaviour evidence contract to the Fedora change audit plus direct reads where assertions need them, and a human-authored per-task or run-level observation (spec updated); verify a non-human author or a changed statement keeps items from passing.
- [x] 10.6 Document the fresh run on a new deployment (inventory, known-defect review, references, new run) and the per-batch loop in `START-HERE.md`.
- [x] 10.7 Rehearse a fresh run offline (simulation mode): build, start-run, advance, gate decisions, record-batch and report; verify a changed source pin stops the build until each known defect is reviewed.
- [ ] 10.8 Post the actionable findings to [ARUP-CAS/aiscr-webamcr#391](https://github.com/ARUP-CAS/aiscr-webamcr/issues/391) and [ARUP-CAS/aiscr-webamcr#3527](https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527) after exact-content approval, reduce the local run to the evidence developers need, and deliver the tooling on the agent branch.
- [ ] 10.9 Revise the pack's paradata contract (finding F37, operator decision 2026-11-15/16): every paradata insert, update and delete is expected to write history like distributions and refresh the owner's metadata timestamp - file-level paradata in the file's history, record-level paradata in the record's history - and the T04/V03 expectations change accordingly; verify the oracle against a build before the next live run.

## Workflow follow-up

- Review the prepared pack before beginning a separately authorized behaviour session.
- Schedule and authorize each load window independently; complete live outcomes in the
  run ledgers rather than marking preparation tasks as evidence of import correctness.
- Keep input manifests, reports, baselines, observations, results and recovery evidence
  after testing. Authorize dataset cleanup separately and retain the evidence until an
  explicit later retention decision.
- If hub delivery or sync is proposed later, inspect the scoped sync dry run before any
  future sync apply and obtain the required separate approval. Neither is in this change.
- Commit, push, spec sync and archive only on their own explicit user instructions.
