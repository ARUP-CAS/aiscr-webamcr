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

   Aktualizuje identifikátor hesla po uložení.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``check_container_deleted_or_not_exists()``, ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

   :raises Exception: Vyvolá se při splnění podmínky ``not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, 'heslar')``.

.. py:function:: save_metadata_heslar(sender, instance)

   Vytváří metadata pro heslo po uložení.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_katastr(sender, instance)

   Funkce pro uložení metadat katastru.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_kraj(sender, instance)

   Funkce pro uložení metadat kraje.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_okres(sender, instance)

   Uloží metadata okres.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_heslar_hierarchie(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_heslar_datace(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_heslar_dokument_typ_material_rada(sender, instance, created)

   Funkce pro uložení metadat heslář - hierarchie.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` ovlivňuje větvení podmínek.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: save_metadata_heslar_odkaz(sender, instance, created)

   Funkce pro uložení metadat heslář - odkaz.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: heslar_delete_repository_container(sender, instance)

   Provádí operaci heslar delete repository container.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: ruian_katastr_delete_repository_container(sender, instance)

   Provádí operaci ruian katastr delete repository container.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: ruian_kraj_delete_repository_container(sender, instance)

   Provádí operaci ruian kraj delete repository container.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: ruian_okres_delete_repository_container(sender, instance)

   Provádí operaci ruian okres delete repository container.

   :param sender: Model třídy, která poslala signál.
   :param instance: Instance modelu, která byla uložena.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: delete_uppdate_related_heslar_hierarchie(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.

   :param sender: Model třídy, která poslala signál.
   :param instance: Instance modelu, která byla uložena.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.

   :param sender: Model třídy, která poslala signál.
   :param instance: Instance modelu, která byla uložena.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: delete_uppdate_related_heslar_odkaz(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
   :param kwargs: Další klíčové argumenty signálu.

.. py:function:: delete_uppdate_related_heslar_datace(sender, instance)

   Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.

   :param sender: Model třídy, která poslala signál.
   :param instance: Parametr ``instance`` pracuje se s atributy ``obdobi``.
   :param kwargs: Další klíčové argumenty signálu.
