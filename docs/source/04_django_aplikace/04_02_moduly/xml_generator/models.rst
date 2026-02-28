XML_GENERATOR modely
====================

Definice modelů.

Třídy
------

.. py:class:: BaseAmcrModel

   Základní model pro všechny modely v aplikaci.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_ident_cely_link()

      Vrací ident cely link.


.. py:class:: ModelWithMetadata

   Implementuje komponentu ``ModelWithMetadata`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.

   .. py:method:: metadata()

      Provádí operaci metadata.

   .. py:method:: get_metadata_historicka()

      Metoda k získání vlastního souboru metadat dané verze z Fedory

      :param timestamp: Popis parametru ``timestamp``.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích metadat ve Fedoře pro tabulku historie

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param include_files: Vstupní hodnota ``include_files`` pro danou operaci.
      :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
      :param skip_container_check: Vstupní hodnota ``skip_container_check`` pro danou operaci.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param deleted_by_user: Vstupní hodnota ``deleted_by_user`` pro danou operaci.

   .. py:method:: _get_fedora_transaction()

      Vrací fedora transaction.

      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param old_ident_cely: Vstupní hodnota ``old_ident_cely`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param new_ident_cely: Vstupní hodnota ``new_ident_cely`` pro danou operaci.
      :param delete_container: Vstupní hodnota ``delete_container`` pro danou operaci.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.


Funkce
------

.. py:function:: check_if_task_queued(class_name, pk, task_name)

   Ověří if task queued.

   :param class_name: Vstupní hodnota ``class_name`` pro danou operaci.
   :param pk: Primární klíč zpracovávaného záznamu.
   :param task_name: Vstupní hodnota ``task_name`` pro danou operaci.
