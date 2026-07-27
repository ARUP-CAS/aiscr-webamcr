# .agents/

Konfigurace, prompty a výstupy pro AI coding agenty.
Pravidla a governance viz [AGENTS.md](../AGENTS.md).

## Struktura

```plain
.agents/
  prompts/
    review_codebase.md          — Hlavní prompt pro review session (plný audit T01–T11)
    review_update.md            — Follow-up prompt pro inkrementální aktualizaci auditu (U01–U06)
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
    review_reports/              — Standardizovaný cíl pro reviews (viz níže); reporty z tasků (<task_id>.md); final_audit.md obsahuje Changelog
    bugs.md                      — Evidence nalezených chyb
    refactoring_backlog.md       — Backlog strukturálních vylepšení
    claude_automation_recommendations.md  — Doporučení pro Claude Code automations
  scripts/
    review_tools.py              — Repo-agnostic review automation (hash, cross-validate, coverage-gaps, id-inventory, lint-artifacts, prompt-evolution, repo-structure, status)
```

## Kanonický zdroj

- **Governance:** `AGENTS.md`
- **Konfigurační hodnoty:** `config/review_config.yaml`
- **Stav review:** `config/review_cache.json`
- **Task instrukce:** `prompts/review_codebase.md`
- **Inkrementální update:** `prompts/review_update.md`
- **Doc hygiene audit:** `prompts/audit_doc_hygiene.md`
- **Konvence / setup / hooks:** `prompts/project_conventions.md`, `prompts/setup_dev.md`, `prompts/hooks_reference.md`
- **Automation doporučení:** `reports/claude_automation_recommendations.md`

## Ukládání reviews (standardizovaný cíl)

Každé review provedené agentem se ukládá do adresáře
`.agents/reports/review_reports/` jako Markdown dokument s **náhodným řetězcem
znaků** v názvu souboru, aby jeden agent nepřepsal review jiného agenta. Vzor:
`review_<topic>_<random>.md` (např. `review_validation_refactor_a3f9k2.md`).
Každé review musí navíc uvádět **název modelu**, který jej vytvořil (např.
`claude-opus-4-8`), zaznamenaný v hlavičce nebo metadatech dokumentu.

Všechny Markdown dokumenty generované agenty (plány, analýzy, reviews apod.)
musí být psány **anglicky**. Governance viz [AGENTS.md](../AGENTS.md).

Viz také [CONTRIBUTING.md](../CONTRIBUTING.md) § Správa dokumentace repozitáře.
