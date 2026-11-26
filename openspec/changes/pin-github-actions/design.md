# Design

## Context

See [proposal.md](proposal.md) for motivation and scope, originating in
[ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).

Historical baseline evidence gathered before implementation on 2026-11-22:

| Tier | Observation |
| --- | --- |
| Source-verified | Six workflow files contained 34 active `uses:` entries: 33 external references to 17 distinct action paths and one local reusable workflow. All external references used tags. Commented Scout steps were excluded. |
| Source-verified | `run-tests.yml` initialized `webfactory/ssh-agent` before separate SSH and SCP steps. `deployment.yml` supplied a native-agent example within one shell step. |
| Source-verified | Dependabot already schedules weekly action updates into `test` with `docker-actions` and `attest` groups. |
| Live-verified | The policy read returned `enabled: true`, `allowed_actions: all`, and `sha_pinning_required: false`; the repository's default branch was `main`. Re-read hosted state before activation. |
| Documentation-verified | GitHub documents SHA and same-line version-comment updates by Dependabot, and says SHA enforcement also covers GitHub-owned actions. Reusable workflows are a distinct policy case. |
| Inferred risk | Mutable references can introduce upstream changes into privileged jobs. Neither this plan nor the issue establishes that a compromise has occurred. |

The issue's 2026-11-21 inventory and the baseline above are dated observations.
The first local implementation pinned 32 retained external calls across 16
distinct action paths, replaced the SSH-agent action, and added tests and a
manual dependency page. Exploration found missing inventory generation,
PR-specific prose, a temporary evidence snapshot, and unnecessary periodic
reviews. Those areas and the release/security assessment were subsequently
revised; the review remediation below was completed in `62146241c`.

No DEV workflow, image publication, Dependabot update, or policy rejection
has been exercised for this change. Those hosted observations remain
follow-up to the driving issue.

## Review remediation (2026-11-23)

The first review remediation covered all nine items from the
review of [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544)
at `0735cb560a223d2fac0822358359a4521e4e4322`, compared with
`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`. The identifiers below preserve the
review's finding/observation distinction; they are not new severity judgments.

| Item | Evidence and bounded repair | Tasks |
| --- | --- | --- |
| F1 | `docs/generate_module_docs.py:3340` accepts one trailing release comment for multiple flow-style calls. Reject ambiguous comment ownership. | 1.3 |
| F2 | `docs/generate_module_docs.py:3278` returns the first duplicate mapping key. Reject duplicate keys before extracting calls. | 1.3 |
| F4 | `docs/source/12_zavislosti/github_actions.rst:183` describes separate SCP steps and final cleanup; the workflow has one result step with two SCP calls and later VPN/result steps. Correct the wording. | 2.3 |
| F5 | `scripts/test_generate_github_actions.py:195` builds only a step-level expected subset. Add independent exact inventory expectations including external reusable jobs. | 3.2 |
| F6 | `CONTRIBUTING.md:272` still names only the JavaScript suite. Match CI's `test_generate_*.py` discovery. | 3.2 |
| O1 | `.github/workflows/deployment.yml:104` starts an agent without stopping it. Add single-step EXIT cleanup. | 2.4 |
| O2 | `.github/workflows/deployment.yml:44` exposes the private key at job level. Scope it to the loading step. | 2.4 |
| O3 | `.github/workflows/run-tests.yml:111` substitutes manual input into the remote shell body. Validate and transport values as arguments to a static script. | 2.5, 2.6 |
| N1 | `.github/workflows/deployment.yml:53` substitutes the tag before validation. Read it from step environment and validate without evaluation. | 2.5, 2.6 |

Exploration reproduced F1 and F2 with in-memory parser fixtures. The F5
fixture confirmed that the current test's expected subset omits a job-level
external reusable call. Harmless local Bash probes reproduced command
substitution in the actual tag-normalization body and in the DEV script's
assignment prefix. They used synthetic values, discarded normalization
outputs, replaced sudo with a local function, and performed no SSH or live
operation. Base/head source comparison confirms O1/O2/O3/N1 predate this PR;
they retain advisory `fix-in-pr` disposition and do not contribute to its verdict.

F2 establishes a local validator gap. The inspected GitHub runner
`TemplateReader` explicitly reports duplicate keys, supporting fail-closed
behavior; hosted parser behavior was not exercised. Do not describe this as
a verified bypass of GitHub enforcement. Tests preceding that remediation
did not cover the reproduced edge cases. The capture reopened affected tasks;
the approved implementation completed them in `62146241c`.

## Second review remediation (2026-11-23)

The second review of [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544)
at `62146241c98d877985751550d10a6f34dfed5ebe` confirmed the first round's nine
items addressed and identified the following bounded additions. The user
explicitly requested their capture and application together. The task
checkboxes record current implementation progress; dated earlier completion
records remain historical evidence.

| Item | Evidence and repair | Tasks |
| --- | --- | --- |
| R2-F1 | The task preamble, proposal boundary, and design repeated capture-only wording after implementation. Use past tense for completed phases and the checklist for current status. | 5.1 |
| R2-O1 | `.github/workflows/run-tests.yml:199` sources the downloaded `test_summary.env` while the agent and VPN remain active. Replace execution with strict data parsing and regressions. | 5.2 |

Source comparison confirmed the result-retrieval body unchanged from the
base `d327f2caff9cb0e6ffadb8325defcd948bbaa13f`. The producer at
`webclient/run_tests.py:153` writes two integer assignments. An in-memory Bash
control demonstrated that sourcing such data also executes appended commands;
no live workflow or real credentials were used. R2-O1 retains advisory
`fix-in-pr` status because it predates this change.

## Execution reliability remediation (2026-11-24)

The user approved capture of the following five repairs after investigating
[ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544)
at `65b0f6a8e43298360f323fe61aad71966f1e75c1`, against base
`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`. The subsequent explicit apply
invocation authorized implementation after capture; group 6 records progress.
Earlier completed task groups and usage records remain historical evidence.

| Item | Provenance, evidence at the reviewed head, and repair boundary | Tasks |
| --- | --- | --- |
| REMOTE-STDIN | Introduced in `62146241c`: `run-tests.yml:149-186` changes remote execution from `bash -c` to `bash -s`. The unchanged `deploy_test_server.sh:121` passes inherited stdin into `docker exec -i` and consumes the remaining test commands. Isolate dependency stdin and verify actual dispatch. | 6.1 |
| RESULT-FRESHNESS | Pre-existing: fixed result downloads at `run-tests.yml:196-197` have no attempt identity; early selection exits in `run_tests.py:26-60` can leave old output available. Preserve previous selection input and publish an explicit current-attempt outcome with matching files. | 6.2-6.4 |
| DEPLOY-FAILURES | Pre-existing: `deploy_server.sh:42-63`, `deploy_test_server.sh:74-76,120-139`, and nested deployment helpers can mask failed required operations or update the last successful tag after failure. Preserve child failure statuses through every layer. | 6.5 |
| RUNNER-OUTCOME | Pre-existing: `run_tests.py:117-161` ignores migration/test return codes and infers zero failures from absent output matches. Check process outcomes and complete output, including selection and file-logging paths. | 6.2 |
| STACK-READINESS | Pre-existing: `deploy_test_server.sh:85-95` checks `health=starting` and replica counts, allowing already-unhealthy tasks to pass. Scope checks to required target-stack services and verify actual health and inspection success. | 6.6 |

The last four items retain advisory `fix-in-pr` attribution. Comparing their
source files with the base confirmed they predate the PR; capture does not
reclassify them as introduced findings. The stdin regression remains a
separate introduced defect. No automatic rollback, deployment topology
redesign, production Django feature, database migration, or hub asset change
is included.

Observed evidence is separated from planned verification:

- The linked [DEV job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45288367885/job/138090470675)
  completed green after displaying the unexecuted test-dispatch source during
  database cloning and retrieving existing result files. It is evidence of
  the defect, not acceptance of a repair.
- In-memory probes using the actual remote body reproduced skipped tests in
  all three modes with a stdin-consuming deployment fixture. Deployment-off,
  command-string, and detached-stdin controls reached the test invocation.
