# Hooks reference — recommended local configuration

Hooks are configured locally (for example in `.claude/settings.json` or the Cursor equivalent); the `.cursor/` and `.claude/` directories are in `.gitignore`. This file is a reference description for the team — copy the rules into your local configuration.

## 1. PostToolUse: format and lint after editing Python

**Purpose:** After writing to `*.py`, run formatting and linting so the code stays consistent with `CONTRIBUTING.md` (black, isort, flake8).

**Configuration idea:**

- Trigger: after any tool use that modifies a file matching `**/*.py` (within the repository).
- Action: for the changed files, run for example:
  - `pre-commit run --files <path>` for the given paths, or
  - `black <path>` and `isort <path>` (from the repository root, with `webclient` on the path as needed).

**Note:** Migrations (`*/migrations/*.py`) are excluded from pre-commit; the hook can also skip these paths, or leave them to the pre-commit configuration.

## 2. PreToolUse: warn/block editing of sensitive files

**Purpose:** Prevent accidental edits of files containing secrets or local configuration (see `.gitignore`).

**Paths to protect (or warn about):**

- `**/local_settings.py`
- `**/secrets*.json` (including `secrets.json`, `secrets_backup.json`, `secrets.alternative.json`, …)
- `**/webclient_env_var.sh`

**Configuration idea:**

- Before executing a tool use that writes to a file, check the path.
- If it matches the patterns above: block with an explanation or show a confirmation prompt (depending on client capabilities).

---

For full context see `[automation_recommendations.md](../reports/automation_recommendations.md)` and `AGENTS.md` § Shared Automation Rules.
