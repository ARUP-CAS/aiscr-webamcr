# .agents/prompts

Prompty a pomocná dokumentace pro AI agenty pracující v tomto repozitáři. Pokud není uvedeno jinak, nové prompty, plánovací texty a pomocné instrukce v této složce mají být psány anglicky; formální pravidla pro jazyk agentích promptů viz `AGENTS.md`.

## Hlavní soubory

- Codebase review: operační workflow je kanonické `aiscr-codebase-review` (režimy full T01–T11 / update U01–U06), dodané přes skill surfaces `.cursor/` / `.claude/` / `.codex/` / `.gemini/`; samostatné prompty `review_codebase.md` / `review_update.md` již v této složce nejsou.

## Evidence workflow-evolution

Starší soubory `.agents/prompts/prompt_evolution/` byly klasifikovány a zachovány
v `.agents/reports/workflow_evolution_legacy_evidence.md`. Aktivní zpětná vazba
z U05 zůstává pouze evidencí, dokud člověk výslovně neschválí předání do backlogu.
