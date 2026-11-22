# Proposal

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).

## Why

The issue records mutable action references in workflows that receive SSH keys,
registry credentials, and image-signing permissions. Following the removal of
an action in [ARUP-CAS/aiscr-webamcr#4375](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4375),
the remaining action dependencies need immutable references and documented trust
decisions before repository-wide SHA enforcement can be enabled safely.

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
- Keep relevant trust rationale and pin-resolution, rollout, and recovery
  instructions on the linked dependency page. Remove PR-specific completion
  wording, special review-date bookkeeping, and the temporary
  `.agents/analysis/github-actions-trust.json` snapshot and its references.
- Deliver the runbook for enabling `sha_pinning_required` after compatible
  rollout, including approval, positive/negative probes, and recovery.
  Executing that runbook is post-merge follow-up.

This changes CI security governance and workflow behavior. Django application
behavior and data contracts are unaffected. Container image pinning, replacing
`docker/*` actions, and changes to other repositories are outside scope.

## Capabilities

### New Capabilities

- `github-actions-trust`: Immutable workflow action dependencies, native SSH
  access, generated dependency inventory, retained-action rationale, normal
  dependency maintenance, update compatibility, and documented policy readiness.

### Modified Capabilities

None. The repository currently has no durable capability specs.

## Impact

- Implementation: the six existing `.github/workflows/*.yml` files;
  `.github/dependabot.yml` only if a demonstrated compatibility issue needs it;
  production parsing and generation in `docs/generate_module_docs.py` or a
  shared helper; `scripts/test_pre_commit_actions_trust.py` and generator
  regression tests under `scripts/`, run by the existing CI test job;
  the existing `generate-module-docs` pre-commit integration;
  `docs/source/12_zavislosti/github_actions.rst` and its `index.rst` entry;
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

## Follow-up outside this change

After merge, follow up the DEV SSH/SCP run, an actual Dependabot SHA/comment
update PR, human promotion to `main` and other intended execution refs,
approved repository policy activation, and positive/negative policy probes.
Their ordering, authorization, and evidence requirements remain explicit in
[tasks.md](tasks.md#workflow-follow-up) and [design.md](design.md).

This change ends with the implementation, documentation, and verification
deliverable in this PR. Completing it does not establish the hosted outcomes
or resolve the driving issue's remaining operational acceptance criteria.
