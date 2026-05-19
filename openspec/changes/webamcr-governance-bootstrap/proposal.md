## Why

Until now, `aiscr-webamcr` has carried agent-vendor surfaces (`.cursor/`, `.claude/`, `.codex/`) as gitignored, repository-local artefacts, alongside an explicit "no agent folders in git" policy in [AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md). The legacy in-development tooling under those folders never reached production, and the resulting governance posture is inconsistent with the rest of the AIS CR ecosystem (where the management hub `aiscr-management` syncs canonical agent configurations into siblings as tracked content). On 2026-05-06 the legacy assets were removed and the corresponding `.gitignore` entries dropped, opening the door to a coherent first pass: adopt OpenSpec for spec-driven evolution and document the new tracked-vendor-folder posture as a behavioural contract.

## What Changes

- Adopt OpenSpec (`spec-driven` schema) as the requirement surface for `aiscr-webamcr` and add `@fission-ai/openspec` to the project's dev tooling.
- Treat `.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, and `.qodo/` as **tracked** content delivered by the hub canonical sync (`aiscr-management/.agents/local_configs/`) rather than gitignored local artefacts. **BREAKING** for the prior "no agent folders in git" rule documented in `AGENTS.md` and `CLAUDE.md`.
- Introduce `.agents/local_overrides.toml` with a `[bootstrap]` block recording the schema in use, the date and hub revision the repository was last aligned to, and any explicit deviations from the hub baseline.
- Update `AGENTS.md` (Shared Automation Rules section) and `CLAUDE.md` (Recommended MCP section) to describe the new tracked-vendor posture and the hub-driven sync as the source of truth.
- Defer non-bootstrap behavioural changes (Django app behaviour, deploy/operations, AI review process formalisation) to follow-on changes; this change only establishes the governance foundation.

## Capabilities

### New Capabilities

- `agent-governance`: Defines how `aiscr-webamcr` declares its agent-governance posture, tracks vendor surfaces synchronised from `aiscr-management`, records intentional overrides, and resolves inconsistencies against canonical hub references.

### Modified Capabilities

<!-- None — no prior OpenSpec specs in this repository. -->

## Impact

- **Tooling:** `package.json` and `package-lock.json` gain `@fission-ai/openspec` (devDependency) and three `openspec:*` npm scripts mirroring the hub.
- **Repository layout:** new `openspec/` tree (`config.yaml`, change-local artifacts under `changes/webamcr-governance-bootstrap/`, including `changes/webamcr-governance-bootstrap/specs/agent-governance/spec.md`); new `.agents/local_overrides.toml`; modified `.gitignore` (already in working tree) removing agent-folder ignore lines. The persistent `openspec/specs/agent-governance/spec.md` is created later only when the change is archived.
- **Vendor surfaces:** `.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, and `.qodo/` are (re)created from hub canonical sync after dry-run review. The initial lower-level sync was followed by the orchestrator specialized-asset apply so rules, skills, agents, and reference assets from the effective sync surface are present.
- **Cross-repo:** none directly — this change is sibling-local. Hub `repos.toml` already lists `aiscr-webamcr` for sync into the affected vendor folders, so no hub registration change is required.
- **CI / automation:** `npx openspec validate --all` becomes part of the verification surface for future changes that touch `openspec/`.
- **Documentation drift repaired:** `AGENTS.md` "Shared Automation Rules" and `CLAUDE.md` "Recommended MCP" now describe tracked hub-synchronized vendor surfaces.
