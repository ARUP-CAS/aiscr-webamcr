# .agents/scripts

Skripty a pomocné nástroje pro AI review systém v tomto repozitáři.
Všechny skripty předpokládají standardní strukturu `.agents/` popsanou v
`AGENTS.md` a `.agents/README.md`.

## Hlavní skripty

- `review_tools.py` — repo‑agnostický CLI nástroj pro ověřování a
  sumarizaci artefaktů v `.agents/`. Umí mimo jiné:
  - `hash` — kontrola hashů souborů podle `review_cache.json`
  - `cross-validate` — konzistence `bugs.md`, backlogu a `final_audit.md`
  - `coverage-gaps` — nevdokumentované modely/skripty/JS soubory
  - `id-inventory` — inventarizace a křížové reference ID (`BUG-*`, `SEC-*`, …)
  - `lint-artifacts` — validace struktury `.agents/`
  - `prompt-evolution` — stav integrace návrhů z `prompt_evolution/`
  - `repo-structure` — souhrn struktury repozitáře
  - `status` — dashboard stavu review systému
  - `all` — spuštění všech výše uvedených kontrol

## Spuštění

Spouštějte z kořene repozitáře, typicky:

```bash
python .agents/scripts/review_tools.py status
python .agents/scripts/review_tools.py all
```

Volitelné přepínače:

- `--repo-root` — cesta ke kořeni repozitáře (jinak se detekuje z `.git`)
- `--config` — cesta k `review_config.yaml` (výchozí `.agents/config/review_config.yaml`)

