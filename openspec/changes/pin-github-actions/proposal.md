# Proposal

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).

## Why

The issue records mutable action references in workflows that receive SSH keys,
registry credentials, and image-signing permissions. Following the removal of
an action in [ARUP-CAS/aiscr-webamcr#4375](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4375),
the remaining action dependencies need immutable references and documented trust
decisions before repository-wide SHA enforcement can be enabled safely.
Review of [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544)
also exposed parser/test gaps and bounded existing SSH/input-handling defects;
the agreed scope includes all nine items in this same change.
The deployment-enabled DEV run subsequently exposed a regression that skips
test execution while reporting success. The approved follow-up also covers
four pre-existing gaps in result freshness, failure propagation, runner
outcomes, and deployment readiness.

## What Changes

- Pin every active external `uses:` reference in `.github/workflows/` to a
  verified 40-character commit SHA with its release version in a same-line
  comment. Select the latest compatible stable action releases, including
  compatible major upgrades, and record relevant compatibility or security
  exceptions. Include GitHub-owned actions and preserve local `./` calls.
- Replace `webfactory/ssh-agent` in `run-tests.yml` with native SSH-agent setup
  that supports subsequent SSH and SCP steps, fails on key-loading errors,
  and cleans up the agent.
- Retain `aquasecurity/trivy-action` and `sigstore/cosign-installer` with
  verified SHA pins and documented trust reviews, recording the approved
  rationale and residual trust.
- Keep Dependabot's weekly `github-actions` updates targeting `test`, including
  its `docker-actions` and `attest` groups, with compatible SHA/version-comment
  references. Use the existing human dependency-review and documentation-refresh
  process without a separate Actions maintenance workflow or review schedule.
- Generate the Actions inventory from workflow references through the existing
  dependency-documentation generator and pre-commit hook. Keep production
  parsing outside test modules and cover validation and generation in the
  existing test suite.
- Reject ambiguous shared release comments and duplicate YAML keys, while
  retaining unambiguous single-action flow syntax. Add independent complete
  inventory expectations covering job-level external reusable workflows.
- Scope the deployment SSH key to its SSH step and stop its native agent on
  every exit. Treat manual workflow inputs and reference names as data across
  both local and remote shell boundaries, validating accepted inputs before
  use and keeping the remote test script static.
- Correct the SSH lifecycle description and align CONTRIBUTING's local test
  command with CI's existing dependency-generation discovery.
- Read the downloaded test summary strictly as data: require one numeric
  `PASSED` and one numeric `FAILED` value, reject other content before writing
  outputs, and preserve cleanup after validation failure. Retain the existing
  two-count summary format and non-evaluating validation, extending result
  retrieval with current-attempt identity and an explicit execution outcome.
- Isolate non-interactive deployment/test commands from the remote shell's
  script input so deployment cannot consume the following test commands.
- Bind summaries and spreadsheet artifacts to the current execution attempt;
  preserve the previous spreadsheet separately as test-selection input and
  explicitly report a legitimate failed-only no-op.
- Propagate required build, deployment, database-clone, migration, and test
  failures through the nested scripts to GitHub. Update the recorded deployed
  version only after required deployment checks succeed.
- Make the test runner check subprocess outcomes and complete captured output;
  a startup crash or missing test summary must not become a passing zero-count
  result. Reject missing selection input and unknown numbered tests.
- Check required services and actual health within the target stack, including
  unhealthy, missing, and non-running tasks, before declaring readiness.
- Guarantee Selenium cleanup after workbook errors and classify each workbook
  row from that test's own result. Bound attempt history to the latest ten
  finished attempts and clean up verified inactive interrupted attempts after
  thirty days, protecting active runs and the previous selection workbook.
- Report actual passes, skips and expected failures distinctly through matching
  producer/consumer outcome metadata, retaining the two-key numeric summary.
  Bound summary reads before allocation, retain deployment precondition
  diagnostics, and support Bash outside the default Windows Git location.
- Share the existing SSH quoting and deployment helper implementations, repair
  deployment-log rotation, remove unused state reads/writes, and serialize DEV
  tests and deployments without canceling an active shared-host operation.
- Keep relevant trust rationale and pin-resolution, rollout, and recovery
  instructions on the linked dependency page. Remove PR-specific completion
  wording, special review-date bookkeeping, and the temporary
  `.agents/analysis/github-actions-trust.json` snapshot and its references.
- Deliver the runbook for enabling `sha_pinning_required` after compatible
  rollout, including approval, positive/negative probes, and recovery.
  Executing that runbook is post-merge follow-up.

This changes CI security governance, deployment/test execution, and the test
result publication contract. Production Django application behavior and
business-data contracts are unaffected; test-runner and test-output handling
under `webclient/` are in scope. Container image pinning, replacing
`docker/*` actions, and changes to other repositories are outside scope.

## Capabilities

### New Capabilities

- `github-actions-trust`: Immutable workflow action dependencies, native SSH
  access and key scope in both SSH workflows, safe workflow-input/result handling,
  reliable deployment/test execution and current-attempt results,
  generated dependency inventory, retained-action rationale, normal dependency
  maintenance, update compatibility, and documented policy readiness.

### Modified Capabilities

None. The repository currently has no durable capability specs.

## Impact

- Implementation: the six existing `.github/workflows/*.yml` files;
  `.github/dependabot.yml` only if a demonstrated compatibility issue needs it;
  production parsing and generation in `docs/generate_module_docs.py` or a
  shared helper; `scripts/test_pre_commit_actions_trust.py` and generator
  regression tests under `scripts/`, run by the existing CI test job;
  the two CI deployment wrappers, `scripts/test_deploy.sh`,
  `scripts/prod_deploy.sh`, `scripts/start_selenium_tests.sh`, and
  `webclient/run_tests.py`; the test-only output setting and existing Selenium
  spreadsheet writer where needed to separate selection input from new output;
  Selenium lifecycle/result classification; repository-owned protocol,
  retention, shell and test helpers and focused tests within these areas;
  the existing `generate-module-docs` pre-commit integration;
  `docs/source/12_zavislosti/github_actions.rst` and its `index.rst` entry;
  the local test instructions in `CONTRIBUTING.md`;
  generator-produced script documentation and indexes; cleanup of the temporary
  JSON snapshot and references, including the rolling usage entry. No separate
  workflow or privileged execution path for Dependabot is added.
- Planning: this local OpenSpec change and its rolling usage entry under
  `.agents/reports/usage/`.
- Generated assistant assets remain owned by the `aiscr-management` baseline
  recorded in `.agents/delivery-manifest.json` (source commit
  `4ce7896238fe9996ccf1b0740cf3d6440d8d4d3f`), supplied through its
  `.agents/sync/repos.toml` enrollment and
  `.agents/canonical_configs/asset_manifest.toml`. This change requires no hub
  delivery, sync apply, or governance bootstrap.

## Review remediation boundary

The five new findings are F1 (shared release comment), F2 (duplicate YAML
keys), F4 (SSH lifecycle wording), F5 (incomplete inventory expectations),
and F6 (local test guidance). O1 (deployment agent cleanup), O2 (deployment
key scope), O3 (DEV test input interpolation), and N1 (deployment tag
interpolation) predate the reviewed commit and retain their advisory
`fix-in-pr` disposition. Their repair is included without attributing them
to this PR or changing the review verdict. Evidence and task mapping live
in [design.md](design.md#review-remediation-2026-11-23).

The first review's nine repairs were implemented in commit `62146241c`.
The second review identified R2-F1 (stale capture-phase status prose) and
advisory pre-existing R2-O1 (execution of a downloaded result summary).
Their capture and application were explicitly requested together. Keep
historical milestones separate from current task progress in [tasks.md](tasks.md).

On 2026-11-24 the user approved capture of the reproduced stdin regression and
all four pre-existing gaps into this same change. Group 6 in [tasks.md](tasks.md)
records their implementation and verification progress; the preceding 23
completed tasks remain historical evidence. The four older gaps retain
advisory `fix-in-pr` attribution. The subsequent explicit apply invocation
authorized implementation; live operations retain their separate approval.
Evidence, design decisions, and item mapping are in
[design.md](design.md#execution-reliability-remediation-2026-11-24).

Preserve valid workflow inputs, defaults, triggers, permissions, deployment
selection, and test modes. Reject unsafe values before they can become shell
code. These bounded repairs do not authorize a deployment, workflow dispatch,
review post, or broader infrastructure refactor.

## CI portability and runner diagnostic remediation (2026-11-24)

After delivery of `5ae9cf45c`, the user approved capture and implementation of
two introduced defects in [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544).
The [pre-commit job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45374557884/job/138377173853)
failed in the combined execution fixture before hooks ran: copying command
stubs without executable permissions selected real host commands on Linux.
The [CodeQL discussion](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4678598669)
traces a secret-backed output path to runner logging. Raw exception messages
also reach stderr and outcome metadata.

Group 7 repairs fixture permissions and verifies command selection and intended
failure stages, replaces runner-owned path and exception diagnostics with
validated attempt identifiers and controlled stages, and adds regressions
including failed error publication. Existing output files and process status
contracts remain in force. Validate Windows and Linux separately; record any
hosted CI or CodeQL acceptance still awaiting delivery. Refresh affected
documentation through its existing generator and keep one usage entry for
this remediation. The preceding 31 completed tasks describe the earlier scope.

## Round-four review remediation (2026-11-24)

The user approved capture of the [round-four review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6043320852)
at `09d4d12e1acf64a6c0276f3af3c549bf6c957f9d`. This captures seven findings
and seven bounded advisory repairs in the same change. Observation O4 is
recorded as no change: `-a`/`--all` already selects the all-tests default and
participates in mutual exclusion. The prior CodeQL thread is resolved and
outdated; it is not reopened. Source attribution, every comment link and task
mapping are in [design.md](design.md#round-four-review-remediation-2026-11-24).

The confirmed retention policy keeps ten finished attempts, including failed
attempts, and retains interrupted attempts for thirty days before cleanup,
which requires verified inactivity. Active attempts and the selection
workbook remain protected. Explicit skipped/expected-failure accounting must
work across producer and consumer; correcting one arithmetic expression must
not accidentally reject an executed expected-failure-only run. Existing
ordinary zero-execution failure and failed-only no-op behavior remain in force.

The subsequent explicit `openspec-apply-change` invocation authorized the
captured implementation. Group 8 records its implementation and validation;
the previous 34 completed tasks remain historical evidence. Capture changed
only the four existing planning artifacts and one rolling usage entry.
Implementation uses repository-owned source, fixtures and documentation;
live cleanup, deployment, posting, delivery, sync and archive retain their
separate authorization boundaries.

## Round-five review capture (2026-11-25)

The user approved planning capture of the [round-five review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6049994746)
at `d90182be3893880e6f9d9e4c4a89591180b202e7`. The review confirms the
fourteen round-four repairs and the decision to keep the all-tests aliases.
The 44 completed tasks describe that work. Group 9 tracks seven new findings
and two bounded advisory repairs. The [design ledger](design.md#round-five-review-capture-2026-11-25)
links each item to its task and distinguishes new findings from pre-existing
observations.

Restore selection of older release tags by resolving the shared SSH helper
from the workflow revision while retaining the requested tag for deployment.
Reject duplicate attempt identities before pruning and acquire an ownership
lease before publishing a new attempt directory. Existing uncertain evidence
stays protected under the agreed retention policy. Consolidate bounded outcome
reading, report validated test failures with an annotation and a nonzero exit,
and make Docker fixture drift fail at setup. Document the outcome-v2
prerequisite for the deployment-disabled DEV control. Include the production
option cleanup and shared stack removal as advisory `fix-in-pr` work.

The scope covers repository-owned workflow, test runner, fixture and
documentation behavior. It requires no delivered governance or hub asset
changes. The user subsequently authorized group 9 implementation by invoking
`openspec-apply-change`. Delivery and live acceptance remain separate.

## Round-six review capture (2026-11-25)

The user approved capture of the [round-six review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6053375832)
at `5dc50a8797e184f8c11b06746bb6939526bff4db`. The review confirms the
nine round-five repairs. Group 10 covers five new findings and one advisory
in the same repository-owned workflow and runner scope. The
[design ledger](design.md#round-six-review-capture-2026-11-25) links each
disposition to its task.

Publish the retention root lock only after its marker is initialized.
Keep retrieval bookkeeping out of the verified artifact and narrow
`GITHUB_OUTPUT` to the artifact eligibility signal, with all validated result
details still in the report and outcome. Share the web-container lookup
used by cloning and test launch. Explain the historical failure semantics
that apply when deploying an older tag.

O11 is a pre-existing advisory. The test deployment parser inherited
unsupported letters from its production ancestor. It will reject these
and other unsupported options before touching Docker, while preserving
the valid deployment and test selection modes. The 52 completed tasks
remain historical evidence. The user subsequently authorized group 10
implementation by invoking `openspec-apply-change`.

## Follow-up outside this change

After merge, follow up the DEV SSH/SCP run, an actual Dependabot SHA/comment
update PR, human promotion to `main` and other intended execution refs,
approved repository policy activation, and positive/negative policy probes.
Their ordering, authorization, and evidence requirements remain explicit in
[tasks.md](tasks.md#workflow-follow-up) and [design.md](design.md).

This change ends with the implementation, documentation, and verification
deliverable in this PR. Completing it does not establish the hosted outcomes
or resolve the driving issue's remaining operational acceptance criteria.