- Twelve reference tests, 25 parser probes, 12 argument/status probes, guarded
  inventory regeneration, and upstream pin readback found no additional
  introduced defect in their examined scope. They did not execute live
  deployment or the unchanged child scripts against real services.
- Extracting the existing runner's parsing/outcome statements and supplying a
  startup traceback reproduced `PASSED=0`, `FAILED=0`, and exit status 0.
  Readiness evidence comes from source and Docker's distinct `starting` and
  `unhealthy` states; the expanded repair still needs fixture verification.

## Goals / Non-Goals

Use the contracts in [github-actions-trust](specs/github-actions-trust/spec.md).
Preserve valid workflow inputs and defaults, triggers, job permissions,
publishing behavior, and the existing local reusable-workflow relationship
while changing dependency
selection, SSH-agent setup, and unsafe input handling. Tighten validation
without changing input names/types, valid deployment selection, or test modes.
Pinning does not make downloaded binaries, vulnerability databases, or action
owners inherently trustworthy.

The change's completion boundary is the implementation, documentation, and
verification deliverable in this PR. The post-merge operations below are
documented follow-up, not unfinished implementation tasks or completion gates.

All planning and implementation files are repository-owned local edits.
Generated assistant assets come from the hub baseline named in the proposal
and require no sync. Any later need to modify delivered assets requires
separate hub work, including a dry-run check before any approved sync apply.

## Decisions

### Select current compatible releases and verify their commits

Assess the latest stable release of every retained action, including newer
major releases, against the runners, inputs, outputs, permissions, and behavior
used here. Select it when compatible; explain any necessary older selection
with source-backed compatibility or security reasons. Do not follow an
unreleased branch tip or assume that a moving major tag identifies the newest
release. Include the action release rather than unrelated CLI-bundle releases
when an upstream repository publishes both.

Resolve each selected action release against its upstream repository using
GitHub's refs/commits API or `git ls-remote`. Peel annotated tags to commits;
do not use a tag-object SHA, file blob SHA, guessed hash, or a fork's commit.
For moving major tags, select and record the corresponding full release
version and verify the tag-to-commit relationship. An unresolved relationship
blocks that pin. Preserve action subpaths and reuse the same verified SHA
and version comment for every occurrence of the same release.

Use `@<40-character-commit> # vX.Y.Z`. Tags and abbreviated hashes leave the
dependency mutable or ambiguous; introducing another pinning tool is
unnecessary for this bounded inventory. Keep runtime SHAs in the workflows and
derive the inventory from them. Record concise upstream sources, relevant
findings, and exceptions in change evidence rather than maintaining a separate
JSON snapshot or duplicating all pins in this design.

Perform a bounded security assessment of the selected upstream revisions,
maintenance/ownership signals, transitive action references, and downloaded
tool defaults using upstream source and relevant published advisories. Assess
advisories against the actual configured use; distinguish a database lookup
from a full audit or a demonstrated exploit. Explain material residual risk
and compatibility exceptions alongside this dependency update. This does not
establish a new recurring review procedure.

Keep action-reference parsing and validation in production generation code or
a shared helper, with regression coverage in
`scripts/test_pre_commit_actions_trust.py`, discovered by the existing
CI command `python -m unittest discover -s scripts -p 'test_pre_commit*.py' -v`,
for active workflow references. It must distinguish action steps from job-level reusable
calls, accept the existing `./` call, ignore commented steps, and reject
mutable references, malformed hashes, and missing version comments with a
file/line diagnostic. Fixture mutation tests must prove those failures;
format checks alone cannot prove upstream commit provenance.

Reject duplicate YAML mapping keys before traversing action references,
including duplicate structural keys that would hide jobs or steps. Report
the source file and duplicate location, and leave the inventory untouched
on failure. Retain unambiguous single-action flow mappings, quoted values,
local calls, and commented-step handling. Reject lines where multiple
external calls would claim one trailing release comment. Requiring block
style everywhere would unnecessarily remove syntax already covered by tests.
These checks harden the existing parser rather than add a general YAML linter.

### Match agent lifetime and private-key scope to each SSH workflow

Use native `ssh-agent` and `ssh-add` with fail-fast Bash and CRLF-normalized key
input from a step environment variable. In `run-tests.yml`, persist only
`SSH_AUTH_SOCK` and `SSH_AGENT_PID` through `GITHUB_ENV` for the later SSH and SCP steps. Never
persist the private key or enable shell tracing around it. Add unconditional
cleanup that safely handles initialization failure and stops a created agent.

Preserve known-host verification and the VPN setup. Simply copying
`deployment.yml` would lose the agent environment at the end of the setup
step. Verify the cross-step lifecycle and key-loading failure with isolated
shell execution and a disposable test key; live DEV access remains a
separate post-merge follow-up check.

In `deployment.yml`, move `SSH_PRIVATE_KEY` from job environment to the
existing SSH connection step and consume it as a quoted shell variable.
Capture and evaluate the native agent's environment, then install an EXIT
trap immediately before loading the key. The entire agent lifetime fits
within this step, so a trap handles success and failures without exporting
agent state or adding a separate cleanup step. Cleanup is best-effort and
must preserve the original failure status. Exercise the real setup/cleanup
with a disposable key and stubbed remote operations.

### Keep workflow values out of local and remote script source

Pass manual inputs and workflow reference values through step environment
variables, following GitHub's intermediate-variable guidance. Read the tag
from that environment before applying the existing tag pattern; retain its
Git/image normalization and supported prerelease suffix. Validate test modes
against `vsechny`, `neuspesne`, and `konkretni`, deployment booleans against
`true`/`false`, and every nonempty test number as decimal digits; require a
number for `konkretni`. Complete validation before VPN connection or SSH.

Keep the DEV remote script in a quoted static heredoc, invoked with
`sudo bash -s --` and positional arguments. Construct the remote command
using POSIX shell quoting for each argument, including reference names and
paths, then quote their expansions within the receiving script. Local
double quotes alone do not survive SSH's reconstruction of a remote command;
Bash-only argument escaping also assumes the remote login shell understands
it. POSIX quoting avoids adding that assumption or a new runtime dependency.
Do not evaluate input, concatenate it into the script body, or rely on the
downstream test script's numeric check after assignment has already executed.
Isolate non-interactive deployment and test invocations from the shell's
script input, using explicit stdin redirection at their call boundaries.
Do not restore interpolation into remote script source. A consuming child
fixture must prove that all later test dispatch still executes; an argument
recorder alone is insufficient.

Keep input names, types/defaults, test modes, deployment-source/environment
selection, and valid reference handling. Isolated shell regressions must
exercise both interpretation boundaries with harmless canaries, quotes,
newlines, and literal references, plus the valid all/failed/numbered test
paths. Invalid values must prevent remote work and never execute a canary.
Adapt the existing SSH fixtures to supply valid inputs instead of replacing
every expression with the same generic string. No live dispatch is needed.

### Parse the downloaded result summary without evaluating it

Keep the producer's two-key numeric summary format. The original two-file
retrieval is extended by the current-attempt protocol below; a fixed legacy
file by itself can no longer establish the current run's result.
Use `scripts/collect_test_results.py` and the shared Python standard-library
consumer `webclient/test_run_results.py:read_summary` to read
`test_summary.env` as data, never with `source` or `eval`. Require exactly one `PASSED` and one
`FAILED` assignment containing ASCII decimal digits; reject duplicate or
unknown keys, missing values, executable text, empty records, and NUL bytes.
Support LF/CRLF records and a final record without a terminating newline.
Normalize validated ASCII decimal strings to canonical report counts in
Python without shell evaluation. The round-four repair additionally bounds
the raw summary read to 4097 bytes, rejecting a result larger than 4096 bytes
before decoding or allocating the entire input.

Finish validating the entire file before appending either output or the
human-readable summary. Preserve the Markdown layout, spreadsheet artifact
and failed-test reporting contract. Group 9 moved the failure annotation
into the result report. Group 10 narrows the result step output to
`ARTIFACTS`. The existing `always()` cleanup handles a parse failure after
the SCP clients used the agent.

