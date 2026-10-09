Kódovací standardy
==================

Tato stránka popisuje pravidla, která musí vývojář splnit před odesláním změn.
Kromě obecných doporučení (PEP8) jsou závazná i automatická pravidla spuštěná
přes ``pre-commit``.

Pre-commit pravidla
-------------------

Projekt má nakonfigurované následující hooky v souboru
``.pre-commit-config.yaml``:

* ``isort``

  * sjednocuje pořadí importů,
  * používá profil ``black``.

* ``black``

  * formátuje Python kód,
  * používá délku řádku ``120`` znaků.

* ``flake8``

  * statická kontrola kvality Python kódu,
  * upozorňuje na porušení PEP8 a běžné chyby.

* ``method-docstring-style-reminder`` (lokální hook)

  * kontroluje veřejné funkce a metody tříd v Python souborech,
  * běží skript ``docs/check_method_docstrings.py``,
  * vypíše upozornění, pokud docstring chybí nebo neodpovídá základní
    struktuře (shrnutí, ``:param:``, ``:return:``),
  * při nalezených nedostatcích vrací nenulový kód a blokuje commit,
  * slouží jako průběžná připomínka standardu popsaného v dokumentu
    ``04_django_aplikace/04_01_core/docstring_style_guide``.

* ``generate-module-docs``

  * regeneruje dokumentaci modulů,
  * spouští se vždy (``always_run: true``).

* ``generate-selenium-test-docs``

  * regeneruje dokumentaci selenium testů,
  * spouští se vždy (``always_run: true``).

Poznámka: Hooky jsou globálně nastavené s výjimkou cesty ``migrations``
(``exclude: (migrations)``).

Jak zajistit správný běh
------------------------

1. Nainstaluj závislosti pro vývoj (včetně ``pre-commit``).
2. Aktivuj hooky v lokálním repozitáři:

   .. code-block:: bash

      pre-commit install

3. Ověř kontrolu na všech souborech:

   .. code-block:: bash

      pre-commit run --all-files

4. Před commitem oprav nalezené problémy:

   * formátovací hooky (``isort``, ``black``) často opraví soubory automaticky,
   * upozornění docstring hooku oprav podle style guide, aby kontrola prošla.

Doporučený workflow vývojáře
----------------------------

* Po větší změně spusť lokálně ``pre-commit run --all-files``.
* Před vytvořením PR zkontroluj, že je pracovní strom čistý
  (bez nechtěně přegenerovaných souborů).
* Pro jednotný styl docstringů používej checklist v dokumentu
  ``docstring_style_guide.rst``.

Kontrola v CI (workflow ``Pre-commit``)
---------------------------------------

Kromě lokálního spuštění vynucuje pravidla i workflow GitHub Actions
``Pre-commit`` (``.github/workflows/pre_commit.yml``). Má jediný požadovaný job
``pre-commit``. Spouští se při otevření, znovuotevření nebo aktualizaci PR do
``main`` či ``test``, při pushi do ``main`` a ručně (``workflow_dispatch``).
Úplná pravidla včetně CLI/API příkladů jsou v
`CONTRIBUTING.md <https://github.com/ARUP-CAS/aiscr-webamcr/blob/test/CONTRIBUTING.md#automatické-kontroly-a-opravy-ci>`_.

Způsobilé PR do ``main`` a push do ``main`` používají režim ``refresh``:
obnova tranzitivních pinů, instalace výsledných závislostí, regresní testy,
generování dokumentace přes ``docs/licenses/convert_to_rst.py`` a hooky
proběhnou v tomto pořadí ve stejném jobu. Běžné PR do ``test`` používají
``checks``: kompilace bez upgradu a standardní kontroly. Přímé piny v
``requirements*.in`` se automaticky neupgradují.

Ruční vstup ``mode`` nabízí ``checks`` (kontroly), ``docs`` (kontroly a
dokumentace bez upgradu; výchozí) a ``refresh`` (kontroly, obnova pinů a
dokumentace). Samostatný vstup ``bypass_docstring_exclusions`` rozšíří rozsah
docstring kontroly; neobchází vyloučení celého běhu.

Účty s příponou ``[bot]`` včetně release App, PR autora Dependabot a zdrojové
větve ``dependabot/*``, ``pre-commit-fixes/*`` a historická
``deps/python-pins-refresh`` jsou vyloučeny. Job úspěšně skončí bez změn nebo
opravného PR a vypíše důvod v summary. To platí i při ručním spuštění či
lidské aktualizaci vyloučeného PR; release push ``CITATION.cff`` tak nezaloží
opravné PR mezi kroky vydání.

Checkout používá zdrojový SHA původního PR, u pushů a ručních běhů SHA události.
Neimportuje historii cílové větve. Po všech generátorech a hookách se změny
stageují společně. Jediné opravné PR ``pre-commit-fixes/…`` míří do zdrojové
větve původního PR, po pushi do ``main`` do ``main`` a po ručním spuštění do
vybrané větve. Opakování aktualizuje existující PR; prázdný diff žádné nevytvoří.
Publikace používá GitHub App token a vyloučení opravných větví brání rekurzi.

Společný report popisu opravného PR, sticky komentáře původního PR a Actions
summary čte jediný snapshot staged diffu před commitem. Odděluje provedené
operace od skutečně změněných souborů, uvádí typy změn a počty řádků, režim,
zdrojový commit, cílovou větev a odkazy na workflow a publikované PR. Diagnostika
obsahuje sbalitelný konec logu hooků; výpisy jsou velikostně omezené a úplný log
je dostupný v odkazovaném workflow. Selhání zpracování zabrání publikaci;
nenulový kód hooků zůstává selháním checku i po nabídnutí automatických oprav.
Selhání publikace je uvedeno samostatně.

.. mermaid::
   :align: center

   flowchart TD
       T["PR do main/test, push do main, ruční spuštění"] --> G{"Vyloučený účet, autor nebo větev?"}
       G -- "ano" --> N["Úspěšný check bez změn; důvod v summary"]
       G -- "ne" --> M["main: refresh; test: checks; ručně: mode"]
       M --> C["Checkout zdrojového SHA; kompilace, upgrade jen v refresh"]
       C --> I["Instalace závislostí a regresní testy"]
       I --> D["Dokumentace závislostí v docs a refresh"]
       D --> H["Hooky; zachování jejich návratového kódu"]
       H --> S["Stage a společný snapshot změn"]
       S --> F{"Změnily se soubory?"}
       F -- "ano" --> P["Vytvořit nebo aktualizovat jediné opravné PR"]
       F -- "ne" --> R["Společné reporty a výsledný check"]
       P --> R
       C -- "selhání" --> E["Report selhání; bez publikace; check selže"]
       I -- "selhání" --> E
       D -- "selhání" --> E
