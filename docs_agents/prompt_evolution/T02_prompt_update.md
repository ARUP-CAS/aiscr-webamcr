# Návrhy na zlepšení promptu — T02 (Dependency Graph)

**Datum:** 2026-03-08
**Task:** T02

---

## Co v promptu chybělo nebo bylo nejasné

1. **Absence package.json nebyla anticipována.** PROMPT.md předpokládá existenci `package.json`, ale ten v repozitáři chybí. Agent se zbytečně zdržel hledáním. Doporučeno: přidat do T02 instrukci „pokud package.json neexistuje, zaznamenat jako N/A a přesunout analýzu CDN závislostí do T07."

2. **Definice cross-app importu je nejednoznačná.** Není jasné, zda do grafu patří i importy uvnitř testů (`tests/`) nebo pouze produkční kód. Pro tuto analýzu byl zahrnut produkční kód i testovací soubory, ale konvence by měla být explicitně definována.

3. **Chybí instrukce pro identifikaci lazy importů.** Lazy import (import uvnitř funkce) je architektonicky odlišný od modulového importu, ale PROMPT.md to nerozlišuje. U cirkulárních závislostí je tento rozdíl klíčový.

---

## Co by příštímu agentovi pomohlo

1. **Explicitní potvrzení absence package.json** — přidat kontrolu do inicializační sekvence.

2. **Rozlišení fan-in/fan-out metriky** — PROMPT.md by mohl specifikovat prahové hodnoty (např. fan-in > 10 = kandidát na dekompozici).

3. **Odkaz na INSTALLED_APPS** jako autoritativní zdroj seznamu aplikací — v tomto tasku bylo nutné ručně sestavit seznam z base.py.

4. **Instrukce pro dokumentaci lazy importů** — přidat poznámku, že lazy importy (uvnitř funkcí) snižují, ale neodstraňují riziko cirkulárních závislostí.

---

## Jaké soubory nebo adresáře by stálo za to přidat

- `webclient/services/` — tento adresář nebyl explicitně uveden v INSTALLED_APPS ani v repository_map.json, ale obsahuje sdílené servisní funkce (mailer.py) importované více aplikacemi. Doporučeno přidat do `important_directories` v review_config.yaml.
- `webclient/xml_generator/` — doporučeno explicitně zmínit v kontextu T02, protože funguje jako průřezová base-model knihovna.
