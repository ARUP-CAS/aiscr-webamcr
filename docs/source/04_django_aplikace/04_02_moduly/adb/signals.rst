ADB signály
===========

Definice signálů.

Funkce
------

.. py:function:: adb_save_metadata(sender, instance, created)

   Provádí operaci adb save metadata.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``adb_save_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``adb_save_metadata``.

.. py:function:: vyskovy_bod_save_metadata(sender, instance)

   Provádí operaci vyskovy bod save metadata.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``vyskovy_bod_save_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``vyskovy_bod_save_metadata``.

.. py:function:: adb_delete_repository_container(sender, instance)

   Provádí operaci adb delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``adb_delete_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``adb_delete_repository_container``.

.. py:function:: vyskovy_bod_delete_repository_container(sender, instance)

   Provádí operaci vyskovy bod delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``vyskovy_bod_delete_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``vyskovy_bod_delete_repository_container``.