Extend the existing disposable-key result-step fixtures to deliver arbitrary
summary bytes. Exercise the real shell with valid/zero/failed counts, record
order and line-ending controls, and malformed, duplicate, missing, unknown,
binary, and command-substitution payloads. Invalid input must execute no
canary, leave outputs and summary untouched, fail the step, and still permit
agent cleanup. Document this result-data boundary on the dependency page.
The earlier Bash result-parsing repair needed no producer change. The
execution-reliability extension subsequently replaced that shell parser with
the shared Python consumer and introduced the version-1 outcome protocol.
The round-four implementation below uses explicit version-2 outcome counters while retaining
the two-key numeric summary and adding no third-party runtime dependency or
new workflow.

### Separate current-attempt output from previous selection input

Use a validated execution identity containing the GitHub run ID and run
attempt, transported as quoted data through SSH, the container wrapper, and
the runner. A standalone invocation generates a fresh local identity through
the Python standard library. Reruns receive distinct identities. Give each
attempt its own output directory under the existing test-results volume;
never select a result by an unqualified latest-file glob or timestamp alone.

Keep the previous `results.xlsx` available for failed-only and numbered
selection before preparing new output. Pass the attempt output path through
the test-only output setting so current test output is written separately.
Preserve ordinary standalone defaults and CLI modes. Do not delete the prior
spreadsheet to manufacture freshness, or label its unchanged contents as
newly executed test output. A compatibility copy used by subsequent selection
can be refreshed only from validated completed results.

Retain `test_summary.env` with exactly the two existing count fields. Add a
small, versioned JSON outcome record beside it, using the standard library.
Its schema binds the attempt identity and requested mode/number to the
execution state, subprocess status, and names of the files belonging to that
attempt. Validate expected fields and types, mode/number agreement, allowed
states, and fixed contained artifact paths without evaluating any content.
Only `completed` tests and the intentional failed-only `no-tests` state can
support a successful job; an `error` outcome or nonzero required process
result cannot be overridden by zero counts.

Publish the outcome record last with an atomic replacement after required
outputs have been written and validated. A completed attempt's required
spreadsheet must exist in that attempt's directory; a failed workbook write
cannot publish a successful bundle. A legitimate no-op explicitly records
that it produced no new spreadsheet. Readers never combine a new summary
with an older spreadsheet or accept a partial directory as complete. An
execution error may retain its own diagnostic outcome without presenting a
successful completion or invented passing counts.

Update producer and consumer together. Retrieve the expected attempt's
outcome and named files, validate the bundle before publishing results, and
retain matching diagnostics when tests complete unsuccessfully. Arrange the
retrieval/artifact conditions so an earlier failed test step does not hide
its current diagnostics; preserve the original failure and always cleanup.
Missing outcome/files, legacy-only data, identity mismatch, or an interrupted
publication fails closed rather than falling back to old files.

### Derive runner outcomes from complete execution

Check migration status before starting tests. Retain reader thread objects,
drain both streams, and join the readers before interpreting results in both
console and file-logging modes. Use subprocess status together with a complete
consistent test summary; missing output, a startup traceback, capture failure,
or disagreement cannot become a passing zero-count result. A normal execution
must run tests. Completed failing tests can publish current diagnostic results
while preserving their nonzero outcome.

Resolve failed-only and numbered selection explicitly. Missing, unreadable,
or malformed selection input and an unknown number fail with a current
diagnostic outcome. A readable failed-only selection with no failures is the
sole intentional zero-execution success and publishes a new `no-tests` outcome.
This preserves the useful no-op without confusing it with a crash or skipped
invocation. The previous numeric summary remains a count format, not proof
that an execution completed.

### Propagate required failures through the deployment chain

Handle required command statuses in `test_deploy.sh`, `prod_deploy.sh`, and
their CI wrappers. An `er` helper returning nonzero is ineffective if its
caller ignores it or later unconditionally exits zero. Guard required build,
pull, removal, rollout, and database-clone operations explicitly and stop their
dependents. Do not rely solely on a parent workflow's `set -e`: child scripts
and conditional command lists can lose the original status.

Preserve the child exit result through container and terminal wrappers,
including `script --return` when retaining the PTY wrapper, and detach their
stdin. Keep expected absent-stack cleanup and explicitly optional maintenance
as named successful/warning cases. A required readiness failure returns
nonzero; write the last-successful-deployment record only after required
deployment checks and preparation succeed. A test failure does not erase a
successful deployment record, and reporting/cleanup must not hide either
operation's actual outcome. This does not implement automatic rollback.

### Verify actual target-stack readiness

Inspect the required services and active tasks of `swarm_webamcr`, using the
existing compose/stack definitions for the expected service inventory rather
than assuming that an empty service listing is ready. Check required replica
counts and applicable container health states; both `starting` and `unhealthy`
are unready. Inspect command failures explicitly, including failures inside
pipelines and command substitutions. Do not infer readiness from a formatted
line count or from absence of `health=starting` output.

Keep the existing bounded wait, with unsuccessful completion at its deadline
and diagnostics scoped to the target stack. Intentionally zero-scaled services
and expected completed one-shot jobs are explicit exceptions, not missing
required active services. Unrelated containers on the host must not block
this deployment. Apply the same required-readiness contract to both CI
deployment wrappers; no new deployment service or polling daemon is needed.

### Retain the SHA-pinned scanner and signer integrations

The operator selected retention of both wrappers with full SHA pins and
documented trust reviews on 2026-11-22. Preserve the existing image-scanning
and signing behavior. Replacing them would add ownership of binary installation,
verification, upgrades, and output compatibility to this repository.

Source inspection supports the comparison: Trivy's `v0.36.0` manifest pins
its setup and cache actions to full SHAs; the Cosign `v4.1.3` installer
embeds bootstrap checksums and verification logic. These are observations
about those release files, not a full security review. Reassess the releases
selected for this update, including their nested actions and tool defaults;
the action wrapper's release number is not the downloaded executable's version.
Trivy's selected wrapper defaults to CLI `0.70.0`, for which exploration found
published advisories. The repository was not found to configure the affected
artifact overrides, plugin installation, or misconfiguration scans; this is a
bounded exposure observation, not a safe-version guarantee. Resolve the
selected tool/version and any relevant exception within the update assessment.
Do not assume Dependabot tracks arbitrary `with: version` inputs or introduce
a separately maintained override without a demonstrated need. Retain trust
in downloaded tools and network services as an explicit residual.

### Generate the inventory through existing dependency documentation tooling

Create `docs/source/12_zavislosti/github_actions.rst` and link it from that
directory's `index.rst`. Use the documentation's existing Czech language.
Extend `docs/generate_module_docs.py`, which already generates Docker and
JavaScript dependency documentation, to derive a marked inventory section
from active workflow references. Include GitHub-owned and third-party action
paths, upstream owners/source links, release comments, full commits, and
workflow locations. Preserve distinct versions if the same action is used at
different releases; ignore local calls and commented-out steps. Use the same
parser for generation and validation, not an operational parser hidden inside
a test module.

The existing `generate-module-docs` pre-commit hook invokes this generation
with the other dependency tables. Use deterministic ordering, no network or
credentials, and the generator's existing changed-file behavior. Refresh
additions, removals, and version changes while preserving authored rationale
and instructions outside the generated section; a second run must be clean.
Generating rows establishes inventory freshness, not a security-review date
or automatically verified maintenance status.

Keep concise authored owner/exposure/retention rationale for each retained
third-party action, especially Trivy and Cosign. Remove the manual version
list, quarterly cadence, separate review-date fields, and routine Actions-only
review requirements. Relevant pin-resolution and exceptional upgrade
instructions remain useful; ordinary dependency PR review already supplies
human review. Keep policy readiness, activation, and recovery instructions
durable: describe prerequisites and operations without reporting completion
of this particular PR.

Remove `.agents/analysis/github-actions-trust.json` after inspecting its exact
contents and confirming it has no consumers. Remove links to it from the page
and rolling usage entry, retaining useful concise source-backed conclusions
in the change evidence. It is a one-off snapshot, not required runtime input,
an inventory source, or permanent metadata configuration.

