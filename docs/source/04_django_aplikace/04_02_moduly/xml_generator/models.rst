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

      Textová reprezentace objektu.

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

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
      :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.

   .. py:method:: metadata()

      Provádí operaci metadata.

   .. py:method:: get_metadata_historicka()

      Metoda k získání vlastního souboru metadat dané verze z Fedory

      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích metadat ve Fedoře pro tabulku historie

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param include_files: Příznak ``include_files`` určující průběh nebo rozsah zpracování.
      :param close_transaction: Příznak ``close_transaction`` určující průběh nebo rozsah zpracování.
      :param skip_container_check: Příznak ``skip_container_check`` určující průběh nebo rozsah zpracování.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param deleted_by_user: Příznak ``deleted_by_user`` určující průběh nebo rozsah zpracování.

   .. py:method:: _get_fedora_transaction()

      Vrací fedora transaction.

      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param close_transaction: Příznak ``close_transaction`` určující průběh nebo rozsah zpracování.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param old_ident_cely: Identifikátor ``old_ident_cely`` používaný pro dohledání cílového záznamu.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param new_ident_cely: Identifikátor ``new_ident_cely`` používaný pro dohledání cílového záznamu.
      :param delete_container: Příznak ``delete_container`` určující průběh nebo rozsah zpracování.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.


Funkce
------

.. py:function:: check_if_task_queued(class_name, pk, task_name)

   Ověří if task queued.

   :param class_name: Název nebo typ ``class_name`` používaný pro volbu cílové logiky.
   :param pk: Primární klíč zpracovávaného záznamu.
   :param task_name: Textový název nebo klíč ``task_name`` používaný v rámci operace.
