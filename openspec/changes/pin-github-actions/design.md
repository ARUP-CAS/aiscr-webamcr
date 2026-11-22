# Design

## Context

See [proposal.md](proposal.md) for motivation and scope, originating in
[ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).

Evidence gathered on 2026-11-22:

| Tier | Observation |
| --- | --- |
| Source-verified | Six workflow files contain 34 active `uses:` entries: 33 external references to 17 distinct action paths and one local reusable workflow. All external references currently use tags. Commented Scout steps are excluded. |
| Source-verified | `run-tests.yml` initializes `webfactory/ssh-agent` before separate SSH and SCP steps. `deployment.yml` provides a native-agent example within one shell step. |
| Source-verified | Dependabot already schedules weekly action updates into `test` with `docker-actions` and `attest` groups. |
| Live-verified | `GET repos/ARUP-CAS/aiscr-webamcr/actions/permissions` returns `enabled: true`, `allowed_actions: all`, and `sha_pinning_required: false`. The repository's default branch is `main`. |
| Documentation-verified | GitHub documents SHA and same-line version-comment updates by Dependabot, and says SHA enforcement also covers GitHub-owned actions. Reusable workflows are a distinct policy case. |
| Inferred risk | Mutable references can introduce upstream changes into privileged jobs. Neither this plan nor the issue establishes that a compromise has occurred. |

The issue's 2026-11-21 inventory is historical evidence; the current source
and policy reads above refresh it without upgrading its unverified claims.
No DEV workflow, image publication, Dependabot update, or policy rejection
has been exercised by this promotion.

## Goals / Non-Goals

Use the contracts in [github-actions-trust](specs/github-actions-trust/spec.md).
Preserve workflow inputs, triggers, job permissions, publishing behavior, and
the existing local reusable-workflow relationship while changing dependency
selection and SSH-agent setup. Pinning does not make downloaded binaries,
vulnerability databases, or action owners inherently trustworthy.

All planning and implementation files are repository-owned local edits.
Generated assistant assets come from the hub baseline named in the proposal
and require no sync. Any later need to modify delivered assets requires
separate hub work, including a dry-run check before any approved sync apply.

## Decisions

### Verify release commits without upgrading action major versions

Resolve each current action release against its upstream repository using
GitHub's refs/commits API or `git ls-remote`. Peel annotated tags to commits;
do not use a tag-object SHA, file blob SHA, guessed hash, or a fork's commit.
For moving major tags, select and record the corresponding full release
version and verify the tag-to-commit relationship. An unresolved relationship
blocks that pin. Preserve action subpaths and reuse the same verified SHA
and version comment for every occurrence of the same release.

Use `@<40-character-commit> # vX.Y.Z`. Tags and abbreviated hashes leave the
dependency mutable or ambiguous; introducing another pinning tool is
unnecessary for this bounded inventory. Record upstream verification sources
and date alongside the review evidence. This plan intentionally contains no
implementation SHAs that might become stale before apply.

Add `scripts/test_pre_commit_actions_trust.py`, discovered by the existing
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
separate acceptance check.

### Retain the SHA-pinned scanner and signer integrations

The operator selected retention of both wrappers with full SHA pins and
documented trust reviews on 2026-11-22. Preserve the existing image-scanning
and signing behavior. Replacing them would add ownership of binary installation,
verification, upgrades, and output compatibility to this repository.

Source inspection supports the comparison: Trivy's `v0.36.0` manifest pins
its setup and cache actions to full SHAs; the Cosign `v4.1.3` installer
embeds bootstrap checksums and verification logic. These are observations
about those release files, not a full security review. Inspect the resolved
action revisions and transitive action
references before policy activation; retain the trust in downloaded tools
and network services as an explicit residual.

### Keep a human-maintained dependency registry

Create `docs/source/12_zavislosti/github_actions.rst` and link it from that
directory's `index.rst`. Use the documentation's existing Czech language.
Include one row per retained third-party action path with upstream owner,
source-backed maintenance status, last actual review date, review cadence,
exposure, and decision rationale. GitHub-owned actions can be summarized
separately, while remaining subject to SHA pinning.

