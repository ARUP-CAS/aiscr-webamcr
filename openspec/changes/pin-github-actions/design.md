# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. Requirements are in
[github-actions-trust](specs/github-actions-trust/spec.md),
[ci-test-results](specs/ci-test-results/spec.md) and
[deployment-automation](specs/deployment-automation/spec.md).

State at the start (base `d327f2caf`, 2026-11-22):

- Six workflow files held 33 external `uses:` references to 17 action paths,
  all by tag, plus one local reusable workflow. The policy read returned
  `allowed_actions: all` and `sha_pinning_required: false`.
- Dependabot already updated actions weekly into `test`, with the
  `docker-actions` and `attest` groups.
- The DEV test workflow fetched `results.xlsx` and `test_summary.env` from
  fixed paths and executed the summary with `source`.

The only DEV run of this branch,
[job 138090470675](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45288367885/job/138090470675)
at `65b0f6a8e`, reported success although no tests ran. The input-transport
repair had switched the remote script from `bash -c` to `bash -s`, and
`docker exec -i` in the deployment script then read the remaining script
from stdin. Comparing with the base confirmed four older gaps:

- The workflow accepted results from an earlier run.
- The runner ignored migration and test return codes, and turned a crash
  into `PASSED=0 FAILED=0` with exit 0.
- The wrappers hid failed operations and recorded a failed deployment as
  successful.
- Readiness accepted tasks that were already unhealthy.

No DEV run or deployment has exercised any later commit. Outcome format v1
(`5ae9cf45c`) was replaced by v2 (`d90182be3`) before any server ran either.

All files in this change are repository-owned local edits. Generated
assistant assets come from the hub baseline named in the proposal, and no
sync is needed.

## Goals / Non-Goals

**Goals:**

- Meet the issue's pinning, SSH, inventory and runbook criteria.
- Make the DEV test run a reliable acceptance check, preferring the smallest
  mechanism that does so.
- Keep valid workflow inputs, triggers, permissions, publishing and test
  modes unchanged.

**Non-Goals:**

- Pinning container images or replacing `docker/*` actions.
- Automatic rollback, or deployment topology changes.
- Server-side history beyond one previous test run.
- Locking against a manual test run started during a CI run.
- Compatibility with result formats that were never deployed.

## Decisions

### Pin format and release selection

Use `@<40-character-commit> # vX.Y.Z`, resolved against the upstream
repository with annotated tags peeled to commits. Each workflow uses the
latest compatible stable release, including newer majors, and every
occurrence of the same release shares one SHA and comment.

Alternatives: a pinning tool such as `pinact` adds a dependency for a
bounded inventory, and a JSON evidence snapshot duplicated the workflows (it
was removed).

Assessment on 2026-11-22:

- 15 of 16 retained paths were already at the latest release. Docker Scout
  moved to `v1.30.0`, with an identical manifest.
- CodeQL uses the action release `v4.39.4`, not the CLI bundle releases.
- All upstream repositories are active and released. The GitHub Advisory
  Database showed no active match for the selected actions, the nested
  actions or Cosign CLI `3.1.4`.
- Trivy's wrapper defaults to CLI `0.70.0`. Its three known advisories need
  alternate OCI repositories, plugin installation or Helm misconfiguration
  scanning, and none is configured here. The risk is accepted for these
  calls, not judged safe in general.

### Parser and inventory in the existing documentation tooling

`docs/generate_module_docs.py` parses the workflows and generates the
inventory on `docs/source/12_zavislosti/github_actions.rst` through the
existing `generate-module-docs` hook. The parser:

- distinguishes step actions from job-level reusable workflows;
- ignores local and commented calls;
- rejects mutable references, malformed hashes, missing comments, comments
  shared by several calls on one line, and duplicate mapping keys.

Each rejection carries a file and line diagnostic. Regression tests in
`scripts/` define the expected inventory rows independently of the
production code, so an omission cannot appear on both sides. Requiring
block style everywhere was rejected because flow syntax is already covered
by tests.

### Retain Trivy and Cosign

The operator chose on 2026-11-22 to keep both actions with pins and recorded
rationale. Replacing them would make this repository own binary
installation, verification and upgrades. Trust in the downloaded tools and
the vulnerability database remains a documented residual risk.

### Native SSH agents and key scope

- **`run-tests.yml`** starts `ssh-agent` in a setup step and passes only
  `SSH_AUTH_SOCK` and `SSH_AGENT_PID` to the later SSH and SCP steps. An
  unconditional step stops the agent.
