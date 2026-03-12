# .agents/

Konfigurace, prompty a výstupy pro AI coding agenty.
Pravidla a governance viz [AGENTS.md](../AGENTS.md).

## Struktura

```plain
.agents/
  prompts/
    review_codebase.md          — Hlavní prompt pro review session
    audit_doc_hygiene.md        — Portable audit: duplikace, drift, governance (any repo)
    project_conventions.md      — Shrnutí konvencí pro agenty (odkaz z AGENTS.md)
    setup_dev.md                — Checklist vývojového prostředí a onboarding
    hooks_reference.md          — Doporučené hooks (pro lokální konfiguraci)
    prompt_evolution/            — Návrhy na vylepšení promptu z jednotlivých sessions
  config/
    review_config.yaml          — Konfigurace review tasků, tech stack, adresáře
    review_cache.json            — Perzistentní stav a průběh review sessions
  analysis/
    repository_map.json          — Strukturální mapa repozitáře (T01)
    dependency_graph.json        — Graf interních a externích závislostí (T02)
    *_analysis.json              — Výstupy analýz per-task (ORM, Docker, security, …)
  reports/
    review_reports/              — Reporty z jednotlivých tasků (<task_id>.md)
    bugs.md                      — Evidence nalezených chyb
    refactoring_backlog.md       — Backlog strukturálních vylepšení
    claude_automation_recommendations.md  — Doporučení pro Claude Code automations (MCP, hooks, skills); sdílená pravidla v AGENTS.md/.agents/, ne v .cursor/.claude/
```

## Kanonický zdroj

- **Governance:** `AGENTS.md`
- **Konfigurační hodnoty:** `config/review_config.yaml`
- **Stav review:** `config/review_cache.json`
- **Task instrukce:** `prompts/review_codebase.md`
- **Doc hygiene audit:** `prompts/audit_doc_hygiene.md`
- **Konvence / setup / hooks:** `prompts/project_conventions.md`, `prompts/setup_dev.md`, `prompts/hooks_reference.md`
- **Automation doporučení:** `reports/claude_automation_recommendations.md`

Viz také [CONTRIBUTING.md](../CONTRIBUTING.md) § Správa dokumentace repozitáře.