Review quarterly and on major-version, ownership, or material security
changes. A date is evidence of a completed review, not an automatically
renewed timestamp. Put the release-SHA lookup procedure, Dependabot review,
policy rollout, and recovery guidance on the same page. This keeps the
registry discoverable and avoids adding an unrelated registry generator.

### Preserve Dependabot and require hosted evidence

Keep the existing ecosystem, schedule, target branch, and update groups.
Change `.github/dependabot.yml` only if a reproduced compatibility issue
requires it. Local tests can check the pin/comment format and configuration;
they cannot establish that Dependabot has opened an update PR.

After rollout to `test`, capture a real Dependabot PR URL and its diff showing
both SHA and version-comment updates, including applicable grouping. If no
new release is available, acceptance remains pending rather than weakening
it or introducing a deliberately obsolete production dependency.

## Risks / Trade-offs

- Repository-wide activation can block workflows on unprepared refs. Prepare
  `test`, human-promoted `main`, and any release refs still intended for
  execution; explicitly retire unsupported historical reruns without moving
  published tags.
- SHA pins retain trust in the selected code and its runtime downloads.
  Review upstream code and transitive references; record remaining exposure.
- Missing SSH-agent environment can remain undetected until a later SSH or
  SCP step. Exercise setup, later-client access, failure, and cleanup.
- Hosted checks need privileges and infrastructure access. Keep local results
  distinct and retain pending acceptance tasks until authorized runs provide
  evidence.

## Migration Plan

1. After fresh implementation approval, refresh the inventory, retain the
   SHA-pinned scanner/signer actions, implement and test pins and native SSH,
   and publish the registry and operating procedures together.
2. Review the complete workflow diff and merge into `test` through human
   review. Record an approved manual `Run tests` execution against DEV with
   `nasadit_verzi: false` and an agreed valid test selection. A deployment
   requires its own explicit authorization.
3. Observe the real Dependabot pin/comment update PR. Arrange human promotion
   of the pinned workflows to `main`; identify every other intended execution
   ref and either prepare it or explicitly exclude it from future runs.
4. Immediately before activation, re-read the repository policy and audit the
   workflow revisions actually used by those refs, including external
   composite action dependencies. Present the exact setting change and
   harmless probe for separate approval. Preserve other Actions settings.
5. Enable only `sha_pinning_required`, then capture the API response, a pinned
   control, and a tag-pinned negative probe with no secrets, infrastructure
   access, registry publication, or write-token permissions. Record its
   policy-specific rejection and remove the disposable probe with approval.
6. For a broken action pin, prefer another verified compatible SHA. If an
   emergency requires disabling enforcement, obtain explicit approval first
   and record the temporary policy state before restoring mutable refs.
   Re-audit compatibility and repeat policy probes before re-enabling it.

This promotion performs none of the hosted operations above. Branch delivery,
commits, PR creation, merges, live runs, policy changes, sync apply, and
archival retain the approval boundaries in the repository rules and invoked
workflow.

## Acceptance Mapping

| Issue criterion | Contract and evidence |
| --- | --- |
| All external references use SHA plus version | Immutable references; complete inventory, regression tests, and upstream commit provenance |
| Native SSH and successful DEV connection | Cross-step authentication and cleanup; isolated checks plus authorized DEV run URL |
| Dependabot updates SHA and comment | Pin maintenance; actual Dependabot PR and diff |
| Enforcement true and tag run rejected | Compatible rollout; policy API and positive/negative hosted probes |
| Complete retained-action registry | Trust records and maintenance procedure; documented inventory reconciliation |
| Trivy/Cosign decisions with reasons | Operator decision followed by matching registry rationale |

## Sources

- [GitHub: supported Dependabot ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
- [GitHub: repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [Trivy action manifest at v0.36.0](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/action.yaml)
- [Cosign installer manifest at v4.1.3](https://github.com/sigstore/cosign-installer/blob/v4.1.3/action.yml)
