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
