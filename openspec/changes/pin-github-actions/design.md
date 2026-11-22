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
The first local implementation pins 32 retained external calls across 16
distinct action paths, replaces the SSH-agent action, and adds tests and a
manual dependency page. Exploration found that it lacks inventory generation,
still carries PR-specific prose and a temporary evidence snapshot, and imposes
unnecessary periodic reviews. The revised tasks reopen those areas and the
latest-release/security assessment; earlier completion is not acceptance of
this revised design.

No DEV workflow, image publication, Dependabot update, or policy rejection
has been exercised for this change. Those hosted observations remain
follow-up to the driving issue.

## Goals / Non-Goals

Use the contracts in [github-actions-trust](specs/github-actions-trust/spec.md).
Preserve workflow inputs, triggers, job permissions, publishing behavior, and
the existing local reusable-workflow relationship while changing dependency
selection and SSH-agent setup. Pinning does not make downloaded binaries,
vulnerability databases, or action owners inherently trustworthy.

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

### Keep SSH-agent state across steps

Use native `ssh-agent` and `ssh-add` with fail-fast Bash and CRLF-normalized key
input from a step environment variable. Persist only `SSH_AUTH_SOCK` and
`SSH_AGENT_PID` through `GITHUB_ENV` for the later SSH and SCP steps. Never
persist the private key or enable shell tracing around it. Add unconditional
cleanup that safely handles initialization failure and stops a created agent.

Preserve known-host verification and the VPN setup. Simply copying
`deployment.yml` would lose the agent environment at the end of the setup
step. Verify the cross-step lifecycle and key-loading failure with isolated
shell execution and a disposable test key; live DEV access remains a
separate post-merge follow-up check.

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
- Hosted checks need privileges and infrastructure access. Keep their
  follow-up evidence distinct from the PR's implementation and verification
  results; local completion does not establish live outcomes.

## Migration Plan

### PR delivery

Deliver the verified pins, native SSH setup/cleanup, regression tests,
generated inventory, concise provenance/retention rationale, and operating
procedures together. Remove the temporary snapshot and stale references.
Verify the
code behavior through isolated workflow tests, configuration checks, source
comparison, and documentation builds. These are the tracked implementation
and verification tasks in this change.

### Post-merge follow-up outside this change

The runbook preserves the following operational sequence. These steps remain
follow-up in [tasks.md](tasks.md#workflow-follow-up), outside the PR's scope.

1. Review the complete workflow diff and merge into `test` through human
   review. Record an approved manual `Run tests` execution against DEV with
   `nasadit_verzi: false` and an agreed valid test selection. A deployment
   requires its own explicit authorization.
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
