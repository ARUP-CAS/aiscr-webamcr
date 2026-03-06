CORE signály
============

Definice signálů.

Funkce
------

.. py:function:: soubor_get_rozsah(sender, instance)

   Provádí operaci soubor get rozsah.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``soubor_get_rozsah``.
   :param instance: Parametr ``instance`` předává se do volání ``PdfReader()``, ``open()``, pracuje se s atributy ``binary_data``, ``nazev``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``soubor_get_rozsah``.

.. py:function:: soubor_save_update_record_metadata(sender, instance)

   Provádí operaci soubor save update record metadata.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``soubor_save_update_record_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``isinstance()``, pracuje se s atributy ``close_active_transaction_when_finished``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``soubor_save_update_record_metadata``.

.. py:function:: soubor_delete_connections(sender, instance)

   Provádí operaci soubor delete connections.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``soubor_delete_connections``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``historie``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``soubor_delete_connections``.

.. py:function:: soubor_delete_update_metadata(sender, instance)

   Provádí operaci soubor delete update metadata.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``soubor_delete_update_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``isinstance()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``soubor_delete_update_metadata``.
