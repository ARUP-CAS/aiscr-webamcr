HESLAR signály
==============

Definice signálů.

Funkce
------

.. py:function:: get_or_create_transaction(instance)

   Vrací or create transaction.

   :param instance: Vstupní hodnota ``instance`` pro danou operaci.

.. py:function:: save_ident_cely(sender, instance)

   Funkce pro uložení metadat hesláře.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_heslar(sender, instance)

   Funkce pro uložení metadat hesláře.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_katastr(sender, instance)

   Funkce pro uložení metadat katastru.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_kraj(sender, instance)

   Funkce pro uložení metadat kraje.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_okres(sender, instance)

   Uloží metadata okres.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: save_metadata_heslar_hierarchie(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param created: Popis parametru ``created``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_heslar_datace(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param created: Popis parametru ``created``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_heslar_dokument_typ_material_rada(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param created: Popis parametru ``created``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: save_metadata_heslar_odkaz(sender, instance, created)

   Funkce pro uložení metadat heslář - odkaz.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param created: Popis parametru ``created``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: heslar_delete_repository_container(sender, instance)

   Provádí operaci heslar delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: ruian_katastr_delete_repository_container(sender, instance)

   Provádí operaci ruian katastr delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: ruian_kraj_delete_repository_container(sender, instance)

   Provádí operaci ruian kraj delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: ruian_okres_delete_repository_container(sender, instance)

   Provádí operaci ruian okres delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_uppdate_related_heslar_hierarchie(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: delete_uppdate_related_heslar_odkaz(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: delete_uppdate_related_heslar_datace(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.
