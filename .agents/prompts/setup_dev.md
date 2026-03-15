# Setup dev / onboarding — AMČR

Checklist for setting up the development environment and for agents that execute steps on the developer’s machine.

## Environment

- **OS:** Windows 11 (use Unix-style syntax in bash/scripts where possible).
- **Python venv:** `.venv\Scripts\python.exe` (repository root).
- **Django project root:** `webclient/` — not the repository root.

## Basic commands

| Purpose | Command |
|--------|---------|
| Syntax check | `.venv\Scripts\python.exe -m compileall -q webclient` |
| Formatting + lint | `pre-commit run --all-files` |
| Django manage | `cd webclient && ..\.venv\Scripts\python.exe manage.py <command>` |
| Tests | see `CONTRIBUTING.md` § Testing (typically from `webclient/`) |

## Before the first commit

1. Branch from `test`: `git checkout test && git pull && git checkout -b feature/<issue>`.
2. Verify that pre-commit passes: `pre-commit run --all-files`.
3. Do not add to commits: `local_settings.py`, `secrets.json`, `webclient_env_var.sh` (they are in `.gitignore`).

## For agents

- Read `AGENTS.md` and `.agents/config/review_cache.json` first. Code conventions: `[project_conventions.md](project_conventions.md)`. Full wording: `CONTRIBUTING.md`, `CLAUDE.md` (in the repository root).

## Further documentation

- Installation and deployment: `docs/02_instalace_nasazeni/`
- Development and standards: `docs/03_vyvoj/`, `CONTRIBUTING.md`
