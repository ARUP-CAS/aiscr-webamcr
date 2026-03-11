# Setup dev / onboarding — AMČR

Checklist pro nastavení vývojového prostředí a pro agenty, které provádějí kroky na stroji vývojáře.

## Prostředí

- **OS:** Windows 11 (používat Unixovou syntaxi v bashe/skriptech kde možno).
- **Python venv:** `.venv\Scripts\python.exe` (kořen repozitáře).
- **Django project root:** `webclient/` — ne kořen repozitáře.

## Základní příkazy

| Účel | Příkaz |
|------|--------|
| Kontrola syntaxe | `.venv\Scripts\python.exe -m compileall -q webclient` |
| Formátování + lint | `pre-commit run --all-files` |
| Django manage | `cd webclient && ..\.venv\Scripts\python.exe manage.py <command>` |
| Testy | dle CONTRIBUTING.md § Testování (typicky z `webclient/`) |

## Před prvním commitem

1. Větev z `test`: `git checkout test && git pull && git checkout -b feature/<issue>`.
2. Ověřit, že pre-commit projde: `pre-commit run --all-files`.
3. Nepřidávat do commitu: `local_settings.py`, `secrets.json`, `webclient_env_var.sh` (jsou v `.gitignore`).

## Pro agenty

- Číst nejprve `AGENTS.md` a `.agents/config/review_cache.json`. Konvence kódu: [project_conventions.md](project_conventions.md). Plné znění: CONTRIBUTING.md, CLAUDE.md (v kořeni repozitáře).

## Další dokumentace

- Instalace a nasazení: `docs/02_instalace_nasazeni/`
- Vývoj a standardy: `docs/03_vyvoj/`, CONTRIBUTING.md
