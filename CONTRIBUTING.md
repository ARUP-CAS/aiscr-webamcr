# Contributing

Děkujeme, že chcete přispět do projektu AIS CR / AMČR.

Tento dokument shrnuje doporučený postup pro změny v kódu, dokumentaci a pull requestech.

## 1) Základní workflow

1. Vytvořte si branch z aktuálního cílového branch (typicky `main`/`develop`).
2. Provádějte menší, logicky oddělené commity.
3. Před otevřením PR spusťte relevantní testy a kontrolní příkazy.
4. V PR popište **motivaci**, **co se změnilo** a **jak bylo ověřeno**.

## 2) Pravidla pro změny

- Neměňte runtime chování, pokud je úkol čistě dokumentační/refaktoringový.
- Při úpravách držte konzistentní styl existující části projektu.
- U větších změn preferujte postup po menších krocích (snadnější review i revert).

## 3) Django migrace

- Soubory v `*/migrations/*.py` jsou generované artefakty.
- Pokud úkol explicitně nepožaduje schématovou změnu, migrace **neupravujte ručně**.
- Pokud schématová změna proběhne, migrace generujte standardně přes Django nástroje.

## 4) Docstringy a dokumentace

- Pro psaní docstringů používejte projektový style guide:
  - `docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst`
- Dodržujte konkrétní a doménově relevantní popisy parametrů a návratových hodnot.
- Vyhýbejte se obecným formulacím bez informační hodnoty.

## 5) Testování

Před odevzdáním změn spusťte podle povahy úpravy zejména:

- `python -m compileall -q webclient` (rychlá kontrola syntaxe)
- `python manage.py test` (pokud je změna funkční)
- další modulové/integrační testy dle oblasti změny

Pokud test nelze v prostředí spustit, uveďte to transparentně v PR.

## 6) Commit message a PR

Doporučená struktura:

- Commit: krátký imperativní popis (např. „Přidání validace exportního payloadu“)
- PR:
  - **Motivation** (proč)
  - **Description** (co)
  - **Testing** (jak ověřeno)

## 7) Co zlepší review

- Přiložte minimální nutný diff bez vedlejších změn.
- U změn API/chování doplňte příklad vstupu/výstupu.
- U dokumentačních změn přidejte odkaz na aktualizovanou sekci dokumentace.
