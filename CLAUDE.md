# CLAUDE.md — Claude Code Instructions

Full agent rules, repository structure, and coding standards: see [AGENTS.md](AGENTS.md).
Coding standards, branch rules, and PR process: see [CONTRIBUTING.md](CONTRIBUTING.md).
AI review system state and artifacts: see [.agents/README.md](.agents/README.md).

## Governance & OpenSpec

Hub-required minimums apply: **plan first** with human approval before mutating
steps, and record **one rolling usage-log entry** (with agent/runtime + backend
model id) for significant work. Canonical rule bodies are delivered as readers
under [.claude/rules/](.claude/rules/) (`aiscr-planning-core`,
`aiscr-usage-logging`, `aiscr-model-logging`); full governance is in
[AGENTS.md](AGENTS.md).

OpenSpec is versioned in `openspec/` (`specs/`, `changes/`, `config.yaml` —
schema `spec-driven`). Validate with `npm run openspec:validate`. Use the
`openspec-*` / `opsx` skills under `.claude/skills/`; honour explore → plan →
implement mode-transfer gating per `aiscr-planning-core`.

## Repository

Django web app for the Archaeological Map of the Czech Republic (AMČR), part of AIS CR (ARUP-CAS).
Django project root is `webclient/` — `manage.py` and `requirements.txt` live there, **not** in the repo root.

## Environment

- Windows 11, bash shell (use Unix syntax)
- Python venv: `.venv\Scripts\python.exe`
- Compile check: `.venv\Scripts\python.exe -m compileall -q webclient`
- Pre-commit: `pre-commit run --all-files`
- Django manage: `cd webclient && ..\.venv\Scripts\python.exe manage.py <command>`

## Formatting & Code Style

- `black` (line-length 120), `isort` (profile black), `flake8` (per `.flake8`)
- Docstrings: Czech language, Sphinx style (`:param:`, `:return:`, `:raises:`)
- Google-style blocks (`Args`, `Returns`, `Raises`) are **not allowed**
- Docstrings must describe real behavior — no generic text

## Branch Workflow

```
feature / bugfix / docs / agents branches → test → main
```

- Always branch from `test`; PR to `test`
- Never push directly to `test` or `main`
- Agent branches: `agents/<agent>/<topic>`

## Key Paths

| Path | Purpose |
|------|---------|
| `webclient/` | Django app root (manage.py, requirements.txt) |
| `webclient/core/` | Shared infrastructure — largest app (77 .py, 26 migrations) |
| `webclient/projekt/` | Archaeological projects |
| `webclient/uzivatel/` | Users, permissions, CAS SSO |
| `docs/` | Sphinx documentation |
| `scripts/` | Operational & deploy scripts |
| `.agents/` | AI review artifacts (reports, analysis, config) |
| `static/`, `templates/` | Inside `webclient/`, not repo root |

## Do Not

- Edit `*/migrations/*.py` unless schema change is required
- Edit generated docs — run generators instead (`docs/generate_module_docs.py`, `docs/generate_selenium_test_docs.py`)
- Flag `cert/` as security concern — self-signed dev certs, intentionally committed
- Modify files outside task scope
- Commit secrets or sensitive configuration

## Generated Artifacts & Pre-commit Hooks

See [CONTRIBUTING.md](CONTRIBUTING.md) § Generovaná dokumentace a artefakty and § Testování for details.
Migrations are excluded from all hooks.

## Recommended MCP (local config)

For live library docs (Django, DRF, Celery, Sphinx): **context7**. For
issues/PRs and cross-referencing with AGENTS.md: **GitHub MCP**. Configure
personal MCP credentials locally. Repository vendor surfaces such as
`.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, and `.qodo/`
are tracked when materialized from the `aiscr-management` hub sync baseline;
do not store private credentials in them. Dev setup checklist:
[.agents/prompts/setup_dev.md](.agents/prompts/setup_dev.md).
