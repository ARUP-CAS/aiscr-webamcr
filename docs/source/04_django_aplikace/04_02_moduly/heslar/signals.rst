HESLAR signály
==============

Definice signálů.

Funkce
------

.. py:function:: get_or_create_transaction(instance)

   Vrací or create transaction.

   :param instance: Parametr ``instance`` pracuje se s atributy ``active_transaction``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, výsledek volání ``FedoraTransaction()``.

.. py:function:: save_ident_cely(sender, instance)

   Funkce pro uložení metadat hesláře.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_ident_cely``.
   :param instance: Parametr ``instance`` předává se do volání ``check_container_deleted_or_not_exists()``, ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_ident_cely``.

   :raises Exception: Vyvolá se při splnění podmínky ``not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, 'heslar')``.

.. py:function:: save_metadata_heslar(sender, instance)

   Funkce pro uložení metadat hesláře.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar``.

.. py:function:: save_metadata_katastr(sender, instance)

   Funkce pro uložení metadat katastru.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_katastr``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_katastr``.

.. py:function:: save_metadata_kraj(sender, instance)

   Funkce pro uložení metadat kraje.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_kraj``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_kraj``.

.. py:function:: save_metadata_okres(sender, instance)

   Uloží metadata okres.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_okres``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_okres``.

.. py:function:: save_metadata_heslar_hierarchie(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.

.. py:function:: save_metadata_heslar_datace(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.

.. py:function:: save_metadata_heslar_dokument_typ_material_rada(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_dokument_typ_material_rada``.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_dokument_typ_material_rada``.

.. py:function:: save_metadata_heslar_odkaz(sender, instance, created)

   Funkce pro uložení metadat heslář - odkaz.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.

.. py:function:: heslar_delete_repository_container(sender, instance)

   Provádí operaci heslar delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``heslar_delete_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``heslar_delete_repository_container``.

.. py:function:: ruian_katastr_delete_repository_container(sender, instance)

   Provádí operaci ruian katastr delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_katastr_delete_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_katastr_delete_repository_container``.

.. py:function:: ruian_kraj_delete_repository_container(sender, instance)

   Provádí operaci ruian kraj delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_kraj_delete_repository_container``.
   :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_kraj_delete_repository_container``.

.. py:function:: ruian_okres_delete_repository_container(sender, instance)

   Provádí operaci ruian okres delete repository container.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.
   :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.

.. py:function:: delete_uppdate_related_heslar_hierarchie(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.
   :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.

.. py:function:: delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.
   :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.

.. py:function:: delete_uppdate_related_heslar_odkaz(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_odkaz``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_odkaz``.

.. py:function:: delete_uppdate_related_heslar_datace(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_datace``.
   :param instance: Parametr ``instance`` pracuje se s atributy ``obdobi``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_datace``.