Place generation regression tests under `scripts/`, following
`scripts/test_generate_js_libraries.py`, and include them in the existing CI
test job. Test changed workflow inventories, invalid references, authored
section preservation, and idempotency with isolated fixtures. Existing
workflow/SSH tests stay in the same test suite. A separate maintenance workflow
or a pre-commit hook whose only purpose is running this test suite is unnecessary.

Define complete expected rows independently in isolated fixtures containing
both step actions and job-level external reusable workflows, as well as local
and commented calls. Compare exact rows, including versions, commits, and
locations, so omitted and unexpected entries fail. Reusing the production
traversal to derive expectations would allow the same omission on both sides.
Keep the real-repository stale-inventory refresh check compatible with CI's
existing test-before-generation order.

Update CONTRIBUTING's local discovery to `test_generate_*.py`, matching CI.
Describe the DEV result-retrieval step and its current-attempt files,
and cleanup as the unconditional step after agent use, followed by VPN/result
steps. Do not impose an inaccurate final-step guarantee.

### Use normal dependency maintenance and refresh points

Keep the existing ecosystem, schedule, target branch, and update groups.
Change `.github/dependabot.yml` only if a reproduced compatibility issue
requires it. Local tests can check the pin/comment format and configuration;
they cannot establish that Dependabot has opened an update PR.

Use the existing human review and dependency-documentation refresh process.
The current pre-commit workflow excludes Dependabot and other bot source
branches; preserve that boundary rather than adding an Actions-specific bot
mode or exposing privileged autofix steps. The inventory refreshes when the
existing pre-commit/documentation generation runs, including the established
release refresh. Consequently, a fresh inventory is not promised in the
initial Dependabot diff. No separate schedule, trust-review checklist,
recurring review-date update, or special approval is required for an ordinary
Actions dependency update.

As follow-up after rollout to `test`, capture a real Dependabot PR URL and its
diff showing both SHA and version-comment updates, including applicable
grouping. If no new release is available, that issue-level observation remains
pending; it does not block this change or justify deliberately introducing
an obsolete production dependency.

### Selected-release assessment (2026-11-22)

The refreshed upstream Releases and tag/commit API reads identify the existing
pins as the latest stable action releases for 15 of the 16 retained action
paths. Select Docker Scout `v1.30.0` instead of `v1.28.0`; their action manifests
are identical, including all inputs and the Node 24 runtime. All 32 configured
external calls use inputs present in their selected upstream manifests. The
JavaScript actions use Node 24 on the existing `ubuntu-latest` runners. No
major-version compatibility exception was needed. These checks establish
manifest compatibility, not hosted execution.

Full release tags resolve to the selected upstream commits; annotated tags
for GitHub Script, CodeQL, and Trivy were peeled to commits. CodeQL selection
uses the action release `v4.39.4`, excluding separately published CLI bundles.
The generated inventory links each selected release and commit back to its
upstream source. Docker Scout's release notes include vulnerability fixes;
other retained action selections remain unchanged from the first local pins.

The 16 upstream repositories are unarchived and have published releases. The
reviewed GitHub Advisory Database lookup returned no active matches for the
selected action versions, inspected nested action versions, or Cosign CLI
`3.1.4`. Trivy/setup-trivy and provenance/attest composite manifests use full
commit references; their inspected JavaScript dependencies also use Node 24.
These checks cover manifests, configured inputs and known published advisories,
not all bundled JavaScript, binary dependencies, or an independent source audit.

Retain the Trivy wrapper's CLI `0.70.0` default for the configured SBOM and
vulnerability image scans. Its three known advisories concern attacker-directed
OCI artifact repositories, installation of malicious plugins, and Helm archive
misconfiguration scanning. The first advisory excludes the default Aqua
repositories; the tracked calls set neither alternate artifact repositories,
plugin installation nor misconfiguration scanning. The configured exposure
therefore does not demonstrate a need for a separate CLI-version override.
This accepts the upstream-default tool dependency for these calls, not the
affected CLI as generally safe. A change to those inputs can change the risk;
normal dependency review remains the place to explain relevant constraints.
The advisory sources and fixed-version ranges are linked below. No independent
manual tool-pin maintenance process is introduced.

## CI portability and runner diagnostic remediation (2026-11-24)

The user approved capture and implementation of both findings after
`5ae9cf45c14e4ddb609c3f20991d42dd428b0e6a` was pushed. Group 7 records this
renewed scope; earlier completion counts remain dated local evidence.

