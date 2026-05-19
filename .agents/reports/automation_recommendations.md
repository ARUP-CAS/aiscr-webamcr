# Automation Recommendations — AMČR (aiscr-webamcr)

Datum: 2026-03-11

## Applied (2026-03-11)

Doporučení byla aplikována do repozitáře; sdílená pravida jsou v `AGENTS.md`, `CLAUDE.md` a `.agents/`.

| Položka | Kde aplikováno |
|--------|------------------|
| **MCP** (context7, GitHub) | AGENTS.md § Recommended MCP Servers and Subagents; CLAUDE.md § Recommended MCP |
| **project-conventions** | `.agents/prompts/project_conventions.md`; odkaz v AGENTS.md (Coding Standards) |
| **setup-dev** | `.agents/prompts/setup_dev.md`; odkaz v CLAUDE.md § Recommended MCP |
| **Hooks** (PostToolUse format/lint, PreToolUse secrets) | `.agents/prompts/hooks_reference.md`; AGENTS.md § Mandatory Rules (pravidlo 6) a § Shared Automation Rules |
| **Subagents** (code-reviewer, security-reviewer) | AGENTS.md § Recommended MCP…; T05 v `review_codebase.md` — poznámka o security-reviewer |

Lokální konfigurace (`.cursor/`, `.claude/`) zůstává na každém vývojáři; tento report a uvedené soubory jsou referenční zdroj.

---

## Umístění sdílených pravidel (důležité)

**Sdílená pravidla a konfigurace pro AI agenty musí být v repozitáři a verzována.** Adresáře `.cursor/` a `.claude/` jsou v `.gitignore`, proto je nepoužívejte pro nic, co má být sdílené týmem.

| Účel | Kde ukládat |
|------|--------------|
| Obecná pravidla pro agenty | `AGENTS.md` |
| Claude Code / Cursor instrukce (prostředí, cesty, formátování) | `CLAUDE.md` |
| Konfigurace review tasků, tech stack, limity | `.agents/config/` (např. `review_config.yaml`) |
| Prompty pro specializované agenty / workflow | `.agents/prompts/` |
| Návrhy hooků, subagentů, skills (dokumentace) | tento soubor nebo `.agents/prompts/` |

Hooks, subagenti a MCP servery, které vyžadují lokální konfiguraci (např. `.claude/settings.json`), lze **dokumentovat** v `AGENTS.md` nebo zde — implementace zůstane v lokálním `.claude/`/`.cursor/`, ale tým má jednu pravdu v repozitáři.

---

## Codebase Profile

- **Type:** Python / Django 5.2
- **Framework:** Django (webclient/), Sphinx (docs/)
- **Key libraries:** Celery, Redis, DRF, Selenium, black/isort/flake8, pre-commit, Docker
- **Existing automation:** `.agents/` review system (prompts, config, cache, reports)

---

## 🔌 MCP Servers

### 1. context7

**Proč:** Django, DRF, Celery, Sphinx a další knihovny — živá dokumentace bez opuštění editoru.

**Instalace (lokálně):** `claude mcp add context7` (nebo ekvivalent v Cursor). Pro sdílení v repozitáři doporučujeme zmínit v `AGENTS.md` nebo v `CLAUDE.md`, že context7 je doporučen pro dokumentaci knihoven.

### 2. GitHub MCP (plugin-github-github)

**Proč:** Repozitář má 113 otevřených issue a workflow v `.github/workflows/`. Propojení s PR, issues a Actions zlepší konzistenci s `AGENTS.md` (křížové reference bugů s GitHub Issues).

**Poznámka:** MCP konfigurace může být v lokálním `.mcp.json`; v `AGENTS.md` lze uvést, že GitHub MCP je doporučen pro práci s issue/PR.

---

## 🎯 Skills

Doporučení: skills, které jsou specifické pro tento repozitář, **dokumentovat** v `.agents/prompts/` jako „skill-like“ prompty nebo sekce v `review_codebase.md`. Vlastní `.claude/skills/` jsou gitignored — pro týmovou shodu tedy popisovat v repozitáři a lokálně si je každý může zřídit podle dokumentace.

### 1. project-conventions (Claude-only)

**Proč:** AGENTS.md a CONTRIBUTING.md už obsahují konvence (větve, commit zprávy, docstringy, migrace). Shrnutí „project conventions“ jako skill zvyšuje pravděpodobnost, že je model dodrží.

