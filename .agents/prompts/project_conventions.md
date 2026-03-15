# Project Conventions — AMČR (summary for agents)

Short extract of conventions from `CONTRIBUTING.md` and `AGENTS.md`. The authoritative wording is in `[CONTRIBUTING.md](../../CONTRIBUTING.md)` and `[CLAUDE.md](../../CLAUDE.md)`.

## Branches

- Base: **always** from `test`. PRs target `test`.
- Branch naming: `feature/<issue>`, `bugfix/<issue>`, `agents/<agent_name>/<topic>`.
- Never push directly to `dev` or `main`.

## Commit messages

```
[type] short description (#issue-number)
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`.

## Python / code

- **Formatting:** black (line 120), isort (profile black), flake8 (`.flake8`). Run `pre-commit run --all-files`.
- **Docstrings:** Czech language, Sphinx style (`:param:`, `:return:`, `:raises:`). **Not** Google-style (`Args`, `Returns`, `Raises`). Describe real behaviour, not generic boilerplate.
- **Agent prompts / plans:** English only, even when surrounding code or docstrings are in Czech (see `AGENTS.md`). The planning phase must be run in English and produce an English-written plan (fixed rule in `AGENTS.md` § Planning phase and plans).
- **Django root:** `webclient/` — `manage.py` and `requirements.txt` live there, not in the repository root.

## What not to edit

- `*/migrations/*.py` — only when a schema change is required.
- Generated documentation — run generators (`docs/generate_module_docs.py`, `docs/generate_selenium_test_docs.py`).
- Sensitive files: `local_settings.py`, `secrets*.json`, `webclient_env_var.sh` (see `AGENTS.md` § Mandatory Rules and `hooks_reference.md`).

## Agent outputs

- Everything goes into `.agents/` (reports, analyses, cache).
- Bugs go to `.agents/reports/bugs.md`; cross-reference with GitHub Issues.
- Refactoring suggestions go to `.agents/reports/refactoring_backlog.md`.
