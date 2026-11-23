# Tasks

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Contracts: [github-actions-trust](specs/github-actions-trust/spec.md).
Approach and rollout: [design.md](design.md).

Tracked tasks cover implementation and verification deliverable in this PR.
Hosted rollout and observations that require merging or later operational
approval are listed under Workflow follow-up, outside this change's completion.
The 2026-11-23 capture includes F1/F2/F4/F5/F6 and advisory pre-existing
O1/O2/O3/N1 from the review of [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544).
The item-to-task mapping and evidence are in [design.md](design.md#review-remediation-2026-11-23).
Seven affected tasks are reopened and three bounded tasks are added; ten
unaffected tasks remain complete. The prior 17/17 result describes the earlier
scope, not completion of this revision. Capture authorizes planning only;
implementation requires a separate explicit apply instruction.

## 1. Immutable action references and update compatibility

- [x] 1.1 Refresh the active workflow inventory and assess the latest stable release of every retained action, including compatible major upgrades; verify release provenance against upstream commits, peel annotated tags, and record concise source URLs and compatibility exceptions in change evidence rather than a permanent JSON snapshot.
- [x] 1.2 Apply the latest compatible verified SHA pins and same-line release comments across the six workflow files, retaining both Trivy calls and the Cosign installer; verify complete coverage, agreement of repeated releases, preserved local calls, and compatibility with the used runners, inputs, outputs, and permissions. Change inputs only where the selected compatible update demonstrably requires it.
- [x] 1.3 Harden the existing production parser and its workflow regressions for F1/F2: reject ambiguous shared release comments and duplicate mapping keys before extracting references, with file/line diagnostics and no inventory overwrite on failure. Verify duplicate `uses` and structural keys cannot hide references; keep rejection of tags, branches, short/malformed hashes, and missing comments, while preserving subpaths, local/commented calls, quoted values, and unambiguous single-action flow syntax.
- [x] 1.4 Preserve Dependabot's weekly `github-actions` updates into `test` and its `docker-actions` and `attest` groups; verify the existing configuration through the workflow regression suite. No configuration repair was required for the pinned reference format.
- [x] 1.5 Assess selected upstream revisions, ownership/maintenance signals, nested action references, and downloaded tool defaults against relevant advisories; verify the findings against configured exposure and document material residual risk or release exceptions with source links. Resolve the Trivy default-tool advisory findings and current Scout release selection within this update without creating a separate maintenance routine.

## 2. Native SSH lifecycle and workflow inputs

Implement 2.4/2.5 with their regressions in 2.6 before finalizing the adapted
cross-step fixtures in 2.2 and the workflow descriptions in 2.3; existing task
identifiers are retained for review traceability.

- [x] 2.1 Replace `webfactory/ssh-agent` in `run-tests.yml` with native setup and unconditional cleanup, passing only agent socket/PID state across steps; verify the workflow no longer references that action, keeps existing host verification and VPN behavior, and does not persist the private key.
- [x] 2.2 Adapt the existing disposable-key fixtures to supply valid explicit workflow inputs after the transport repair; execute the actual setup, SSH/result, and cleanup shell in isolated step environments. Verify later SSH/SCP clients still share the loaded identity, invalid-key loading stops remote execution, and success or SSH/SCP failure still releases the agent without exposing secrets.
- [x] 2.3 Correct F4 and document the revised SSH/input behavior on the dependency page; verify one result-retrieval step contains both SCP calls, unconditional cleanup occurs after agent use with later VPN/result steps, deployment's single-step agent is released, and valid test selection is checked before connection. Preserve the `nasadit_verzi: false` DEV procedure and separate deployment authorization; build the page and inspect its workflow descriptions.
- [x] 2.4 Repair advisory O1/O2 in `deployment.yml`: scope `SSH_PRIVATE_KEY` to the SSH connection step, consume the key from its environment, and install an EXIT trap immediately after agent setup and before key loading. Add disposable-key lifecycle and environment-scope regressions; verify success, key-loading failure, and simulated remote failure all attempt cleanup, preserve the original result, and do not expose or persist the key.
- [x] 2.5 Repair advisory O3/N1 within the two acquired workflow files: read manual inputs and reference values from step environment, validate tags/test modes/booleans/numbers before VPN or SSH, and pass safely quoted arguments through SSH to a static `sudo bash -s --` test script. Verify raw workflow expressions no longer generate the affected shell assignments, remote argument quoting covers both interpretation boundaries, and valid tag normalization, reference names, source/environment selection, input defaults, optional deployment, and all test modes retain their behavior.
- [x] 2.6 Add isolated regressions for the actual local validation and remote argument transport in task 2.5; verify command substitution, single/double quotes, newlines, malformed tags, unknown modes, invalid booleans, nonnumeric numbers, and missing `konkretni` numbers cannot execute canaries or reach remote work. Include literal valid reference names and valid tag/all-tests/failed-tests/numbered-test controls, using stubbed SSH/sudo/deployment/test operations without live infrastructure.

## 3. Generated inventory and ordinary dependency maintenance

- [x] 3.1 Extend `docs/generate_module_docs.py` or its shared helper to generate a marked Actions inventory from active workflow references through the existing `generate-module-docs` pre-commit hook and normal dependency-documentation refresh; verify action paths, owners/source links, release versions, full commits, and workflow locations cover all external actions, omit local/commented calls, and preserve different releases of one action without network access or credentials.
- [x] 3.2 Repair F5/F6 within the existing suite: add fixtures with external job-level reusable workflows and step-level calls, define complete expected inventory rows independently of production traversal, and assert exact results so omitted or unexpected rows fail. Preserve additions/removals/version changes, local/comment exclusions, invalid-pin, authored-section, ordering, idempotency, and stale-input refresh coverage; align CONTRIBUTING's local command with CI's `test_generate_*.py` and run both generation suites. Preserve bot exclusions and the existing CI job without adding another workflow or privileged bot mode.
- [x] 3.3 Revise the Czech dependency page to retain relevant pin-resolution and operating instructions while removing PR-specific completion prose, quarterly/special reviews, recurring review-date fields, and duplicated manual version lists; verify it describes the normal human dependency-review and existing refresh points honestly, preserves its index link and authored rationale, and builds with its generated inventory.
- [x] 3.4 Update concise owner/exposure/retention rationale for every retained third-party action, especially Trivy and Cosign, using the selected-release assessment; verify the rationale agrees with the final workflow inventory, nested references, and tool behavior without claiming a full audit or automatically refreshed trust decisions.
- [x] 3.5 Inspect and remove only the temporary `.agents/analysis/github-actions-trust.json` snapshot, update references in durable documentation and the rolling usage entry, and preserve useful concise conclusions/source links in change evidence; verify no operational consumers or broken references remain and no unrelated analysis files are removed.
- [x] 3.6 Document enforcement readiness across `test`, `main`, and other intended execution refs, harmless positive/negative probes, and recovery; verify the runbook forbids enabling enforcement before compatible rollout or silently rewriting published tags. Rebuilding and cleaning the surrounding page are covered by task 3.3.

## 4. Local integration and governance close-out

- [x] 4.1 Run the focused workflow suite, existing workflow/report regressions, and dependency-generation tests after all nine remediations; verify pins, parser failures, exact inventory coverage, generator/pre-commit integration, idempotency, both agent lifecycles, and input transport through tests and full diff inspection. Preserve triggers, permissions, valid workflow behavior, required scanning/signing outputs, and the local reusable call; allow only the explicitly planned key-scope, cleanup, input-validation, and transport changes in the affected SSH workflows.
- [x] 4.2 Validate the revised implementation's OpenSpec artifacts with `npm run openspec:validate` and `node node_modules/@fission-ai/openspec/bin/openspec.js validate pin-github-actions --strict`; record per-change results separately from unrelated repository failures, then run the contribution-required compilation/pre-commit checks and inspect generated diffs. A planning-only validation does not complete this renewed implementation check.
- [x] 4.3 Update the rolling entry for the current remediation change set with runtime/backend metadata, all nine item dispositions, actual task/validation results, and separately identified hosted follow-up; preserve the earlier committed usage record as historical evidence and verify only approved repository-owned files changed. Keep prior 14/14 and 17/17 milestones distinct from this revision's completion. If generated assistant assets need changes, stop for separate hub scope and require a dry-run sync check before any later approved sync apply.

## Workflow follow-up

These operations remain follow-up to the driving issue. They are outside this
PR's implementation scope and do not block completion of this OpenSpec change.

- **DEV verification:** After approved delivery and human review into `test`, run the approved manual DEV test without deployment; record its workflow URL and revision and verify successful SSH execution and later SCP result retrieval.
- **Dependabot observation:** Observe and record a real Dependabot PR targeting `test` whose diff updates both a SHA pin and its same-line version comment, preserving applicable grouping. Keep this follow-up pending if no update exists.
- **Supported-ref rollout:** Arrange human promotion of the pinned workflows to `main` and audit every ref intended to remain executable, including externally called composite dependencies; record each prepared ref or explicit retirement decision and verify no intended execution path still depends on mutable action references.
- **Policy activation:** After supported-ref rollout, re-read the live Actions policy and obtain approval for the exact policy change and disposable probes; enable only `sha_pinning_required` and verify the API returns true while preserving other settings.
- **Policy probes:** Run approved harmless pinned and tag-pinned control probes with no secrets, infrastructure access, publication, or write-token permissions; record run URLs and revisions, verify the pinned control succeeds and the tag-pinned probe is rejected specifically by the policy, and remove disposable probe artifacts with approval.
- Reconcile the follow-up evidence with the driving issue's remaining acceptance criteria before claiming that issue resolved. PR-local completion does not establish those hosted outcomes.
- Sync durable specs or archive this change only on a separate explicit instruction.
