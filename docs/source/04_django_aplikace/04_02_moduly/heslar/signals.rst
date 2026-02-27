HESLAR signály
==============

Definice signálů.

Funkce
------

.. py:function:: get_or_create_transaction(instance)

   Vrací or create transaction.

   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: save_ident_cely(sender, instance)

   Funkce pro uložení metadat hesláře.

.. py:function:: save_metadata_heslar(sender, instance)

   Funkce pro uložení metadat hesláře.

.. py:function:: save_metadata_katastr(sender, instance)

   Funkce pro uložení metadat katastru.

.. py:function:: save_metadata_kraj(sender, instance)

   Funkce pro uložení metadat kraje.

.. py:function:: save_metadata_okres(sender, instance)

   Uloží metadata okres.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: save_metadata_heslar_hierarchie(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

.. py:function:: save_metadata_heslar_datace(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

.. py:function:: save_metadata_heslar_dokument_typ_material_rada(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

.. py:function:: save_metadata_heslar_odkaz(sender, instance, created)

   Funkce pro uložení metadat heslář - odkaz.

.. py:function:: heslar_delete_repository_container(sender, instance)

   Provádí operaci heslar delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: ruian_katastr_delete_repository_container(sender, instance)

   Provádí operaci ruian katastr delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: ruian_kraj_delete_repository_container(sender, instance)

   Provádí operaci ruian kraj delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: ruian_okres_delete_repository_container(sender, instance)

   Provádí operaci ruian okres delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: delete_uppdate_related_heslar_hierarchie(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.

.. py:function:: delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.

.. py:function:: delete_uppdate_related_heslar_odkaz(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.

.. py:function:: delete_uppdate_related_heslar_datace(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.