**Kde:** Přidat odkaz v `AGENTS.md`: „Pro rychlé shrnutí konvencí viz CONTRIBUTING.md a CLAUDE.md.“ Případně `.agents/prompts/project_conventions.md` s výtahem (branch workflow, docstring style, co needitovat).

### 2. setup-dev / onboarding

**Proč:** Windows, venv v `.venv\Scripts\python.exe`, Django root v `webclient/`, pre-commit — opakovaný workflow pro nové vývojáře.

**Kde:** Dokumentovat v `CLAUDE.md` (už částečně) a v `docs/`; případně `.agents/prompts/setup_dev.md` jako checklist pro agenty i lidi.

---

## ⚡ Hooks

Hooks se konfigurují v `.claude/settings.json` nebo Cursor ekvivalentu (lokálně, gitignored). **Doporučení** lze uložit sem do repozitáře, aby je tým mohl aplikovat lokálně.

### 1. PostToolUse: format / lint po editaci

**Proč:** black, isort, flake8 a pre-commit jsou v projektu; automatické spuštění po editaci Python souborů drží kód v souladu s CONTRIBUTING.md.

**Lokální konfigurace:** PostToolUse hook, který po zápisu do `*.py` spustí např. `pre-commit run --files <file>` nebo `black` + `isort` na změněné soubory. Referenční popis uložit sem nebo do `AGENTS.md`.

### 2. PreToolUse: blokovat editaci citlivých souborů

**Proč:** V `.gitignore` jsou `local_settings.py`, `secrets.json`, `webclient_env_var.sh`. PreToolUse může blokovat pokusy o editaci těchto cest (nebo zobrazit varování).

**Lokální konfigurace:** PreToolUse hook s pravidly pro `**/secrets*.json`, `**/local_settings.py`, `**/webclient_env_var.sh`. Dokumentace sem nebo do `AGENTS.md` § Mandatory Rules.

---

## 🤖 Subagents

Subagenti jsou typicky v `.claude/agents/` (gitignored). **Popis kdy a jak je spouštět** může být v repozitáři.

### 1. code-reviewer

**Proč:** Velký codebase (5000+ commits, 23 Django apps, stovky souborů). Paralelní review konkrétních modulů nebo PR zlepší konzistenci s `.agents/reports/` a `refactoring_backlog.md`.

**Kde dokumentovat:** V `AGENTS.md` nebo zde: „Pro hloubkové review konkrétní části kódu lze použít subagenta code-reviewer; výstupy zapisovat do `.agents/reports/` a backlogu.“

### 2. security-reviewer (nebo ekvivalent)

**Proč:** T05 security analysis, auth (CAS), secrets, Docker — citlivé části. Specializovaný security subagent před mergem do `test`/`dev` dává smysl.

**Kde dokumentovat:** V `.agents/prompts/review_codebase.md` u T05 nebo v `AGENTS.md` jako doporučení pro security-sensitive změny.

---

## Shrnutí

| Kategorie | Doporučení | Sdílená pravda v repozitáři |
|-----------|-------------|-----------------------------|
| MCP | context7, GitHub | Zmínka v AGENTS.md / CLAUDE.md |
| Skills | project-conventions, setup-dev | AGENTS.md, CLAUDE.md, .agents/prompts/ |
| Hooks | PostToolUse format/lint, PreToolUse block secrets | Tento soubor nebo AGENTS.md |
| Subagents | code-reviewer, security-reviewer | AGENTS.md nebo .agents/prompts/ |

Vše, co má být sdílené a verzované, patří do `AGENTS.md`, `CLAUDE.md` nebo `.agents/` — ne do `.cursor/` ani `.claude/`.

---

## Odkazy na aplikované artefakty

- Konvence (shrnutí): [.agents/prompts/project_conventions.md](../prompts/project_conventions.md)
- Setup dev checklist: [.agents/prompts/setup_dev.md](../prompts/setup_dev.md)
- Hooks reference (pro lokální konfiguraci): [.agents/prompts/hooks_reference.md](../prompts/hooks_reference.md)

---

Chcete další doporučení pro konkrétní kategorii? Stačí požádat (např. „další MCP servery“ nebo „detailní hook konfigurace“).
