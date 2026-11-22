# Tasks

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Contracts: [github-actions-trust](specs/github-actions-trust/spec.md).
Approach and rollout: [design.md](design.md).

All tasks below are implementation or acceptance work, initially incomplete.
Starting implementation requires fresh approval naming `pin-github-actions`.
Hosted operations require approval for their target and effects.

## 1. Immutable action references and update compatibility

- [ ] 1.1 Refresh the active workflow inventory and upstream release provenance; verify every selected pin is a commit in the action's upstream repository, peel annotated tags, resolve full release-version comments, and preserve existing major versions. Record source URLs and review dates under `.agents/`.
- [ ] 1.2 Pin every active external reference across the six `.github/workflows/*.yml` files, retaining both Trivy calls and the Cosign installer; verify the complete inventory has full SHAs and version comments, repeated releases agree, and the local reusable call and existing action inputs remain unchanged.
- [ ] 1.3 Add `scripts/test_pre_commit_actions_trust.py` to the existing test-discovery pattern; verify fixture mutations reject tags, branches, short or malformed hashes, and missing comments with file/line diagnostics, while accepting valid action subpaths and local calls and ignoring commented steps.
- [ ] 1.4 Preserve Dependabot's weekly `github-actions` updates into `test` and its `docker-actions` and `attest` groups; test the existing configuration, add only a reproduced necessary repair to `.github/dependabot.yml`, and verify the new regression suite runs through `python -m unittest discover -s scripts -p 'test_pre_commit*.py' -v`.
- [ ] 1.5 Create `docs/source/12_zavislosti/github_actions.rst`, link it from `index.rst`, and document verified pin resolution, comment updates, and the boundary between local checks and a real Dependabot PR; verify the lookup procedure against an actual selected release and resolve the documentation link.

## 2. Native DEV SSH-agent lifecycle

- [ ] 2.1 Replace `webfactory/ssh-agent` in `run-tests.yml` with native setup and unconditional cleanup, passing only agent socket/PID state across steps; verify the workflow no longer references that action, keeps existing host verification and VPN behavior, and does not persist the private key.
- [ ] 2.2 Extend the focused suite to execute the real setup and cleanup shell with a disposable key in isolated step environments; verify later SSH/SCP clients receive the loaded identity, invalid-key loading fails before remote execution, and agents are stopped after success or a simulated later failure without secrets in logs.
- [ ] 2.3 Document native-agent operation and the authorized DEV test procedure on the dependency page; verify the instructions explicitly use `nasadit_verzi: false`, an agreed valid test selection, and later result retrieval, with deployment requiring separate authorization.

## 3. Trust registry and retained scanner/signer decisions

- [ ] 3.1 Populate the dependency page with every retained third-party action's upstream owner, source-backed maintenance status, actual last review date, quarterly and event-driven review frequency, exposure, and rationale; verify registry coverage against the final active inventory and distinguish GitHub-owned actions from third-party actions.
- [ ] 3.2 Record the approved retention of Trivy and the Cosign installer with SHA pins and trust reviews; inspect the selected upstream revisions and transitive action references, document residual binary/network trust, and verify the registry reasons and workflow calls agree.
- [ ] 3.3 Document enforcement readiness across `test`, `main`, and other intended execution refs, harmless positive/negative probes, and recovery; verify the runbook forbids enabling enforcement before compatible rollout or silently rewriting published tags, and that the new Czech RST page builds and appears in the dependency navigation.

## 4. Local integration and governance close-out

- [ ] 4.1 Run the focused workflow suite and the existing workflow/report regression tests; verify pinning and SSH changes preserve existing triggers, permissions, scanning/signing inputs, and local reusable-workflow behavior through tests and full diff inspection.
- [ ] 4.2 Validate all edited OpenSpec artifacts with `npm run openspec:validate` and `node node_modules/@fission-ai/openspec/bin/openspec.js validate pin-github-actions --strict`; record per-change results separately from unrelated repository failures, then run the contribution-required compilation and pre-commit checks and inspect generated diffs.
- [ ] 4.3 Update this change's rolling usage entry with runtime/backend metadata, actual validation, and pending hosted evidence; verify only approved repository-owned files changed. If generated-asset changes become necessary, stop for separate hub scope and require a dry-run sync check before any later approved sync apply.

## 5. Approved hosted rollout and acceptance

- [ ] 5.1 After approved delivery and human review into `test`, run the approved manual DEV test without deployment; record its workflow URL and revision and verify successful SSH execution and later SCP result retrieval.
- [ ] 5.2 Observe and record a real Dependabot PR targeting `test` whose diff updates both a SHA pin and its same-line version comment, preserving applicable grouping; leave this task pending if no update exists.
- [ ] 5.3 Arrange human promotion of the pinned workflows to `main` and audit every ref intended to remain executable, including externally called composite dependencies; record each prepared ref or explicit retirement decision and verify no intended execution path still depends on mutable action references.
- [ ] 5.4 Re-read the live Actions policy and obtain approval for the exact policy change and disposable probes; enable only `sha_pinning_required` after task 5.3 and verify the API returns true while preserving other settings.
- [ ] 5.5 Run approved harmless pinned and tag-pinned control probes with no secrets, infrastructure access, publication, or write-token permissions; record run URLs and revisions, verify the pinned control succeeds and the tag-pinned probe is rejected specifically by the policy, and remove disposable probe artifacts with approval.

## Workflow follow-up

- Reconcile the final hosted evidence with all six issue acceptance criteria before requesting completion and archival approval.
- Sync durable specs or archive this change only on a separate explicit instruction.
