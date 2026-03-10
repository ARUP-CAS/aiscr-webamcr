# .agents/

Složka obsahující konfiguraci, prompty a výstupy pro AI coding agenty.

## Struktura

- **prompts/** — Předdefinované prompty a návrhy na jejich vylepšení
  - `review_codebase.md` — Hlavní prompt pro review session
  - `prompt_evolution/` — Návrhy na vylepšení promptu z jednotlivých sessions
- **config/** — Konfigurace a perzistentní stav
  - `review_config.yaml` — Konfigurace review tasků
  - `review_cache.json` — Stav a průběh review sessions
- **analysis/** — Výstupy analýz (generované JSON soubory)
- **reports/** — Review reporty a sledování problémů
  - `review_reports/` — Reporty z jednotlivých tasků
  - `bugs.md` — Evidence nalezených chyb
  - `refactoring_backlog.md` — Backlog vylepšení

## Použití

Viz [AGENTS.md](../AGENTS.md) pro pravidla a konvence.
