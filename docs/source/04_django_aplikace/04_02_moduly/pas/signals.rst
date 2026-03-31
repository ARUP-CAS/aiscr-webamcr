PAS signály
===========

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Metoda pro vytvoření historických a souborových vazeb samostatnýho náleze.

   Metoda se volá pred uložením záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.

.. py:function:: save_metadata_samostatny_nalez(sender, instance, created)

   Uloží metadata samostatny nalez.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.

.. py:function:: dokument_delete_container_soubor_vazby(sender, instance)

   Provádí operaci dokument delete container soubor vazby.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``dokument_delete_container_soubor_vazby``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``dokument_delete_container_soubor_vazby``.

.. py:function:: save_uzivatel_spoluprce(sender, instance)

   Uloží uzivatel spoluprce.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.

.. py:function:: delete_uzivatel_spoluprce_connections(sender, instance)

   Odstraní uzivatel spoluprce connections.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
