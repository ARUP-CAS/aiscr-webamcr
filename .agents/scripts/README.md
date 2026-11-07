# .agents/scripts

Scripts for the AI review system and the delivered AIS CR workflows in this repository.
All scripts assume the standard `.agents/` layout described in `AGENTS.md` and `.agents/README.md`.

## Delivered tooling (read-only here)

These files are delivered from the `aiscr-management` hub and recorded in `.agents/delivery-manifest.json`; propose changes at the hub rather than editing them here.

- `codebase_review.py` — repo-agnostic CLI for validating and summarising the `.agents/` review artifacts. Subcommands include:
  - `hash` — compare file hashes against `review_cache.json`
  - `cross-validate` — consistency of `bugs.md`, the backlog, and `final_audit.md`
  - `coverage-gaps` — undocumented models, scripts, and JS files
  - `id-inventory` — inventory and cross-references of IDs (`BUG-*`, `SEC-*`, …)
  - `lint-artifacts` — structural validation of `.agents/`
  - `render` — regenerate `bugs.md` and `refactoring_backlog.md` from their TOML sources
  - `issue-transfer`, `record-issue`, `reconcile-issues` — deduplicated GitHub issue capture for findings
  - `status` — review system dashboard; `all` — run every validation check
- `github/` — governed GitHub issue and PR-review engines used by the enrolled workflows.
- `lib/` — shared library modules for the delivered scripts.
- Further workflow scripts (workstation safety, release notes) as enrolled.

## Repository-owned helpers

- `run_import_maintenance_tests.py` — runs the import-maintenance tests in the web container.

## Running

Run from the repository root, typically:

```bash
python .agents/scripts/codebase_review.py status
python .agents/scripts/codebase_review.py all
```

Optional switches:

- `--repo-root` — path to the repository root (otherwise detected from `.git`)
- `--config` — path to `review_config.toml` (default `.agents/config/review_config.toml`)
