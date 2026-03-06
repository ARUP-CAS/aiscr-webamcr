ARCH_Z signály
==============

Definice signálů.

Funkce
------

.. py:function:: invalidate_arch_z_related_models()

   Provádí operaci invalidate arch z related models.

.. py:function:: create_arch_z_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb arch záznamu.

   Metoda se volá pred uložením arch záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_arch_z_vazby``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``str()``, pracuje se s atributy ``pk``, ``historie``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_arch_z_vazby``.

.. py:function:: create_arch_z_metadata(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_arch_z_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``evaluate_pristupnost_change()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_arch_z_metadata``.

.. py:function:: update_akce_snapshot(sender, instance)

   Aktualizuje akce snapshot.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``update_akce_snapshot``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``update_akce_snapshot``.

.. py:function:: create_externi_odkaz_metadata(sender, instance)

   Funkce pro aktualizaci metadat externího odkazu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_externi_odkaz_metadata``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_externi_odkaz_metadata``.

.. py:function:: delete_arch_z_repository_container_and_connections(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_arch_z_repository_container_and_connections``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``dokumentacni_jednotky_akce``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_arch_z_repository_container_and_connections``.

.. py:function:: delete_arch_z_repository_update_connected_records(sender, instance)

   Odstraní arch z repository update connected records.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_arch_z_repository_update_connected_records``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_arch_z_repository_update_connected_records``.

.. py:function:: delete_externi_odkaz_repository_container(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_externi_odkaz_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal_arch_z``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_externi_odkaz_repository_container``.
