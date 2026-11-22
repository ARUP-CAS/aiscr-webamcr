# Tasks

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Contracts: [github-actions-trust](specs/github-actions-trust/spec.md).
Approach and rollout: [design.md](design.md).

Tracked tasks cover implementation and verification deliverable in this PR.
Hosted rollout and observations that require merging or later operational
approval are listed under Workflow follow-up, outside this change's completion.
Checkboxes reflect the revised scope captured after exploration. Tasks affected
by current-release selection, generation, documentation cleanup, and renewed
integration checks are reopened; prior local completion covered the earlier
design only.

## 1. Immutable action references and update compatibility

- [x] 1.1 Refresh the active workflow inventory and assess the latest stable release of every retained action, including compatible major upgrades; verify release provenance against upstream commits, peel annotated tags, and record concise source URLs and compatibility exceptions in change evidence rather than a permanent JSON snapshot.
- [x] 1.2 Apply the latest compatible verified SHA pins and same-line release comments across the six workflow files, retaining both Trivy calls and the Cosign installer; verify complete coverage, agreement of repeated releases, preserved local calls, and compatibility with the used runners, inputs, outputs, and permissions. Change inputs only where the selected compatible update demonstrably requires it.
- [x] 1.3 Move reusable reference parsing/validation out of `scripts/test_pre_commit_actions_trust.py` into production generator code or a shared helper and have tests exercise that code; verify tags, branches, short/malformed hashes, and missing comments fail with file/line diagnostics, while action subpaths, local calls, quoted references, and commented steps are handled correctly through the existing workflow test suite.
- [x] 1.4 Preserve Dependabot's weekly `github-actions` updates into `test` and its `docker-actions` and `attest` groups; verify the existing configuration through the workflow regression suite. No configuration repair was required for the pinned reference format.
- [x] 1.5 Assess selected upstream revisions, ownership/maintenance signals, nested action references, and downloaded tool defaults against relevant advisories; verify the findings against configured exposure and document material residual risk or release exceptions with source links. Resolve the Trivy default-tool advisory findings and current Scout release selection within this update without creating a separate maintenance routine.

## 2. Native DEV SSH-agent lifecycle

- [x] 2.1 Replace `webfactory/ssh-agent` in `run-tests.yml` with native setup and unconditional cleanup, passing only agent socket/PID state across steps; verify the workflow no longer references that action, keeps existing host verification and VPN behavior, and does not persist the private key.
- [x] 2.2 Extend the focused suite to execute the real setup and cleanup shell with a disposable key in isolated step environments; verify later SSH/SCP clients receive the loaded identity, invalid-key loading fails before remote execution, and agents are stopped after success or a simulated later failure without secrets in logs.
- [x] 2.3 Document native-agent operation and the authorized DEV test procedure on the dependency page; verify the instructions explicitly use `nasadit_verzi: false`, an agreed valid test selection, and later result retrieval, with deployment requiring separate authorization.

## 3. Generated inventory and ordinary dependency maintenance

- [x] 3.1 Extend `docs/generate_module_docs.py` or its shared helper to generate a marked Actions inventory from active workflow references through the existing `generate-module-docs` pre-commit hook and normal dependency-documentation refresh; verify action paths, owners/source links, release versions, full commits, and workflow locations cover all external actions, omit local/commented calls, and preserve different releases of one action without network access or credentials.
- [x] 3.2 Add isolated generator regression tests under `scripts/`, following `test_generate_js_libraries.py`, and include them in the existing CI test job; verify additions, removals, version changes, invalid pins, authored-section preservation, deterministic ordering, and a clean second generation run. Keep all tests in the existing test suite and preserve bot exclusions without adding a maintenance workflow or a privileged Dependabot mode.
- [x] 3.3 Revise the Czech dependency page to retain relevant pin-resolution and operating instructions while removing PR-specific completion prose, quarterly/special reviews, recurring review-date fields, and duplicated manual version lists; verify it describes the normal human dependency-review and existing refresh points honestly, preserves its index link and authored rationale, and builds with its generated inventory.
- [x] 3.4 Update concise owner/exposure/retention rationale for every retained third-party action, especially Trivy and Cosign, using the selected-release assessment; verify the rationale agrees with the final workflow inventory, nested references, and tool behavior without claiming a full audit or automatically refreshed trust decisions.
- [x] 3.5 Inspect and remove only the temporary `.agents/analysis/github-actions-trust.json` snapshot, update references in durable documentation and the rolling usage entry, and preserve useful concise conclusions/source links in change evidence; verify no operational consumers or broken references remain and no unrelated analysis files are removed.
- [x] 3.6 Document enforcement readiness across `test`, `main`, and other intended execution refs, harmless positive/negative probes, and recovery; verify the runbook forbids enabling enforcement before compatible rollout or silently rewriting published tags. Rebuilding and cleaning the surrounding page are covered by task 3.3.

## 4. Local integration and governance close-out

- [x] 4.1 Run the focused workflow suite, existing workflow/report regressions, and dependency-generation tests; verify final pins, generator/pre-commit integration, idempotency, and native SSH behavior through tests and full diff inspection, preserving triggers, permissions, required scanning/signing outputs, and local reusable-workflow behavior.
- [x] 4.2 Validate all edited OpenSpec artifacts with `npm run openspec:validate` and `node node_modules/@fission-ai/openspec/bin/openspec.js validate pin-github-actions --strict`; record per-change results separately from unrelated repository failures, then run the contribution-required compilation and pre-commit checks and inspect generated diffs.
- [x] 4.3 Update the same rolling usage entry with runtime/backend metadata, revised task completion, actual validation, temporary-snapshot cleanup, and separately identified post-merge follow-up; verify only approved repository-owned files changed and replace the earlier 14/14 claim with current evidence. If generated-asset changes become necessary, stop for separate hub scope and require a dry-run sync check before any later approved sync apply.

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
