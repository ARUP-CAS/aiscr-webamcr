EZ signály
==========

Definice signálů.

Funkce
------

.. py:function:: create_ez_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb externího zdroje.

   Metoda se volá pred uložením záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_ez_vazby``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_ez_vazby``.

.. py:function:: externi_zdroj_save_metadata(sender, instance)

   Provádí operaci externi zdroj save metadata.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``externi_zdroj_save_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``on_commit()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``externi_zdroj_save_metadata``.

.. py:function:: delete_externi_zdroj_repository_container(sender, instance)

   Odstraní externi zdroj repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_externi_zdroj_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``record_deletion()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_externi_zdroj_repository_container``.
