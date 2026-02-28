DOKUMENT signály
================

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Před uložením dokumentu připraví vazby historie a souborů.

   :param sender: Model, který signal vyvolal.
   :param instance: Ukládaná instance dokumentu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: create_dokument_cast_vazby(sender, instance)

   Před uložením části dokumentu zajistí vytvoření komponentové vazby.

   :param sender: Model, který signal vyvolal.
   :param instance: Ukládaná instance části dokumentu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: dokument_save_metadata(sender, instance)

   Po uložení dokumentu synchronizuje metadata navázaných objektů.

   :param sender: Model, který signal vyvolal.
   :param instance: Uložená instance dokumentu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: let_save_metadata(sender, instance)

   Po uložení letu zapíše metadata do repozitáře.

   :param sender: Model, který signal vyvolal.
   :param instance: Uložená instance letu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: dokument_delete_repository_container(sender, instance)

   Po smazání dokumentu odstraní repozitářové vazby a přegeneruje metadata.

   :param sender: Model, který signal vyvolal.
   :param instance: Smazaná instance dokumentu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: let_delete_repository_container(sender, instance)

   Po smazání letu zapíše jeho odstranění do repozitáře.

   :param sender: Model, který signal vyvolal.
   :param instance: Smazaná instance letu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: dokument_cast_save_metadata_save(sender, instance, created)

   Po uložení části dokumentu synchronizuje metadata navázaných záznamů.

   :param sender: Model, který signal vyvolal.
   :param instance: Uložená instance části dokumentu.
   :param created: Příznak, zda byla část dokumentu právě vytvořena.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: dokument_cast_save_metadata_delete(sender, instance)

   Po smazání části dokumentu přepočítá metadata navázaných objektů.

   :param sender: Model, který signal vyvolal.
   :param instance: Smazaná instance části dokumentu.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: tvar_save(sender, instance, created)

   Po uložení tvaru zajistí zápis metadat souvisejícího dokumentu.

   :param sender: Model, který signal vyvolal.
   :param instance: Uložená instance tvaru.
   :param created: Příznak, zda byl tvar právě vytvořen.
   :param kwargs: Dodatečné argumenty předané Django signalem.

.. py:function:: tvar_delete(sender, instance)

   Po smazání tvaru přepočítá metadata navázaného dokumentu.

   :param sender: Model, který signal vyvolal.
   :param instance: Smazaná instance tvaru.
   :param kwargs: Dodatečné argumenty předané Django signalem.
