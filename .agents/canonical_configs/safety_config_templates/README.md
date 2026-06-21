# safety_config_templates – šablony uživatelské bezpečnosti

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Tato složka drží **šablony** pro uživatelskou (app-level) konfiguraci Codexu a Claude Code související se **sandboxem a workspace hranicí**. Nejsou to repo-level soubory v kořeni projektu; cílové cesty jsou typicky v domovském adresáři uživatele. Ponechané šablony obsahují jen bezpečnostní nastavení podložená důkazy: nadbytečné defaulty vendora a nepřenositelné overridy bez měřitelného přínosu jsou vynechány, proto byly šablony pro Cursor sandbox a Gemini snippet odstraněny.

## K čemu to slouží

- **`port_workspace_safety_config.py`** – sloučí šablony do `~/.codex/config.toml` a `~/.claude/settings.json` (pravidla slučování a validace viz [scripts/README.md](../../scripts/README.md)); seznam cílů: `workspace_safety_registry.py` (stejné jako kontrola u bootstrap doctora). Codex používá současný top-level `sandbox_mode`; existující legacy `[sandbox].mode` se migruje a `[windows].sandbox` se zachovává (merge u nativního Windows `elevated` sandboxu vypíše upozornění, ale nemění ho).

Plán workflow: [port-workspace-safety-config.plan.md](../../plans/port-workspace-safety-config.plan.md). Governance k workspace hranici: `AGENTS.md`, `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.

## Soubory v kořeni této složky

| Soubor | Účel |
| ------ | ---- |
| `codex_user_config.toml` | Šablona pro uživatelský Codex `config.toml` (`approval_policy`, top-level `sandbox_mode`). |
| `claude_safety_snippet.json` | Část pro Claude `settings.json` – `sandbox`, vzorový `permissions.deny` a úzký allow-list pro repo-lokální wrapper `run_pre_commit_local.py`; skript slučuje s existujícím souborem. Claude sandbox běží na macOS/Linux/WSL2, ne na nativním Windows. |

## Podsložka `schemas/`

JSON Schema a související popis: [schemas/README.md](schemas/README.md).

## Úpravy a rizika

- Před zápisem na disk skripty **validují** JSON podle schémat v `schemas/` a strukturu Codex TOML; rozbitá šablona zastaví běh dříve než se cokoli přepíše.
- Bezpečnostně relevantní uživatelskou konfiguraci (sandbox, deny listy) agenti nemění bez výslovného pokynu uživatele; viz pravidla ochrany konfigurace v `AGENTS.md` a `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.
- Sandbox a deny defaulty ponechávejte přísné. Problémy se sdílenou pre-commit cache se mají řešit schválením pouze repo-lokálního wrapperu `run_pre_commit_local.py`, ne oslabováním těchto šablon.