- **`deployment.yml`** keeps the whole agent lifetime inside the SSH step,
  with an EXIT trap set before the key is loaded.

Both read the key from step environment with CRLF normalization and no
tracing. Copying the single-step `deployment.yml` pattern into
`run-tests.yml` would lose the agent between steps.

### Workflow values as data, stdin detached

Inputs and reference names travel through step environment variables and
are validated before the VPN or SSH starts. The remote script is a quoted
static heredoc run with `sudo bash -s --`. Each argument is POSIX-quoted by
`scripts/ssh_arguments.sh`, which both SSH workflows share.

`deployment.yml` checks out the requested release tag. It loads the helper
from a separate sparse checkout of `github.workflow_sha`, so tags older than
the helper stay deployable. Deployment and test commands on the server get
`< /dev/null`, so they cannot read the remaining script.

### Result directories and run identity

```text
/opt/selenium_test/                (TEST_SCREENSHOT_PATH, results root)
  results.xlsx    selection input; replaced only after a completed run
  current/        emptied when a run starts; output of this run
    outcome.json      written last: run id, mode, number, state, counts, file hashes
    test_summary.env  PASSED / FAILED
    test_output.log
    results.xlsx, *.png
  previous/       the run before; never read by selection or the workflow
```

At start the runner validates the run ID: `<run_id>-<run_attempt>` from CI,
or `local-<uuid>` when run by hand. It then:

1. refuses to continue if `current/` or `previous/` is a symbolic link;
2. removes `previous/`;
3. renames `current/` to `previous/`, if present;
4. creates an empty `current/`.

The test-only output setting points the Selenium tests at `current/`.

After a completed run the merged workbook replaces the root `results.xlsx`,
and `outcome.json` is written last. The workflow downloads
`current/outcome.json`, rejects a missing file or a different run ID, then
downloads and hash-checks the listed files. A run that never started
therefore leaves the previous run's ID in place and fails. A run that
stopped after the rotation leaves no outcome and also fails. The format
keeps `version: 2`; v1 existed only in unmerged history.

Alternatives considered:

- **Ten finished runs in `runs/<id>/`.** This needed lock files, atomic
  marker publication, a 30-day rule and v1 backfill, which caused six later
  review findings. It was implemented, then removed in this revision.
- **`current/` only.** This loses the evidence of the run before the latest.
  `previous/` costs one rename.
- **A lock file held during the run.** The DEV concurrency group already
  serializes CI test runs and deployments. A manual run started during a CI
  run is a documented operator error. The run ID and hash checks catch an
  overwrite after publication.
- **Screenshots in the GitHub artifact.** This is the better place for long
  history and is left to a separate issue.

Files from the old base layout in the results root are left untouched.

### Runner outcomes and counts

The runner:

- checks the migration result;
- reads both output streams to the end in both logging modes;
- reconciles the `Ran N tests` line, the status line and the process return
  code;
- requires at least one executed test body.

Skips and expected failures are counted separately, and the outcome counts
must add up to the total. Failed-only selection with no failures is the only
successful run with no tests executed. Selection and publication accept a
test name when every dotted part is a Python identifier
(`str.isidentifier()`), so Czech letters in Selenium method names are valid.
The names reach `manage.py test` as separate arguments without a shell.
Selenium tests register driver cleanup when the driver is created, and
classify each workbook row from their own result.

### Runner diagnostics

A runner failure is reported as
`Chyba testovacího běhu (<stage>): <type>: <message>`. Before the message is
printed or recorded:

- the configured results root is replaced by `<results-root>` in its
  configured, absolute and resolved forms;
- control characters, including line breaks, become spaces;
- the length is capped.

The runner prints this line to stderr and stores it as the outcome
`message`. Outcome validation accepts only one bounded line. For an error
outcome, `scripts/collect_test_results.py` adds the cause to the step summary
and emits one `::error::` annotation, escaping `%`, CR and LF as
workflow-command data.

Alternatives considered:

- **Fixed stage only.** This was the earlier decision, taken after CodeQL
  alert 7461 flagged a printed results path. The first DEV run that reached
  publication (run 45895898223) failed as `publication` without a cause.
  Diagnosing it needed the result artifact and a local reproduction.
- **Own validation messages only, exception type otherwise.** Nothing could
  leak, but library failures lose their detail. This is the fallback if
  hosted CodeQL flags the sanitised text.

### DEV runs only Selenium tests

