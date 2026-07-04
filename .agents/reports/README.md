# .agents/reports

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Lidsky čitelné výstupy dlouhodobého technického review.

## Struktura

- `review_reports/`  
  - detailní reporty pro jednotlivé tasky (`T01.md` … `T10.md`, `final_audit.md`),  
  - viz také `review_reports/README.md` pro popis jednotlivých souborů.

- `bugs.md`  
  - evidence nalezených chyb (`BUG-XXX`),  
  - pro každou chybu: soubor/řádek, závažnost, vztah ke GitHub Issue, návrh opravy, task.

- `refactoring_backlog.md`  
  - backlog strukturálních / architektonických vylepšení,  
  - členění podle priority (vysoká / střední / nízká).


- `workflow_evolution_legacy_evidence.md`
  - zachovaná evidence z vyřazeného kanálu prompt-evolution.

## Poznámky

- Všechny nové bugy a refaktoringové návrhy musí být zapisovány sem, **ne** pouze
  do GitHub Issues, aby byla historie review kompletní.
- Reporty v `review_reports/` se generují po dokončení tasků T01–T11 podle
  kanonického workflow `aiscr-codebase-review`.

- Ekosystémová doporučení pro automatizaci (MCP, skills, hooks, subagenty) jsou pouze v hubu `aiscr-management` — viz `AGENTS.md`.
