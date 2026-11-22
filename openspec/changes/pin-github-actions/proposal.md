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
  comment. Include GitHub-owned actions and preserve local `./` calls.
- Replace `webfactory/ssh-agent` in `run-tests.yml` with native SSH-agent setup
  that supports subsequent SSH and SCP steps, fails on key-loading errors,
  and cleans up the agent.
- Retain `aquasecurity/trivy-action` and `sigstore/cosign-installer` with
  verified SHA pins and documented trust reviews, recording the approved
  rationale and residual trust.
- Keep Dependabot's weekly `github-actions` updates targeting `test`, including
  its `docker-actions` and `attest` groups, and require an observed PR that
  updates both a SHA and its version comment.
- Document retained third-party actions and the pin-resolution, review,
  rollout, and recovery procedures on a linked dependency documentation page.
- Enable `sha_pinning_required` only after the pinned workflows have reached
  every ref intended to remain runnable, with explicit approval for the hosted
  setting change and controlled positive and negative policy probes.

This changes CI security governance and workflow behavior. Django application
behavior and data contracts are unaffected. Container image pinning, replacing
`docker/*` actions, and changes to other repositories are outside scope.

## Capabilities

### New Capabilities

- `github-actions-trust`: Immutable workflow action dependencies, native SSH
  access, maintained third-party trust records, update compatibility, and
  ordered repository policy enforcement.

### Modified Capabilities

None. The repository currently has no durable capability specs.

## Impact

- Implementation: the six existing `.github/workflows/*.yml` files;
  `.github/dependabot.yml` only if a demonstrated compatibility issue needs it;
  `scripts/test_pre_commit_actions_trust.py` for focused regression coverage
  discovered by the existing workflow test command;
  `docs/source/12_zavislosti/github_actions.rst` and its `index.rst` entry.
- Hosted operations: the repository Actions policy, an approved DEV test run,
  a real Dependabot update PR, and a harmless policy-rejection probe. These
  remain pending until separately authorized and observed.
- Planning: this local OpenSpec change and its rolling usage entry under
  `.agents/reports/usage/`.
- Generated assistant assets remain owned by the `aiscr-management` baseline
  recorded in `.agents/delivery-manifest.json` (source commit
  `4ce7896238fe9996ccf1b0740cf3d6440d8d4d3f`), supplied through its
  `.agents/sync/repos.toml` enrollment and
  `.agents/canonical_configs/asset_manifest.toml`. This change requires no hub
  delivery, sync apply, or governance bootstrap.

The promotion contains planning artifacts only. Implementation requires a fresh
instruction naming `pin-github-actions`; hosted acceptance is additional to
local validation.
