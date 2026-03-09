# Návrhy na zlepšení promptu — T03 (ORM analýza)

**Datum:** 2026-03-08
**Agent:** claude-sonnet-4-6

---

## Co v promptu chybělo / bylo nejasné

1. **Důležitost `__init__` metod pro N+1 detekci.** Prompt se zaměřuje na N+1 v iteracích, ale důležitým vzorem jsou modely, které ukládají initial hodnoty v `__init__` — absence tohoto vzoru v `save()` způsobuje extra SELECT. Prompt by měl explicitně uvést: "Zkontroluj, zda modely správně ukládají initial hodnoty FK polí v `__init__()`, aby se v `save()` nemusel dělat extra SELECT."

2. **Kontrola importů z nestandardních knihoven.** Nalezen import `cached_property` z `distlib.util` — nečekaný problém. Prompt by měl obsahovat: "Zkontroluj importy v modelech — správně by měly pocházet z Django, Python standard library nebo z explicitně definovaných závislostí v requirements.txt."

3. **Chybí explicitní instrukce pro kontrolu len() vs count().** Vzor `len(self.related_set.all())` místo `.count()` je časté anti-pattern. Přidat do T03: "Hledej vzory `len(queryset.all())` — mělo by být nahrazeno `.count()`."

4. **Chybí instrukce pro analýzu deprecated API.** `.extra()` je deprecated od Django 4.0. Prompt by měl obsahovat: "Zkontroluj, zda jsou použity deprecated ORM metody: `.extra()`, `select_related` bez polí, `raw()` bez parametrizace."

---

## Co by příštímu agentovi pomohlo

1. **Explicitní sub-task T03b pro views analýzu.** Soubory `arch_z/views.py` (2194 ř.), `dokument/views.py` (2946 ř.) a `projekt/views.py` (2114 ř.) jsou příliš velké pro zpracování v jednom tasku. Doporučuji přidat T03b: "ORM vzory ve views — select_related a prefetch_related pokrytí".

2. **Seznam aplikací v AGENTS.md je cenný.** Tabulka aplikací v AGENTS.md s počty souborů velmi pomohla pro plánování sub-tasků. Prompt by mohl odkazovat přímo na tuto tabulku.

3. **Sekvence databáze 'urgent' je architektonická zvláštnost.** Několik modelů (ProjektSekvence, AkceSekvence, PianSekvence) přistupuje přes speciální databázi `urgent` pro atomické generování sekvencí. Prompt by měl upozornit: "Věnuj pozornost databázi 'urgent' — je to zvláštní Django DB router pro souběžný přístup k sekvencím."

---

## Jaké soubory nebo adresáře by stálo za to přidat

- `webclient/*/signals.py` — signály jsou klíčové pro pochopení, kdy jsou volány `save()` metody s extra logikou.
- `webclient/*/managers.py` — custom QuerySet manažeři mohou výrazně ovlivnit ORM výkon.
- `webclient/history/models.py` — HistorieVazby a Historie jsou používány ve všech modelech, jejich struktura nebyla analyzována.
- `webclient/komponenta/models.py` — komponenty jsou součástí N+1 cyklů v arch_z, ale nebyly analyzovány.