| Item | Verified evidence and bounded repair | Tasks |
| --- | --- | --- |
| CI-EXECUTABLE-STUBS | [Job 138377173853](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45374557884/job/138377173853) reports nine failures and three errors in the combined fixture. `shutil.copyfile` copies executable stubs as non-executable files on Linux, allowing real host tools to be selected. Preserve their modes, check shell command resolution before execution, and assert each failure's intended stage and current outcome. | 7.1 |
| RUNNER-DIAGNOSTICS | [CodeQL alert 7461](https://github.com/ARUP-CAS/aiscr-webamcr/security/code-scanning/7461), linked by [the review discussion](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4678598669), traces `TEST_SCREENSHOT_PATH` from secret-backed settings to the runner's directory print. Raw exception text is also printed and stored in `outcome.json`. Use validated attempt identifiers and fixed failure stages in runner-owned diagnostics; protect error publication against a second exception. | 7.2 |

Use permission-preserving copies for the four borrowed command stubs. Before
any combined workflow operation, verify every operational command resolves to
the fixture directory, including inside its emulated remote shell. A missing,
non-executable, or shadowed stub must stop before a real operational command.
Assert successful preparation before deliberately corrupting output fixtures;
negative cases must identify the expected stage, outcome, or command trace.
Keep the real disposable SSH agent and actual production scripts in the test.

The runner may log the validated attempt identity, state, and fixed stages
such as selection, migration, execution, summary, and publication. Do not print
the configured output root or interpolate caught exception text into stderr
or outcome metadata. If publishing an error outcome itself fails, emit a
fixed publication diagnostic and return nonzero without an uncaught traceback.
This concerns diagnostics authored by the runner, not filtering arbitrary
child test output or changing the outcome schema or artifact paths.

Add synthetic sensitive-path and exception canaries covering normal output,
errors before/after attempt creation, selection, migration, execution,
publication, and failed error publication. Preserve native result status,
current-attempt identity, explicit no-op, and prior selection semantics.
Run the existing suites on Windows and in an isolated local Linux environment,
using only synthetic service/process fixtures. Do not use a successful Windows
run as Linux acceptance. Hosted pre-commit and CodeQL closure remain follow-up
after authorized delivery; do not dismiss the alert to manufacture closure.

The existing proposal, design, capability delta, tasks, focused test files,
runner, authored dependency guidance, generated documentation, and one new
usage entry are repository-owned. No delivered hub asset or sync is involved.

## Round-four review remediation (2026-11-24)

This capture follows the [round-four review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6043320852)
of [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544)
at head `09d4d12e1acf64a6c0276f3af3c549bf6c957f9d`, against
`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`. The user initially approved capture.
The subsequent explicit `openspec-apply-change` invocation authorized its implementation.
The seven finding labels below follow the published review's order; the
`R4-` prefix distinguishes them and its O1-O8 observations from earlier rounds.
The review's Medium/Low labels and pre-existing advisory attribution are
preserved without making a new verdict. Source O4 proposed `fix-in-pr`;
the agreed local disposition is no change for the reasons recorded below.

| Item and source | Disposition, evidence and bounded response | Tasks |
| --- | --- | --- |
| [R4-F1, Medium](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219614) | Repair introduced cleanup regression: the workbook-write raise at `test_selenium.py:1013` bypasses driver and base teardown. Register driver cleanup immediately after creation and ensure teardown errors still propagate. | 8.1 |
| [R4-F2, Medium](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219634) | Repair introduced accumulation: persistent `runs/<identity>` holds screenshots, workbooks and logs with no pruning. Apply the ten-finished-attempt and thirty-day interrupted-attempt policy safely. | 8.2 |
| [R4-F3, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219643) | Repair diagnostic regression: `set -e` exits at bare `docker node ls` before the intended Swarm precondition message. Guard the command explicitly in both deployment entry points. | 8.5 |
| [R4-F4, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219655) | Bound `read_summary` input before allocation; its current `read_bytes()` reads everything before checking the 4096-byte limit. | 8.4 |
| [R4-F5, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219668) | Corrected the active parser description in this capture to name the Python consumer. Keep final design and dependency guidance aligned with the implemented counter/retention changes. | 8.9 |
| [R4-F6, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219677) | Replace the deployment fixture's fixed Windows Git path with existing Git-relative Bash discovery and its PATH fallback. | 8.8 |
| [R4-F7, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219689) | Share the byte-identical SSH quoting/argument-construction helper used by the two SSH workflows; preserve both shell boundaries and current lifecycle tests. | 8.6 |
| [R4-O1](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683220448) | Advisory `fix-in-pr`: run-global error/failure list lengths already existed in the base. Classify the current workbook row by this test's membership in those lists. | 8.1 |
| [R4-O2](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219700) | Advisory `fix-in-pr`: skipped/expected-failure outcomes already inflate passes in the base. Add explicit counter accounting across the runner, outcome, validation and report. | 8.3 |
| [R4-O3](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683220755) | Advisory `fix-in-pr`: base cleanup matches the new timestamp's exact log name with an old-age predicate. Rotate only owned `deployment_*.log` files in the deployment log directory, preserving the current log and unrelated files. | 8.5 |
| [R4-O4](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219711) | No change: the all flag exists in the base and currently requests the default `vsechny` mode; argparse also enforces mutual exclusion. Read-only probes of no flag, `-a` and `--all` selected the same intended mode. Preserve this compatibility rather than remove the option. | Disposition only; guard in 8.3/8.10 |
| [R4-O5](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219716) | Advisory `fix-in-pr`: remove the base's unused `last_deployment_tag` reads. Preserve writes of `last_deployment_tag.txt` after successful deployment; the existing capability requires that record. Do not add rollback behavior. | 8.5 |
| [R4-O6](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683221036) | Advisory `fix-in-pr`: remove the base's unused `date_stamp` write to `GITHUB_ENV`; no later step consumes it. | 8.6 |
| [R4-O7](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683221381) | Advisory `fix-in-pr`: different test/deployment concurrency groups already share the DEV checkout and stack. Give DEV operations one group with active cancellation disabled; keep TEST deployment independent. | 8.7 |
| [R4-O8](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4683219723) | Advisory `fix-in-pr`: consolidate the repeated `er`, network/stack checks and wrapper log/tag scaffolding in repository-owned shell helpers. Preserve required failure and bookkeeping behavior. | 8.5 |

Read-only exploration used the actual `tearDown` AST with in-memory
dependencies to reproduce skipped cleanup after a workbook-write exception
and a later assertion failure being labelled ERROR after another test's error.
The current parser returned `(2, 0)` for two skipped tests and `(1, 0)` for one
expected failure. The combined producer/consumer contract, not only the
arithmetic expression, therefore needs adjustment. Base-source checks support
the advisory provenance; equality checks confirmed the duplicated helpers.
The earlier CodeQL thread is platform-resolved and outdated at this head.
Those read-only observations did not establish a DEV reproduction of the full
timeout or disk-exhaustion scenario. The subsequent implementation's local
fixture and validation results are recorded in the round-four usage entry;
fresh hosted and live acceptance remain separate follow-up.

### Selenium lifecycle and individual results

Register cleanup immediately after a remote or local driver is successfully
created, before later driver setup can fail. Guarantee driver cleanup and
applicable base teardown when workbook reading/writing or another teardown
operation raises, while preserving the original failure. Avoid duplicate
driver shutdown on the normal path. Workbook classification must use the
current test's error/failure membership, not accumulated run-global lists.
Exercise both driver types and the actual lifecycle code with isolated
fixtures; do not require live Selenium, databases or Fedora for these controls.

### Retain ten finished attempts and thirty days of interrupted evidence

The user chose ten finished attempts, including failed runs, and then chose a
month for interrupted evidence, confirmed as thirty days in the capture offer.
Treat valid terminal outcomes (`completed`, `error`, `no-tests`) as finished;
retain the ten newest by completion marker time with a deterministic tie-break.
Active/current attempts are protected even when an outcome has been written.
The root-level selection workbook is outside the pruning set.

For an attempt without a terminal outcome, retain at least thirty days since
its last recorded activity. Cleanup after that threshold also requires verified
inactivity. Establish an ownership/lease or lock that works for standalone and
container execution; age or a PID observed in another namespace alone cannot
establish inactivity. If ownership cannot be established, preserve the evidence
and report the uncertainty. Prune only owned direct children of the configured
`runs/` directory after validating identity, literal boundaries and symlinks or
reparse points; never follow a candidate outside that directory. Protect
unrelated files and any active lease throughout candidate selection/deletion.

Apply retention to normal, failed and no-op runs, including standalone use.
Pruning after terminal publication must leave no more than ten eligible
finished attempts; preparation also handles eligible stale interrupted output.
Recognize finished version-1 records for retention during rollout without
accepting their old counts as a new version-2 result. Required cleanup errors
remain explicit failures without widening deletion scope or replacing an
earlier test failure. Validate deletion with owned temporary fixtures, external
canaries and exact age/count boundaries; this capture authorizes no live cleanup.

### Distinguish passes, skips and expected failures end to end

Keep `test_summary.env` limited to the existing `PASSED` and `FAILED` keys.
`PASSED` counts actual successful test bodies; `FAILED` counts unexpected
failures, errors and unexpected successes. Report skipped and expected-failure
counts separately. Evolve the strict outcome to version 2 with explicit total,
passed, failed, skipped and expected-failure metadata, checked against the
two-key summary and process result before publishing any report or output.
Use native integer type/range and consistency checks; booleans and malformed
or contradictory counters are not valid counts.

An executed expected-failure-only run can complete successfully with zero
passes and zero unexpected failures when its explicit counters establish
actual execution. An ordinary all-skipped/zero-execution run remains an error;
it cannot impersonate the intentional failed-only `no-tests` outcome. Keep
that selection no-op and missing/incomplete summary failures unchanged. Deliver
producer and consumer together and reject unsupported/mixed outcome versions
without a legacy-count fallback. This resolves the current bundle validator's
rejection of completed `0/0` instead of creating a second regression while
correcting the pass arithmetic. Preserve the no-flag, `-a`, `--all`, failed-only
and numbered-test CLI behavior.

### Shared helpers, diagnostics and DEV serialization

Use repository-owned sourced shell helpers for the existing repeated
deployment behavior, and one shared SSH quoting/argument-construction path
consumed by both workflow SSH steps. Resolve helpers from the correct local
checkout or entry-point location, include their dependency closure in fixtures,
and exercise the actual shared code in both callers. Do not substitute a new
composite action, dependency, deployment service or privileged workflow.
Keep static remote bodies, safe quoted arguments, native-agent cleanup,
stdin detachment, required child statuses and readiness contracts intact.

Guard the Swarm precondition explicitly so its operator message runs before a
nonzero exit. Share wrapper log initialization and rotation without removing
the last-successful-tag output: delete only eligible old `deployment_*.log`
files in that log directory under the existing age policy, protect the current
log, and remove unused prior-tag reads. Remove the unused workflow `date_stamp`
environment write. Preserve optional-compaction warnings and avoid rollback.

Give DEV tests and DEV deployments one concurrency group with
`cancel-in-progress: false`, including deployment-disabled tests because they
still use the shared stack. TEST deployment must use a separate group. Do not
promise FIFO delivery or preservation of every pending run beyond GitHub's
configured concurrency semantics. Validate the group expressions and
cancellation settings without dispatching either workflow.

Reuse Git-relative Bash discovery with the existing PATH fallback for
regression processes. Cover a non-default Windows Git installation, fallback
and unavailable-shell diagnostics; do not confuse the WSL launcher with Git
Bash. Keep existing CI discovery and avoid duplicate test collection when
sharing discovery code. Refresh generated documentation only with its existing
generators and keep authored dependency guidance operational, not PR-specific.

The initial capture changed only the four existing planning artifacts and one
rolling usage entry. The subsequent apply instruction authorized the captured
implementation. Shared helpers are repository-owned under `scripts/` and the
existing result/test areas; no
delivered assistant asset or hub sync is needed. The prior 34 completed tasks
remain historical evidence. Group 8 records current implementation progress;
commits, pushes, thread replies/resolution, live operations, sync and archive
require separate authorization.

## Round-five review capture (2026-11-25)

The [round-five review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6049994746)
compares `d90182be3893880e6f9d9e4c4a89591180b202e7` with `test`
(`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`). It confirms the fourteen
round-four repairs and records R4-O4 as unchanged. GitHub reported success
for [pre-commit](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45483796675)
and [CodeQL](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45483783871)
on the reviewed commit. The earlier CodeQL alert thread remains resolved.
Those results describe the reviewed commit. The user approved capture on
2026-11-25 and subsequently invoked `openspec-apply-change` for group 9.

| Review item | Agreed disposition | Task |
| --- | --- | --- |
| [R5-F1, Medium](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801621) | Source the runner-side SSH helper from the workflow commit so a valid pre-helper deployment tag can reach SSH. Keep the remote deployment on the requested tag. | 9.1 |
| [R5-F2, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801631) | Reject a duplicate explicit attempt identity before pruning can remove the existing attempt. | 9.2 |
| [R5-F3, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801636) | Acquire a valid lease before exposing a new attempt directory. Preserve and report existing candidates with uncertain ownership. Age alone does not change eligibility. | 9.2 |
| [R5-F4, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801645) | Document which server wrapper and container runner must be in place before the deployment-disabled DEV control can verify outcome v2. | 9.7 |
| [R5-F5, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801652) | Emit an annotation for a validated positive failure count in the result report and remove the unreachable downstream gate. | 9.4 |
| [R5-F6, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801654) | Share one bounded and duplicate-key-rejecting outcome reader. Retention validates the single parsed object. | 9.3 |
| [R5-F7, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801659) | Require exactly one Docker stub replacement and stop fixture setup when the expected fragment changes. | 9.6 |
| [R5-O9, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688801976) | `fix-in-pr`. Remove the pre-existing `tag_passed`, `msg_pull_success`, and unreachable `d` option branch in `prod_deploy.sh`. | 9.5 |
| [R5-O10, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4688802118) | `fix-in-pr`. Share the stack removal status mapping between the two deployment entry points. | 9.5 |

### Keep the workflow checkout and deployment target distinct

The job currently sources `scripts/ssh_arguments.sh` after checking out the
selected tag. The local Git trees for `v1.4.0`, `v2.0.0-alpha.1` and
`v2.0.0-alpha.2` contain their own server wrapper and VPN config and lack that
helper. Under fail-fast shell options this prevents SSH. Keep the existing
release checkout for its tag validation and files. Use a separate, read-only
checkout with the existing pinned checkout action and `github.workflow_sha`
for the helper. Source from its fixed local path. The remote shell continues
to check out and execute the exact requested tag with its own entry point.
This restores the manual release selection path, including rollback by
choosing an earlier tag. The workflow does not perform automatic rollback.
Exercise the actual SSH step with separate fixture trees for the workflow
helper and a pre-helper tag. Use only stubbed transport and server commands.
Regenerate affected workflow-reference locations through the existing
generator.

### Reserve attempt ownership before exposing results

Under the root retention lock, validate the requested identity and reject
any existing attempt at that path before a prune can run. This makes name
collision behavior independent of the age or terminal state of the attempt.
Resolve and reserve the identity and acquire its valid per-attempt lease
before creating the visible results directory. Keep it held while the
runner writes and publishes. Handle failures during creation without
adopting unknown markers or leaving an unleased visible attempt.

The thirty-day rule still applies only when ownership and inactivity can
be verified. Legacy interrupted attempts with missing leases and candidates
with invalid leases remain protected and reported, even after thirty days.
The count limit still applies to eligible finished attempts. Retention
may recognize valid historical v1 terminal outcomes under the existing
ownership rules. Use one bounded, strict JSON decoding path for both
retention and results, and check the parsed record once in retention using
the directory identity and its recorded selection. Consumer validation
continues to require a current v2 outcome and matching bundle. Cover
duplicate identities outside the retention window, interrupted creation,
old uncertain evidence, and bad or oversized outcome records.

### Report the failure at the point of validation

Publish the verified failed count, applicable artifacts and Markdown summary
as before. Emit the failed-tests annotation from the report when a validated
completed outcome has a positive failed count, and keep its nonzero return
status. Remove the downstream success-gated annotation step. An invalid
bundle or an execution error without verified counts must not emit a
failed-count annotation. Verify that artifact upload and unconditional
agent and VPN cleanup still run in the appropriate failure paths.

### Keep the advisory repairs and fixtures narrow

The legacy production option assignments and the duplicated removal path are
pre-existing. Remove the dead assignments and unreachable option alone.
Move the common stack removal operation and status mapping to the existing
helper. An absent stack is an allowed removal no-op. Inspection and removal
failures still propagate. Leave the entry points responsible for their own
ordering and wait behavior. Keep the combined fixture on real workflow
shell and isolated stubs, and abort setup if the intended unique edit of the
Docker stub cannot be applied.

### DEV control and validation

A deployment-disabled control uses the DEV checkout's existing launcher
and the code inside its running web container. After promotion, verify both
support the v2 protocol before attempting that control. On an older stack,
wait for the compatible rollout or obtain separate approval for a
deployment-enabled control first. Record the deployed revision, workflow
revision and matching attempt evidence for each authorized run. Tests use
offline fixtures, and no legacy-format fallback is planned.

Validate the targeted paths and the existing Windows and isolated Linux
regression suites, compilation, pre-commit, affected documentation and
OpenSpec. Implementation and generated documentation belong to this
repository. The group 9 apply invocation covers this implementation and local
validation. Live operations, review-thread writes, delivery, hub sync and
archive require separate authorization.

## Round-six review capture (2026-11-25)

The [round-six review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6053375832)
at `5dc50a8797e184f8c11b06746bb6939526bff4db` compares the PR with
`test` (`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`). It confirms all nine
round-five repairs and records the earlier round-four and CodeQL threads
as resolved. After the review was gathered, hosted
[pre-commit](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45531908215)
and [CodeQL](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45531903494)
passed for this head. The user approved capture and subsequently invoked
`openspec-apply-change` for group 10.

| Review item | Agreed disposition | Task |
| --- | --- | --- |
| [R6-F1, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691616888) | Publish a complete retention root-lock marker with an atomic create-if-absent operation. Concurrent callers reuse the winning lock. | 10.1 |
| [R6-F2, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691616898) | Store the download plan outside the artifact directory and clean it up after retrieval. | 10.2 |
| [R6-F3, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691616903) | Document that an older tag retains its own deploy and failure behavior, including limitations of a green workflow and of the last-success marker. | 10.3 |
| [R6-F4, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691616906) | Narrow the internal step outputs to `ARTIFACTS`. Retain validated state and counts in the report and outcome data. | 10.4 |
| [R6-F5, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691616909) | Share the exactly-one web container lookup between DEV database cloning and test launch. | 10.5 |
| [R6-O11, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4691617174) | `fix-in-pr`. Reject unsupported test-deployment options, including `-t`, `-d` and `-u`, without Docker side effects. Preserve the supported modes. | 10.6 |

### Initialize one stable retention root lock

The current exclusive open publishes an empty file before the creator
writes and syncs its marker. A second caller can open that file and acquire
its lock before the marker is present. Initialize a unique temporary
marker in the same filesystem, then publish it atomically if the canonical
root lock is absent. A concurrent caller opens the winner. Never replace
an already-visible lock, since an existing file descriptor may still hold
the lock on it. Clean up temporary initialization data where ownership is
known. Retain fail-closed handling for invalid or redirected canonical
markers and preserve per-attempt ownership, pruning and diagnostics.
Exercise simultaneous starting processes against a fresh root using
isolated fixtures and deterministic synchronization.

### Keep retrieval data outside the verified bundle

Write the validated filename plan to a unique runner-owned temporary file
outside the upload directory. Remove it on success and failure. The artifact
contains the current outcome and only its verified, allowlisted files. The
report step still validates the complete bundle before signaling artifact
eligibility. It preserves the native failure status, failure annotation
and unconditional cleanup.

Only `steps.test-result.outputs.ARTIFACTS` has a workflow consumer. Retire
the unused `STATE`, `PASSED`, `FAILED`, `SKIPPED` and `EXPECTED_FAILURES`
step outputs. This narrows the earlier step-output contract. State and
validated counts remain available through the report and applicable outcome
and summary files. Update regressions to assert published results through
those channels. Preserve the distinction among a completed result, an
allowed no-op and an execution error.

### Keep old-tag and container selection behavior explicit

The workflow revision supplies the SSH helper. The selected release tag
continues to supply the remote deployment wrapper. The local `v1.4.0`
wrapper can report a failed readiness check yet still write
`last_deployment_tag.txt` and return success. Document that a green run for
such a tag needs independent verification of the actual deployed version,
stack health and readiness. Preserve older tag selection and treat live
verification as a separately authorized operation.

Use a shared repository helper for the Swarm service filter and the
nonempty, single-container requirement. The DEV deployment wrapper and
standalone test launcher each resolve the current container when their
operation runs. This keeps the selection rule consistent without binding
both operations to one container ID across possible Docker replacement.
Preserve the existing command and status propagation for each caller.

### Reject unsupported options without retiring working modes

Git history identifies
[`b88874461`](https://github.com/ARUP-CAS/aiscr-webamcr/commit/b88874461c8e378aebab7adf3ee08f452de5bb9d)
as the creation of `test_deploy.sh` in June 2024. Its production ancestor
had image-tag selection, service update and database Compose modes. The
new test script inherited the `getopts` letters without those handlers.
An in-memory Bash probe of the actual option block at the PR base,
previous reviewed head and current head returned zero without dispatching
an action for `-t 1.4.0`, `-d` and `-u`. The same probe reached the
intended stub for each documented mode. The earlier production O9 repair
removed an unreachable preliminary `d` alternative. Production
`-t`/`-u` and Selenium's numbered-test `-t` remain separate working modes.

Validate the test deployment request before Swarm inspection, image pruning
or action dispatch. Report unsupported options and return nonzero, even
when combined with a valid option. Removing letters alone still takes the
success-returning invalid-option branch. Keep default and `-b` deployment,
quiet `-q`, removal `-x`, help `-h` and existing valid operation order.
Test the entry points with isolated stubs rather than running deployment.

Implementation belongs to the existing repository workflows, scripts,
tests and documentation. The four planning artifacts and one rolling
usage entry cover this capture. The 52 earlier task descriptions are
preserved. The group 10 apply invocation covers implementation and local
validation. Delivery, live operations and review-thread writes require
separate authorization.

## Round-seven review capture (2026-11-25)

The [round-seven review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6061348584)
examined `244db4ac53d6eb249ae002d5345006e59f70a3e0` against `test`
(`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`) and confirmed all six
round-six repairs. Hosted
[pre-commit](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45618950961/job/139221674405)
and [CodeQL](https://github.com/ARUP-CAS/aiscr-webamcr/runs/139221977213)
passed on the reviewed commit, along with the other hosted checks.

| Review item | Agreed disposition | Task |
| --- | --- | --- |
| [R7-F1, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4697868828) | Use atomic publication for per-attempt markers, including legacy backfill, so an interrupted initialization cannot strand an explicit attempt ID. | 11.1 |
| [R7-O12, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4697868849) | `fix-in-pr`. Return test deployment help after validating the whole request and before setup or Docker operations. | 11.2 |
| [R7-O13, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4697869269) | `fix-in-pr`. Reject invalid production requests before dispatch with nonzero status, and apply the same early help handling. | 11.3 |

### Publish complete per-attempt lease markers

Both new attempt creation and verified v1 terminal metadata backfill can
publish the canonical marker before writing it. A write failure or process
interruption can leave an empty marker, which blocks reuse of an explicit ID
even when no attempt directory was published. Normal CI uses distinct IDs.
Reuse the root lock's same-directory temporary file, sync and atomic
create-if-absent operation for both lease creation paths. Open the canonical
file after publication, and acquire and validate it before making the attempt
directory visible. An interrupted creator can leave a complete unclaimed
marker that a later caller can acquire. An existing invalid or redirected
marker still fails closed. Existing leases, retention limits, and pruning
eligibility retain their current protections.

### Validate both deployment requests before dispatch

Both advisories are visible at the PR base. Test deployment validates options
early, but dispatches help after the Swarm check and image pruning. Production
deployment's preliminary pass ignores unknown switches, and the later error
branch exits zero. A valid operation earlier in a mixed request can already
have executed by the time that branch runs.

Validate the entire request, including production source selection, trailing
operands, and required tag arguments, before setup or action dispatch. Emit a
diagnostic and return nonzero for invalid requests. After validation, help
takes precedence over any other valid mode and exits zero before Docker,
network operations, or log and backup setup. Retain test default, build,
quiet and removal modes, production no-argument guidance, removal, tagged
deployment, tagged update and tag listing, and the existing ordering and
tag and registry selection for valid operational requests.

The user approved capture and then invoked `openspec-apply-change` for these
three dispositions. Group 11 records the work in the repository-owned
runner, scripts, tests and affected documentation. Delivery, live
operations and review-thread writes retain their separate approvals.

## Round-eight review capture (2026-11-26)

The [round-eight review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6066800751)
examined `0bae037a92d767c2025f9b08f37ca53a643fbbae` against `test`
(`d327f2caff9cb0e6ffadb8325defcd948bbaa13f`). All three round-seven
threads are resolved and all six hosted checks passed on this head, including
[pre-commit](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45694687919/job/139488885994)
and [CodeQL](https://github.com/ARUP-CAS/aiscr-webamcr/runs/139489165124).

| Review item | Agreed disposition | Task |
| --- | --- | --- |
| [R8-F1, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4702411261) | Align the deployment overview, workflow walkthrough and command examples with tagged deployment and the actual registry selection. | 12.1 |
| [R8-F2, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4702411269) | Describe atomic publication for the root lock, new attempt markers and eligible legacy backfill. | 12.2 |
| [R8-F3, Low](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4702411271) | Correct the Selenium launch log, per-attempt results, root selection workbook and interactive update branch. | 12.3 |
| [R8-O14, advisory](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#discussion_r4702411415) | `fix-in-pr`. Remove the unused `ask_continue` definition from the standalone test deployment script. | 12.4 |

### Reconcile deployment instructions with the entry points

In `docs/source/02_instalace_nasazeni/nasazovani.rst`, describe release
image publication to both registries and the separate manual deployment
workflow. The workflow dispatch selects an environment, release tag and
source. It calls `scripts/ci_deployment/deploy_server.sh` from the selected
tag and passes the selected source and image tag. Reflect that dispatch
and the GitHub Container Registry default in the overview and walkthrough.
Use `./scripts/prod_deploy.sh -t <tag>` for the default manual invocation
and `./scripts/prod_deploy.sh dockerhub -t <tag>` for Docker Hub. Reconcile
the section heading, table, examples and summary with those two routes.
Retain the existing explanation of bare-command guidance and help.

### Explain lease publication and locate Selenium evidence

In the authored retention narrative of
`docs/source/12_zavislosti/github_actions.rst`, explain that the canonical
root, new attempt and eligible legacy v1 lease markers are published
atomically after a complete marker is written and synced. Publication
preserves any existing marker.

In the authored launch section of
`docs/source/09_testovani/selenium_testy.rst`, describe the interactive
update to `origin/main` and the background wrapper's
`/opt/selenium_test/run.log`. Point operators to
`/opt/selenium_test/runs/<attempt>/` for the runner's `test_output.log`,
workbook and screenshots when produced. Describe the root
`/opt/selenium_test/results.xlsx` as the rolling selection input.

### Remove the unused test deployment prompt helper

The `ask_continue` definition in `scripts/test_deploy.sh` is present at the
PR base and the current head without a caller. The CI wrapper executes
the script as an entry point. Its interactive repository-update path
runs through `actualize_repo`, which supplies the prompt for default
and explicit build deployment. Remove the unused definition and verify
the existing active modes and prompt with the deployment fixtures.

The guides and script belong to this repository. Validate the changed
authored text and generated references using the existing tooling. The
round-seven full-page build recorded thirteen diagnostics in the
unchanged generated Selenium catalog. Verify the full-page diagnostics
against that baseline and run a strict build of the affected authored
sections and reference pages. The user approved this planning capture
and then invoked `openspec-apply-change` for group 12. Delivery and live
operations require separate approval.

## Risks / Trade-offs

- Repository-wide activation can block workflows on unprepared refs. During
  follow-up, prepare `test`, human-promoted `main`, and release refs intended for
  execution; explicitly retire unsupported historical reruns without moving
  published tags.
- SHA pins retain trust in the selected code and its runtime downloads.
  Assess upstream code, transitive references, and relevant tool advisories
  for this update; record remaining exposure without creating a parallel
  maintenance process.
- Dependabot PRs skip the existing documentation CI. Refresh through the
  shared pre-commit/release process; generated inventory may lag a bot's
  initial diff until that normal refresh occurs.
- Missing SSH-agent environment can remain undetected until a later SSH or
  SCP step. Exercise setup, later-client access, failure, and cleanup.
- Shell quoting must cover SSH's remote parsing as well as the local shell.
  Exercise the actual argument transport with malicious-looking data and
  valid reference names; validation alone cannot replace safe transport.
- Duplicate-key hardening does not establish a GitHub policy bypass. Keep
  the hosted-parser uncertainty distinct from the reproduced local gap.
- Hosted checks need privileges and infrastructure access. Keep their
  follow-up evidence distinct from the PR's implementation and verification
  results; local completion does not establish live outcomes.
- A fresh count file alone still accepts a runner crash as zero failures.
  Validate process outcome, complete output, and attempt identity together.
- Deleting the old spreadsheet breaks selective modes. Separate immutable
  selection input from the new attempt's output, and publish completion last.
- Producer and consumer revisions can differ during rollout. Reject legacy or
  mismatched outcomes explicitly; deliver compatible code together and record
  the revision actually exercised by any separately approved live check.

## Migration Plan

### PR delivery

Deliver the verified pins, native SSH setup/cleanup, regression tests,
generated inventory, concise provenance/retention rationale, and operating
procedures together. Remove the temporary snapshot and stale references.
Verify the
code behavior through isolated workflow tests, configuration checks, source
comparison, and documentation builds. These are the tracked implementation
and verification tasks in this change.

The bounded parser, inventory-test, documentation, deployment-key,
agent-cleanup, and input-transport remediations were implemented in
`62146241c`. Preserve the review's pre-existing-observation classification
when incorporating the second-round result-summary repair. The user approved
capture and application of that additional scope on 2026-11-23. Current task
progress is recorded in the checklist; local implementation and validation
do not establish the hosted outcomes below.

The 2026-11-24 extension has separate implementation approval. Its group 6
tasks define the renewed implementation and verification scope; the earlier
23/23 milestone does not complete it. Deliver the runner, test-only output
handling, shell wrappers, result consumer, tests, and documentation together.
Refresh documentation through its existing generators rather than editing
generated blocks. No delivered hub surface changes or sync apply are planned.

### Post-merge follow-up outside this change

The runbook preserves the following operational sequence. These steps remain
follow-up in [tasks.md](tasks.md#workflow-follow-up), outside the PR's scope.

1. Review the complete workflow diff and merge into `test` through human
   review. Before recording an approved manual `Run tests` execution against
   DEV with `nasadit_verzi: false`, verify that the host wrapper passes the
   current attempt identity and the running web container publishes outcome
   v2. If either is older, wait for a compatible rollout or obtain separate
   approval for a deployment-enabled control first. Use an agreed valid test
   selection for each control. The earlier supplied run demonstrates the
   defect. Hosted acceptance of repaired stdin, preparation, and readiness
   needs its own deployment-enabled evidence, in addition to evidence from
   the deployment-disabled control.
2. Observe the real Dependabot pin/comment update PR. Arrange human promotion
   of the pinned workflows to `main`; identify every other intended execution
   ref and either prepare it or explicitly exclude it from future runs.
3. Immediately before activation, re-read the repository policy and audit the
   workflow revisions actually used by those refs, including external
   composite action dependencies. Present the exact setting change and
   harmless probe for separate approval. Preserve other Actions settings.
4. Enable only `sha_pinning_required`, then capture the API response, a pinned
   control, and a tag-pinned negative probe with no secrets, infrastructure
   access, registry publication, or write-token permissions. Record its
   policy-specific rejection and remove the disposable probe with approval.
5. For a broken action pin, prefer another verified compatible SHA. If an
   emergency requires disabling enforcement, obtain explicit approval first
   and record the temporary policy state before restoring mutable refs.
   Re-audit compatibility and repeat policy probes before re-enabling it.

This change implements the runbook, not the hosted operations above. Branch delivery,
commits, PR creation, merges, live runs, policy changes, sync apply, and
archival retain the approval boundaries in the repository rules and invoked
workflow.

## Issue Criteria and PR Boundary

| Issue criterion | Delivered in this PR | Follow-up outside this change |
| --- | --- | --- |
| All external references use SHA plus version | Complete inventory, regression tests, and upstream commit provenance | Apply the reviewed workflows through normal delivery |
| Native SSH and successful DEV connection | Cross-step authentication and cleanup, verified with a disposable key and isolated clients | Authorized DEV SSH/SCP run and its URL |
| Dependabot updates SHA and comment | Compatible references, preserved update configuration, and regression coverage | Actual Dependabot PR and diff |
| Enforcement true and tag run rejected | Readiness, activation, probe, and recovery runbook | Supported-ref rollout, policy API readback, and positive/negative hosted probes |
| Complete retained-action registry | Generated inventory, retained-action rationale, and normal dependency-refresh integration | Normal dependency updates and human review |
| Trivy/Cosign decisions with reasons | Retention rationale and relevant selected-release security findings | Normal dependency updates and human review |

## Sources

- [GitHub: supported Dependabot ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
- [GitHub: repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [Trivy action manifest at v0.36.0](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/action.yaml)
- [Cosign installer manifest at v4.1.3](https://github.com/sigstore/cosign-installer/blob/v4.1.3/action.yml)
- [Docker Scout v1.30.0 release assessed during exploration](https://github.com/docker/scout-action/releases/tag/v1.30.0)
- [Trivy OCI artifact path-traversal advisory](https://github.com/advisories/GHSA-mcj4-mphf-j9ff)
- [Trivy plugin-manager path-traversal advisory](https://github.com/advisories/GHSA-8rc5-4fr6-64pw)
- [Trivy Helm decompression advisory](https://github.com/advisories/GHSA-q3fv-x8vg-qqm4)
- [Dependabot Actions parser](https://github.com/dependabot/dependabot-core/blob/main/github_actions/lib/dependabot/github_actions/file_parser.rb)
- [GitHub: use an intermediate environment variable](https://docs.github.com/en/actions/reference/security/secure-use#use-an-intermediate-environment-variable)
- [GitHub runner duplicate-key handling, inspected during exploration](https://github.com/actions/runner/blob/main/src/Sdk/DTObjectTemplating/ObjectTemplating/TemplateReader.cs#L213-L219)
- [util-linux script: child exit-status forwarding and stdin caveats](https://github.com/util-linux/util-linux/blob/master/term-utils/script.1.adoc)
- [Docker: container health filtering](https://docs.docker.com/reference/cli/docker/container/ls/#filtering---filter)
