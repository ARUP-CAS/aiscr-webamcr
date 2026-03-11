# Hooks reference — doporučená lokální konfigurace

Hooks se konfigurují lokálně (např. `.claude/settings.json` nebo Cursor ekvivalent); adresáře `.cursor/` a `.claude/` jsou v `.gitignore`. Tento soubor je referenční popis pro tým — zkopírujte si pravidla do své lokální konfigurace.

## 1. PostToolUse: format a lint po editaci Pythonu

**Účel:** Po zápisu do `*.py` spustit formátování a lint, aby kód zůstal v souladu s CONTRIBUTING.md (black, isort, flake8).

**Nápad konfigurace:**

- Trigger: po tool use, které upraví soubor matching `**/*.py` (v rámci repozitáře).
- Akce: pro změněné soubory spustit např.:
  - `pre-commit run --files <path>` pro dané cesty, nebo
  - `black <path>` a `isort <path>` (z kořene repozitáře, s `webclient` na cestě podle potřeby).

**Poznámka:** Migrace (`*/migrations/*.py`) jsou z pre-commit vyloučeny; hook může stejně vynechat tyto cesty, nebo je nechat na pre-commit konfiguraci.

## 2. PreToolUse: varování / blokování editace citlivých souborů

**Účel:** Zabránit náhodné editaci souborů se secrets nebo lokální konfigurací (viz `.gitignore`).

**Cesty k chránit (nebo varovat):**

- `**/local_settings.py`
- `**/secrets*.json` (včetně `secrets.json`, `secrets_backup.json`, `secrets.alternative.json`, …)
- `**/webclient_env_var.sh`

**Nápad konfigurace:**

- Před provedením tool use, který zapisuje do souboru, zkontrolovat cestu.
- Pokud odpovídá výše uvedeným vzorům: blokovat s vysvětlením nebo zobrazit výzvu k potvrzení (podle možností klienta).

---

Pro plný kontext viz [claude_automation_recommendations.md](../reports/claude_automation_recommendations.md) a AGENTS.md § Shared Automation Rules.
