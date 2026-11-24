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
Use the result step's existing Bash tooling to read `test_summary.env` as
data, never with `source` or `eval`. Require exactly one `PASSED` and one
`FAILED` assignment containing ASCII decimal digits; reject duplicate or
unknown keys, missing values, executable text, empty records, and NUL bytes.
Support LF/CRLF records and a final record without a terminating newline.
Normalize leading zeros by string operations to canonical decimal outputs;
avoid arithmetic evaluation and overflow while parsing downloaded values.

Finish validating the entire file before appending either output or the
human-readable summary. Preserve their names and Markdown layout, the
spreadsheet artifact, and the numeric failure check. The existing `always()`
cleanup handles a parse failure after the SCP clients used the agent.

Extend the existing disposable-key result-step fixtures to deliver arbitrary
summary bytes. Exercise the real shell with valid/zero/failed counts, record
order and line-ending controls, and malformed, duplicate, missing, unknown,
binary, and command-substitution payloads. Invalid input must execute no
canary, leave outputs and summary untouched, fail the step, and still permit
agent cleanup. Document this result-data boundary on the dependency page.
The earlier result-parsing repair needed no producer change. The approved
execution-reliability extension now changes the producer and retrieval
protocol as described below, retaining this numeric parser and adding no
runtime dependency or new workflow.

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
   review. Record an approved manual `Run tests` execution against DEV with
   `nasadit_verzi: false` and an agreed valid test selection. A deployment
   requires its own explicit authorization. The run already supplied for this
   investigation demonstrates the defect, not repair acceptance. A separately
   authorized deployment-enabled control is also needed to establish hosted
   acceptance of the repaired stdin, preparation, and readiness path; keep that
   evidence distinct from the no-deployment control.
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
