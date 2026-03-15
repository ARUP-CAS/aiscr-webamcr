# .agents/reports

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

- `claude_automation_recommendations.md`  
  - doporučení pro nastavení Claude Code / Cursor automations (MCP servery, hooks, skills),  
  - sdílená pravidla mají žít zde a v `AGENTS.md` / `.agents/`, nikoli v `.cursor/` nebo `.claude/`.

## Poznámky

- Všechny nové bugy a refaktoringové návrhy musí být zapisovány sem, **ne** pouze
  do GitHub Issues, aby byla historie review kompletní.
- Reporty v `review_reports/` se generují po dokončení tasků T01–T11 podle šablony
  v `prompts/review_codebase.md`.

