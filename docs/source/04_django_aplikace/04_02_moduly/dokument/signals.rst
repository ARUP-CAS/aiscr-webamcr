DOKUMENT signály
================

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Před uložením dokumentu připraví vazby historie a souborů.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Ukládaná instance dokumentu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: create_dokument_cast_vazby(sender, instance)

   Před uložením části dokumentu zajistí vytvoření komponentové vazby.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Ukládaná instance části dokumentu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: dokument_save_metadata(sender, instance)

   Po uložení dokumentu synchronizuje metadata navázaných objektů.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Uložená instance dokumentu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: let_save_metadata(sender, instance)

   Po uložení letu zapíše metadata do repozitáře.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Uložená instance letu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: dokument_delete_repository_container(sender, instance)

   Po smazání dokumentu odstraní repozitářové vazby a přegeneruje metadata.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Smazaná instance dokumentu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: let_delete_repository_container(sender, instance)

   Po smazání letu zapíše jeho odstranění do repozitáře.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Smazaná instance letu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: dokument_cast_save_metadata_save(sender, instance, created)

   Po uložení části dokumentu synchronizuje metadata navázaných záznamů.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Uložená instance části dokumentu.
   - ``created``: Parametr ``created`` ovlivňuje větvení podmínek.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: dokument_cast_save_metadata_delete(sender, instance)

   Po smazání části dokumentu přepočítá metadata navázaných objektů.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Smazaná instance části dokumentu.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.


.. py:function:: tvar_save(sender, instance, created)

   Uloží metadata dokumentu při uložení tvaru.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal (Tvar).
   - ``instance``: Uložená instance tvaru.
   - ``created``: Zda je nová instance nebo aktualizace.
   - ``kwargs``: Dodatečné argumenty Djangoho signálu.


.. py:function:: tvar_delete(sender, instance)

   Po smazání tvaru přepočítá metadata navázaného dokumentu.

   **Parametry:**

   - ``sender``: Model, který signal vyvolal.
   - ``instance``: Smazaná instance tvaru.
   - ``kwargs``: Dodatečné argumenty předané Django signalem.

