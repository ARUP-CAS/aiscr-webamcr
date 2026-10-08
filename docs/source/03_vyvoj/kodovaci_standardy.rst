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

* ``method-docstring-style-reminder`` (lokální hook, **neblokující**)

  * kontroluje veřejné metody tříd v Python souborech,
  * běží skript ``docs/check_method_docstrings.py``,
  * vypíše upozornění, pokud docstring chybí nebo neodpovídá základní
    struktuře (shrnutí, ``:param:``, ``:return:``),
  * vrací vždy úspěšný kód, takže commit nezablokuje,
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
   * neblokující docstring hook vypisuje upozornění, která je potřeba průběžně
     zapracovávat podle style guide.

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
``Pre-commit`` (``.github/workflows/pre_commit.yml``). Spouští se při pull
requestu do větví ``main`` a ``test``, při pushi do ``main`` a ručně
(``workflow_dispatch``). Má dva nezávislé joby, které běží vždy, aby požadované
status checky nekončily stavem ``skipped``. Job ``pre-commit`` rozlišuje tři
režimy podle toho, odkud změna přichází:

* **none** – automatické větve (``pre-commit-fixes/*``, ``deps/python-pins-refresh``)
  nebo bot aktér: hooky se nespouští, check jen projde.
* **standard** – vývojové PR (typicky do ``test``): spustí se běžné hooky a při
  nalezených úpravách se založí opravný PR ``pre-commit-fixes/…``; pokud hooky
  selžou a žádná oprava nevznikne, check selže.
* **full** – cokoliv mířící do ``main`` (PR do ``main`` i push do ``main``),
  případně ruční ``workflow_dispatch`` se zapnutým vstupem ``dependencies``:
  jako ``standard``, navíc se přes ``docs/licenses/convert_to_rst.py``
  regeneruje dokumentace závislostí, aby výsledný image z ``main`` odpovídal
  závislostem i dokumentaci.

Druhý job ``refresh-python-pins`` po pushi do ``main`` (nebo ručně) obnoví
tranzitivní piny v ``webclient/requirements*.txt`` a založí/aktualizuje PR
``deps/python-pins-refresh`` do větve ``test``.

Automaticky zakládané PR používá GitHub App token, aby jejich události spouštěly
navazující workflows (PR založené přes ``GITHUB_TOKEN`` běhy nespouští); větve
``pre-commit-fixes/*`` a ``deps/python-pins-refresh`` jsou proto v jobu
``pre-commit`` vynechány (režim ``none``), aby nevznikala řetězená opravná PR.

.. mermaid::
   :align: center

   flowchart TD
       subgraph PC["job: pre-commit"]
           direction TB
           M{"automatická větev nebo bot aktér?"}
           M -- "ano" --> NONE["režim none - žádné hooky, check projde"]
           M -- "ne" --> MAIN{"PR do main, push do main nebo dispatch s dependencies?"}
           MAIN -- "ano" --> FULL["režim full - hooky + regenerace dokumentace závislostí"]
           MAIN -- "ne" --> STD["režim standard - běžné hooky (vývojové PR)"]
           FULL --> FIX["při změnách založí nebo aktualizuje opravný PR pre-commit-fixes/…"]
           STD --> FIX
       end

       subgraph RP["job: refresh-python-pins"]
           direction TB
           G2{"push do main nebo dispatch s upgrade_python_pins?"}
           G2 -- "ano" --> W2["checkout větve test, compile --upgrade, založí nebo aktualizuje PR deps/python-pins-refresh"]
           G2 -- "ne" --> N2["bez akce (check projde)"]
       end

       T([Trigger: PR do main nebo test, push do main, workflow_dispatch]) --> M
       T --> G2
