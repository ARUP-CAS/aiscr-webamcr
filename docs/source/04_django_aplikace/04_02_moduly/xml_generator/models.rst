XML_GENERATOR modely
====================

Definice modelů.

Třídy
------

.. py:class:: BaseAmcrModel

   Základní model pro všechny modely v aplikaci.

   **Metody:**

   .. py:method:: __str__()

   .. py:method:: get_ident_cely_link()


.. py:class:: ModelWithMetadata

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: create_transaction()

   .. py:method:: metadata()

   .. py:method:: get_metadata_historicka()

      Metoda k získání vlastního souboru metadat dané verze z Fedory

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích metadat ve Fedoře pro tabulku historie

   .. py:method:: save_metadata()

   .. py:method:: save_record_deletion_record()

   .. py:method:: _get_fedora_transaction()

   .. py:method:: record_deletion()

   .. py:method:: record_ident_change()

   .. py:method:: get_by_ident_cely()


Funkce
------

.. py:function:: check_if_task_queued(class_name, pk, task_name)

   Popis není k dispozici.
