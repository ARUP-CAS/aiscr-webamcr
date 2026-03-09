# T01 — Návrhy na zlepšení promptu

**Datum:** 2026-03-08
**Task:** T01 — Repository Map

---

## Co v promptu fungovalo dobře

- Jasné vymezení scope (které adresáře zahrnout, které nikoliv).
- Výčet konkrétních souborů, které mají být zahrnuty do `key_config_files`.
- Instrukce pro infrastrukturní komponenty (ELK, Prometheus, Redis, Fedora, Proxy) jsou přesné.

## Co chybělo nebo bylo nejasné

1. **Umístění `requirements.txt` a `manage.py`**: Tyto soubory jsou v `webclient/`, nikoli v kořeni repozitáře. Prompt (a inicializační `review_config.yaml`) je uvádí jako kořenové soubory, což způsobilo zbytečné hledání. Doporučení: doplnit poznámku o jejich skutečném umístění.

2. **Neexistující `pyproject.toml` a `package.json`**: Tyto soubory jsou v `review_config.yaml` uvedeny jako `important_files`, ale v repozitáři (ani v kořeni, ani v `webclient/`) nebyly nalezeny při analýze. Pravděpodobně existují, ale v jiném umístění nebo neexistují vůbec. Doporučení: ověřit existenci nebo odstranit ze seznamu.

3. **Adresář `locale`**: Uveden v `important_directories`, ale v repozitáři nebyl nalezen v kořeni. Případně je zanořen jinde.

## Co by příštímu agentovi pomohlo

1. **Explicitní poznámka o kořeni projektu**: Django project root je `webclient/`, ne kořen repozitáře. `manage.py`, `requirements.txt` jsou v `webclient/`, nikoli v `/`.

2. **Přesný seznam Django aplikací**: Prompt uvádí doménové entity (Projekt, Akce atd.), ale ne mapování na adresáře Django apps. Bylo by užitečné přidat tuto tabulku do promptu nebo AGENTS.md.

3. **Upozornění na `core` jako velkou aplikaci**: `core` se 77 soubory je výrazně největší aplikace. Pro T03 (ORM) by bylo vhodné explicitně navrhnout její rozdělení do sub-tasků.

## Jaké soubory nebo adresáře by stálo za to přidat

- `webclient/webclient/settings/base.py` — klíčový soubor pro T05 (Security)
- `webclient/webclient/celery.py` — klíčový soubor pro T06 (Celery)
- `webclient/cron/tasks.py` — klíčový soubor pro T06
- `webclient/notifikace_projekty/tasks.py` — klíčový soubor pro T06