The DEV default selection holds only the 11 Selenium modules. Their test
classes derive from `BaseSeleniumTestClass`, which records a workbook row for
each test, so failed-only and numbered selection see every DEV result. This
matches the split in
[ARUP-CAS/aiscr-webamcr#4465](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4465):
its inventory excludes the Selenium modules as the DEV workflow's and assigns
unit and import modules to its `fast` and `database` jobs, each with its own
summary and log artifact. A regression test fails when a default module
contains a test class outside `BaseSeleniumTestClass`.

Removed from DEV:

- the four #4450 unit and import modules
  (`core.tests.test_organization_ownership`,
  `core.tests.test_mappers.test_organizace_mapper`,
  `cron.tests.test_run_data_import_organizace` and
  `heslar.tests.test_organization_import_guard`). #4465 assigns two of them
  to its `database` job; the other two postdate its branch;
- the two Fedora integration modules. They need a deployed Fedora, are
  skipped on DEV because the integration flag is off, and #4465 excludes
  them. They now run only through the manual Docker command in the
  integration-test guide; a separate DEV step for them is follow-up.

Alternatives considered:

- **Two DEV suites with their own steps and summaries.** This changes the
  result format and the workflow, duplicates #4465, and keeps the
  reused-database failures on DEV.
- **Rerun every untracked module in each failed-only run.** This restores
  correctness but keeps mixed reporting on DEV.

### Deployment failures, readiness and script hygiene

Every required operation in `test_deploy.sh`, `prod_deploy.sh`,
`start_selenium_tests.sh` and both CI wrappers checks its status explicitly
(`|| return $?`, `|| exit $?`). The success record is written only after
`scripts/check_stack_ready.py` confirms the required services, tasks and
health of the target stack. `scripts/deployment_helpers.sh` holds the shared
code:

- command logging;
- network and stack checks;
- stack removal;
- web-container lookup;
- log rotation;
- the Swarm precondition.

Both deployment scripts validate the whole request, including help, before
any side effect.

`set -eo pipefail` is removed from `prod_deploy.sh`. It duplicated the
explicit checks and already caused one regression (R4-F3, the Swarm message
became unreachable). On the production command it would abort on harmless
nonzero statuses that no test reproduces. The CI wrappers and DEV-only
scripts keep it: they contain few commands, each explicitly checked, and DEV
runs exercise them before any production deployment.

Older release tags run their own wrapper with its historical failure
handling. For example, `v1.4.0` can record success after a failed readiness
check, so the guide requires independent verification for such tags.

### Ordinary dependency maintenance

Keep the Dependabot ecosystem, schedule, target and groups. Updates are
reviewed by humans like any dependency. The inventory refreshes at the
existing pre-commit and release documentation points, because the
documentation CI skips bot branches. No Actions-only schedule, review dates
or privileged bot path is added.

### Scope freeze

From this revision on, a review finding is fixed in this PR only if this PR
introduced it and it is Critical or High. Everything else goes to a
follow-up issue. Eight review rounds showed that accepting every pre-existing
observation keeps generating new code to review.

The first live DEV run at `e0831d563` found a High defect this PR
introduced: the readiness check fails on the host's Python 3.6, which stops
every DEV and TEST deployment. The freeze keeps it in this PR (task 7.1).
The round-nine deployment-guide correction O16 is a deliberate author
exception, made in the same revision (task 7.2). Round-nine observation O15,
the OpenVPN configuration taken from the selected tag, goes to a follow-up
issue. The hosted pre-commit job at `de9a4fc8d` showed a false
`Selhalo 1 testů` error annotation because three execution tests let runner
and report output reach the job log. This Low finding was introduced by this
PR and is fixed here as a further author exception (task 7.4).

The DEV run at `de9a4fc8d` (run 45895898223) passed readiness and executed
the tests, then found two more problems:

- **Test names.** Selection and publication rejected the 17 Selenium tests
  whose names contain Czech letters, so every full run ends as an error.
  This PR introduced the ASCII-only name check, so the freeze keeps the High
  fix here (task 7.5).
- **Diagnostics.** The stage-only message hid that cause. Reporting the cause
  is a deliberate author exception, made in the same revision (task 7.6).

The run's 68 failures in `test_organizace_mapper` and
`test_run_data_import_organizace` predate this PR. These #4450 tests insert
fixed `heslar_nazev` keys into the reused DEV database. They are deferred to
[ARUP-CAS/aiscr-webamcr#4465](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4465).

A failed-only DEV run at `bca3b69d6` (run 45959732625) then reported success
without running a test. The workbook lists only Selenium tests, so the 68
failures of the previous full run were invisible to selection, and the run
published the explicit successful no-op. Before this PR the same run failed
only because the workflow read the previous run's stale summary. This PR
made the no-op explicit, so the freeze keeps this High false pass here. DEV
now runs only Selenium tests, in line with #4465 (task 7.8).

Round ten (review at `bca3b69d6`) found two Low items this PR introduced:

- **Duplicated ssh-agent key-load block.** `deployment.yml` and
  `run-tests.yml` carry the same block, and only `deployment.yml` sets the
  `~/.ssh` and `known_hosts` permissions. This is maintenance only and joins
  the SSH and VPN hardening already tracked in
  [ARUP-CAS/aiscr-webamcr#4570](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4570),
  together with O15.
- **Stale usage sentence.** The usage entry still calls the committed 7.6
  checkbox uncommitted. The close-out corrects it (task 7.11).

Its pre-existing observations O17 (wrong `git_prod_deploy.sh` paths in the
deployment guide) and O18 (the documentation generator drops `*args`,
keyword-only and `**kwargs` parameters from function signatures) are
deliberate author exceptions, fixed in the same revision (tasks 7.9 and
7.10). The generator fix also feeds the Django module pages, so it
regenerates 99 signatures on 28 pages, each only adding missing
parameters.

## Risks / Trade-offs

- **Activation blocks unprepared refs.** Activating enforcement stops
  workflows on refs that still use tags. → Follow the runbook: prepare or
  retire each intended ref first.
- **Pins still trust upstream.** Pinned actions and their runtime downloads
  are still trusted code. → The assessment and residual risk are recorded,
  and normal dependency review continues.
- **Fixtures are not real Docker.** They replace `docker`, `ssh` and `sudo`
  with stand-ins. → The DEV and TEST checks in the migration plan come before
  relying on the change.
- **Workflow and DEV host must match.** A deployment-disabled run against an
  older DEV host fails because `current/outcome.json` is missing. → Run with
  deployment enabled first. The failure is visible, not a false pass.
- **A manual run during CI can mix `current/` files.** → Rare and
  documented. The run ID and hashes catch an overwrite after publication.
- **`prod_deploy.sh` has not run live.** Its first live run comes with the
  first tagged deployment. → Deploy to TEST first and verify the version and
  readiness before production.
- **Dependabot inventory lags.** A Dependabot diff can update pins before the
  inventory. → The next normal refresh corrects it.
- **A sanitised cause could still carry a path.** A path in a form the
  sanitiser does not recognise could appear in a message. → The root is
  replaced in three forms, fixtures cover a secret-backed root and a resolved
  root, and hosted CodeQL checks the flow. If CodeQL flags it, fall back to
  the runner's own messages and the exception type.
- **The tests removed from DEV have no hosted run until #4465 lands.** #4465's
  branch predates `core.tests.test_organization_ownership` and
  `heslar.tests.test_organization_import_guard`. → Ask its owner to add them
  to its inventory when rebasing (workflow follow-up). On DEV they only
  failed against the reused database.

## Migration Plan

1. Before merge, after separate approval, dispatch `Run tests` from the PR
   branch with deployment enabled. This covers stdin, deployment, readiness
   and the new result directories. Then run it with deployment disabled.
   Record run URLs, revisions and attempt IDs. Both runs are expected to
   pass, because DEV runs only Selenium tests.
2. A colleague reviews the PR and merges it into `test`. The PR description
   gives a reading order and flags the production script changes.
3. The first TEST deployment of a release containing this change is the
   first live run of `prod_deploy.sh` and `deploy_server.sh`. Verify the
   deployed version and stack readiness independently, before any production
   deployment.
4. Observe a real Dependabot pin update, promote the pinned workflows to
   `main`, and audit every other ref intended to run.
5. With separate approval, enable only `sha_pinning_required`, read it back,
   and run a pinned control and a tag-pinned probe. The probes use no secrets
   or write tokens.

Recovery: for a broken pin, prefer another verified SHA. Disabling
enforcement needs approval and a recorded policy state. Reverting the PR is
safe; an older runner ignores `current/` and `previous/`.

## Issue criteria and PR boundary

| Issue criterion | Delivered in this PR | Follow-up |
| --- | --- | --- |
| SHA pins with version comments | Complete pins, parser and tests | Normal delivery |
| Native SSH, DEV connection works | Native agent with fixture tests | DEV run (migration step 1) |
| Dependabot updates SHA and comment | Configuration kept and tested | Observed Dependabot PR |
| Enforcement on, tag run rejected | Runbook | Rollout, activation, probes |
| Registry of retained actions | Generated inventory and rationale | Normal dependency review |
| Trivy and Cosign decisions | Recorded rationale and assessment | Normal dependency review |

## Review history

Per-item evidence and dispositions are in the linked reviews and in the git
history of this file. Every round from 5 to 10 confirmed all repairs from the
round before. Pre-commit and CodeQL passed on each delivered head from
`d90182be3` to `e0831d563`.

| Round | Reviewed head | Source | Introduced | Pre-existing fixed | Main outcome |
| --- | --- | --- | --- | --- | --- |
| 1 | `0735cb560` | PR review | 5 | 4 | Parser hardening, key scope, input transport |
| 2 | `62146241c` | PR review | 1 | 1 | Summary read as data |
| DEV run | `65b0f6a8e` | [job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45288367885/job/138090470675) | 1 (stdin) | 4 | Execution reliability |
| CI | `5ae9cf45c` | [pre-commit job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45374557884/job/138377173853), [CodeQL 7461](https://github.com/ARUP-CAS/aiscr-webamcr/security/code-scanning/7461) | 2 | 0 | Executable stubs, runner diagnostics |
| 4 | `09d4d12e1` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6043320852) | 7 | 7 (O4 declined) | Selenium cleanup, counts, helpers, retention |
| 5 | `d90182be3` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6049994746) | 7 | 2 | Older tags, attempt ownership |
| 6 | `5dc50a879` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6053375832) | 5 | 1 | Lock marker, artifact contents, container lookup |
| 7 | `244db4ac5` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6061348584) | 1 | 2 | Lease markers, request validation |
| 8 | `0bae037a9` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6066800751) | 3 (docs) | 1 | Guides aligned |
| 9 | `e0831d563` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6069580737) | 0 | 1 (O16; O15 deferred) | No new findings |
| DEV run | `e0831d563` | [job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45771045340/job/139747914273), attempt 2 | 1 (host Python) | 0 | Readiness check must run on Python 3.6 |
| CI | `de9a4fc8d` | [pre-commit job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45895469093/job/140168151293) | 1 (leaked annotation) | 0 | Test output captured and asserted |
| DEV run | `de9a4fc8d` | [job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45895898223/job/140169581355), attempt 2 | 1 (test names) | 0 | Readiness passed; non-ASCII names rejected at publication; cause reporting added; #4450 failures deferred to #4465 |
| DEV run | `5932d146c` | [run 45911203331](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45911203331), attempt 1 | 0 | 0 | Completed; 17 non-ASCII names accepted; only the #4450 modules failed |
| DEV run | `bca3b69d6` | [job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45959732625/job/140374449093), attempt 1, failed-only | 1 (false pass) | 0 | No-op success despite 68 untracked failures; DEV becomes Selenium-only |
| 10 | `bca3b69d6` | [review](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544#pullrequestreview-6085012707) | 2 (Low) | 2 (O17, O18; O15 in #4570) | ssh-agent block to #4570; usage sentence; guide paths; generator signatures |
| Simplification | `f11aa5629` | Exploration on 2026-11-26 | - | - | Retention replaced, v1 code and `set -e` removed, specs split |

## Sources

- [GitHub: supported Dependabot ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
- [GitHub: repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [GitHub: use an intermediate environment variable](https://docs.github.com/en/actions/reference/security/secure-use#use-an-intermediate-environment-variable)
- [Trivy action manifest at v0.36.0](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/action.yaml)
- [Cosign installer manifest at v4.1.3](https://github.com/sigstore/cosign-installer/blob/v4.1.3/action.yml)
- [Docker Scout v1.30.0 release](https://github.com/docker/scout-action/releases/tag/v1.30.0)
- Trivy advisories: [OCI artifact path traversal](https://github.com/advisories/GHSA-mcj4-mphf-j9ff), [plugin manager path traversal](https://github.com/advisories/GHSA-8rc5-4fr6-64pw), [Helm decompression](https://github.com/advisories/GHSA-q3fv-x8vg-qqm4)
- [Dependabot Actions parser](https://github.com/dependabot/dependabot-core/blob/main/github_actions/lib/dependabot/github_actions/file_parser.rb)
- [GitHub runner duplicate-key handling](https://github.com/actions/runner/blob/main/src/Sdk/DTObjectTemplating/ObjectTemplating/TemplateReader.cs#L213-L219)
- [util-linux `script`: exit status and stdin](https://github.com/util-linux/util-linux/blob/master/term-utils/script.1.adoc)
- [Docker: container health filtering](https://docs.docker.com/reference/cli/docker/container/ls/#filtering---filter)
