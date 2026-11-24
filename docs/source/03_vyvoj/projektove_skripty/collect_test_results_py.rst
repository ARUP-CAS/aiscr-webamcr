Skript collect_test_results.py
==============================

Automaticky generovaná dokumentace skriptu ``scripts/collect_test_results.py``.

Přehled modulu
--------------

Ověří stažené výsledky konkrétního pokusu před publikací do GitHub Actions.

Funkce
------

.. py:function:: report(directory, identity, mode, number, output_path, summary_path)

   Zveřejní pouze úplný aktuální výsledek a zachová neúspěch procesu.

   :param directory: Adresář staženého pokusu.
   :param identity: Očekávaná identita.
   :param mode: Očekávaný režim.
   :param number: Očekávané číslo testu.
   :param output_path: Soubor GITHUB_OUTPUT.
   :param summary_path: Soubor GITHUB_STEP_SUMMARY.
   :return: Návratový kód pokusu.

.. py:function:: main(argv)

   Nejprve určí bezpečné názvy ke stažení, potom ověří celý balík.

   :param argv: Volitelné argumenty příkazové řádky.
   :return: Nula při úspěchu, jinak nenulový výsledek.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/collect_test_results.py
   :language: python
   :linenos:
