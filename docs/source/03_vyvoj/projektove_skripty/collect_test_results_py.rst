Skript collect_test_results.py
==============================

Automaticky generovaná dokumentace skriptu ``scripts/collect_test_results.py``.

Přehled modulu
--------------

Ověří stažené výsledky konkrétního pokusu před publikací do GitHub Actions.

Funkce
------

.. py:function:: command_data(text)

   Zakóduje text jako data příkazu workflow, aby nemohl začít další příkaz.

   :param text: Zobrazovaná diagnostika.
   :return: Text s ``%``, CR a LF zakódovanými podle pravidel GitHub Actions.

.. py:function:: code_span(text)

   Vloží text do kódového úseku Markdownu bez ohledu na obsažené zpětné apostrofy.

   :param text: Jednořádkový text.
   :return: Kódový úsek s oddělovačem delším než nejdelší běh apostrofů v textu.

.. py:function:: report(directory, identity, mode, number, output_path, summary_path)

   Zveřejní pouze úplný aktuální výsledek a zachová neúspěch procesu.

   U chybového výsledku uvede zaznamenanou příčinu v souhrnu kroku
   a v jediné chybové anotaci zakódované jako data příkazu workflow.

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
