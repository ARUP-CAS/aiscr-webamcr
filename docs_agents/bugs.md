# Evidované chyby — AMČR (aiscr-webamcr)

> Všechny záznamy jsou psány v češtině.
> Před přidáním nové chyby ověř existující GitHub Issues (aktuálně 113 otevřených).
>
> Stavy: `již evidováno (Issue #XXX)` | `rozšíření existujícího issue #XXX` | `nový kandidát na issue`
>
> Závažnosti: `Kritická` | `Vysoká` | `Střední` | `Nízká`

---

<!-- Záznamy přidávají agenti po dokončení jednotlivých tasků -->

### BUG-001: eval() na hodnotách z databáze v generátorech identifikátorů

- **Soubory:**
  - `webclient/projekt/models.py:663` — `Projekt.set_permanent_ident_cely()`
  - `webclient/arch_z/models.py:331` — `ArcheologickyZaznam.set_lokalita_permanent_ident_cely()`
  - `webclient/arch_z/models.py:889` — `get_akce_ident()`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Všechna tři místa používají `eval(i)` pro převod textového čísla (segmentu `ident_cely` z DB) na integer. Ačkoliv jsou hodnoty interně generované a jejich formát je řízen aplikací, `eval()` je inherentně nebezpečná funkce — pokud by byl formát ident_cely narušen (např. chybnou migrací dat), mohl by být spuštěn libovolný Python kód.
- **Navrhovaná oprava:** Nahradit `eval(i)` za `int(i)` na všech třech místech. Přidat validaci formátu před konverzí (např. `i.isdigit()`).
- **Task:** T03

---

### BUG-002: N+1 dotazy v ArcheologickyZaznam.check_pred_odeslanim() a Projekt.check_pred_uzavrenim()

- **Soubory:**
  - `webclient/arch_z/models.py:240-268`
  - `webclient/projekt/models.py:561-578`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `check_pred_odeslanim()` volá `self.dokumentacni_jednotky_akce.all()` dvakrát a pro každou DJ dělá dotaz na `dj.komponenty.komponenty.all()`. `check_pred_uzavrenim()` volá `self.akce_set.all()` dvakrát a pro každou akci spouští kaskádovou `check_pred_odeslanim()`. Tyto metody jsou volány při každém pokusu o posun stavu záznamu — pro projekty s více akcemi a DJ může počet dotazů dosáhnout desítek.
- **Navrhovaná oprava:** Přidat `prefetch_related` ve view metodách před voláním `check_pred_*`. Refaktorovat `check_pred_*` metody tak, aby přijímaly prefetchovaná data jako parametr.
- **Task:** T03

---

### BUG-003: Import cached_property z distlib.util místo functools

- **Soubory:** `webclient/uzivatel/models.py:28`
- **Závažnost:** Nízká
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `from distlib.util import cached_property` — `distlib` je balíčkovací nástroj (součást pip), nikoliv Django nebo Python standard library. Správná implementace je `from functools import cached_property` (Python 3.8+). Import funguje, ale je nespolehlivý jako závislost a matoucí pro vývojáře.
- **Navrhovaná oprava:** `from functools import cached_property`
- **Task:** T03
