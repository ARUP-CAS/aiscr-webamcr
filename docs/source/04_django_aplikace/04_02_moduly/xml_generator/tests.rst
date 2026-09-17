XML_GENERATOR tests
===================

Modul tests.

Přehled modulu
--------------

Testy determinismu pořadí prvků v generovaných XML metadatech.

Pokrývají :func:`xml_generator.generator.stable_related_records`, která doplňuje primární klíč
jako poslední kritérium řazení navázaných záznamů. Bez něj PostgreSQL vrací řádky se shodným
řadicím klíčem v libovolném pořadí a tentýž nezměněný záznam generuje odlišné XML, což vede
ke vzniku zbytečných verzí v OCFL úložišti.

Třídy
------

.. py:class:: StableRelatedRecordsTest

   Testuje doplnění stabilního řazení navázaných záznamů.

   **Metody:**

   .. py:method:: test_doplni_pk_k_nejednoznacnemu_razeni()

      Model řazený podle neunikátního pole dostane ``pk`` jako poslední kritérium.

   .. py:method:: test_zachova_existujici_razeni_modelu()

      Původní řadicí kritéria modelu zůstanou zachována i s doplněným tiebreakerem.

   .. py:method:: test_nepridava_pk_kdyz_uz_razeni_obsahuje_id()

      Řazení, které už obsahuje ``id``, je jednoznačné a nepotřebuje další kritérium.

   .. py:method:: test_respektuje_razeni_nastavene_na_querysetu()

      Explicitní ``order_by`` na QuerySetu má přednost před výchozím řazením modelu.

   .. py:method:: test_objekt_bez_querysetu_projde_beze_zmeny()

      Kolekce, která není QuerySet, se vrátí beze změny a nezpůsobí chybu.


.. py:class:: SouborOrderingTest

   Testuje jednoznačnost výchozího řazení modelu :class:`core.models.Soubor`.

   **Metody:**

   .. py:method:: test_razeni_obsahuje_tiebreaker()

      ``nazev`` není unikátní, proto musí řazení končit primárním klíčem.

