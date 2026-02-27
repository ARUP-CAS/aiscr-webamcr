DOKUMENT signály
================

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb dokumentu.
   Metoda se volá pred uložením záznamu.

.. py:function:: create_dokument_cast_vazby(sender, instance)

   Metoda pro vytvoření komponent vazeb dokument části.
   Metoda se volá pred uložením dokument části.

.. py:function:: dokument_save_metadata(sender, instance)

   Provádí operaci dokument save metadata.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: let_save_metadata(sender, instance)

   Provádí operaci let save metadata.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: dokument_delete_repository_container(sender, instance)

   Provádí operaci dokument delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: let_delete_repository_container(sender, instance)

   Provádí operaci let delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: dokument_cast_save_metadata_save(sender, instance, created)

   Provádí operaci dokument cast save metadata save.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param created: Vstupní hodnota ``created`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: dokument_cast_save_metadata_delete(sender, instance)

   Provádí operaci dokument cast save metadata delete.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: tvar_save(sender, instance, created)

   Provádí operaci tvar save.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param created: Vstupní hodnota ``created`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: tvar_delete(sender, instance)

   Provádí operaci tvar delete.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.
