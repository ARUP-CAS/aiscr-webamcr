# Contributing

Děkujeme, že chcete přispět do projektu AMČR.

Tento dokument shrnuje doporučený postup pro změny v kódu, dokumentaci a pull requestech.

## 1) Základní workflow

- Vytvořte si branch z aktuálního cílového branch (typicky `test`) s využitím čísla zdrojového issue a prefixu `feature/` či `bugfix/` (např. `bugfix/123`).
- Provádějte menší, logicky oddělené commity.
- Před sloučením PR spusťte relevantní testy a kontrolní příkazy.
- V PR popište **motivaci**, **co se změnilo** a **jak bylo ověřeno**.
- Aktualizujte průběžně konkrétní status v projektu AMCR pro související issue:
  - `To do` - čeká na zahájení
  - `In progress` - probíhá vývoj
  - `Review` - PR k dispozici pro review
  - `Deployment` - sloučeno a čeká na nasazení

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

## 5) Ověření

- Před odevzdáním změn spusťte podle povahy úpravy zejména `python -m compileall -q webclient` (rychlá kontrola syntaxe).
- Kontrolu vůči zadání požadavku v issue.
- Vlastní testy aplikovatelné na dané PR.

V PR vždy popište, zda a jak došlo k ověření funkčnosti.

## 6) Commit message a PR

Doporučená struktura:

- Commit: krátký imperativní popis (např. „Přidání validace exportního payloadu“)
- PR:
  - Číslo souvisejícího issue vč. křížku pro vytvoření linku (např. `#123`)
  - **Motivation** (proč)
  - **Description** (co)
  - **Testing** (jak ověřeno)

- Přiložte minimální nutný diff bez vedlejších změn.
- U změn API/chování doplňte příklad vstupu/výstupu.
- U dokumentačních změn přidejte odkaz na aktualizovanou sekci dokumentace, pokud nestačí úpravy docstrings.
- Do issue uveďte případné změny konfigurace a další úkony, které je nutné aplikovat při nasazení.

Pokud PR ještě není k review, veďte jej jako draft.

## 7) Release proces a uživatelské testování

Sloučení změn z `test` do `dev` větve a následující kroky koordinuje vždy odpovědný správce repozitáře (viz [`CODEOWNERS`](CODEOWNERS)).
