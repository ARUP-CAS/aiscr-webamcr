# .agents/prompts

Prompty a pomocná dokumentace pro AI agenty pracující v tomto repozitáři. Pokud není uvedeno jinak, nové prompty, plánovací texty a pomocné instrukce v této složce mají být psány anglicky; formální pravidla pro jazyk agentích promptů viz `AGENTS.md`.

## Hlavní soubory

- `review_codebase.md` — hlavní prompt pro dlouhodobý technický review (plný audit T01–T11).
- `review_update.md` — follow-up prompt pro inkrementální aktualizaci auditu (U01–U06); výstup do `final_audit.md` Changelog.
- `audit_doc_hygiene.md` — přenositelný prompt pro audit dokumentace (duplicit, drift, governance).
- `project_conventions.md` — shrnutí projektových konvencí pro agenty (větve, commity, docstringy…).
- `setup_dev.md` — onboarding a nastavení vývojového prostředí.
- `hooks_reference.md` — doporučené lokální hooks (PostToolUse / PreToolUse).

## Prompt evolution

Podsložka `prompt_evolution/` obsahuje návrhy na vylepšení hlavního review promptu
generované na konci jednotlivých tasků (`<task_id>_prompt_update.md`).

