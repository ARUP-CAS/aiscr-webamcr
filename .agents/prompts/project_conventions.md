# Project Conventions — AMČR (shrnutí pro agenty)

Krátký výtah konvencí z CONTRIBUTING.md a AGENTS.md. Autoritativní znění je v [CONTRIBUTING.md](../../CONTRIBUTING.md) a [CLAUDE.md](../../CLAUDE.md).

## Větve

- Základna: **vždy** od `test`. PR směřují do `test`.
- Vzor větví: `feature/<issue>`, `bugfix/<issue>`, `agents/<agent_name>/<topic>`.
- Do `dev` ani `main` přímo nepushovat.

## Commit zprávy

```
[typ] stručný popis (#číslo-issue)
```

Typy: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`.

## Python / kód

- **Formátování:** black (line 120), isort (profile black), flake8 (`.flake8`). Spouštět `pre-commit run --all-files`.
- **Docstringy:** čeština, Sphinx styl (`:param:`, `:return:`, `:raises:`). **Ne** Google-style (`Args`, `Returns`, `Raises`). Popisovat reálné chování, ne generické texty.
- **Django root:** `webclient/` — `manage.py` a `requirements.txt` jsou tam, ne v kořeni repozitáře.

## Co needitovat

- `*/migrations/*.py` — pouze při změně schématu.
- Generovanou dokumentaci — spouštět generátory (`docs/generate_module_docs.py`, `docs/generate_selenium_test_docs.py`).
- Citlivé soubory: `local_settings.py`, `secrets*.json`, `webclient_env_var.sh` (viz AGENTS.md § Mandatory Rules a hooks_reference.md).

## Výstupy agentů

- Vše do `.agents/` (reporty, analýzy, cache).
- Chyby do `.agents/reports/bugs.md`; křížově referencovat s GitHub Issues.
- Refaktoring návrhy do `.agents/reports/refactoring_backlog.md`.
