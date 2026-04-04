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

          :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_ident_cely_link()

      Vrací ident cely link.

      :return: Vrací hodnotu podle větve zpracování.


.. py:class:: ModelWithMetadata

   Implementuje komponentu ``ModelWithMetadata`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      :param error_message: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.

          :return: Vrací atribut objektu.

   .. py:method:: metadata()

      Provádí operaci metadata.

      :return: Vrací výsledek volání ``get_metadata()``.

   .. py:method:: get_metadata_historicka()

      Metoda k získání vlastního souboru metadat dané verze z Fedory

      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.

          :return: Vrací výsledek volání ``get_metadata_historicka()``.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích metadat ve Fedoře pro tabulku historie

      :return: Vrací proměnná ``results``.

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``_get_fedora_transaction()``, ``isinstance()``, pracuje se s atributy ``add_updated_ident_cely``, ``uid``, ovlivňuje větvení podmínek.
      :param include_files: Parametr ``include_files`` ovlivňuje větvení podmínek.
      :param close_transaction: Parametr ``close_transaction`` předává se do volání ``warning()``, ``debug()``, ovlivňuje větvení podmínek.
      :param skip_container_check: Parametr ``skip_container_check`` slouží jako vstup pro logiku funkce ``save_metadata``.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``_get_fedora_transaction()``, ``save_metadata()``.
      :param deleted_by_user: Parametr ``deleted_by_user`` ovlivňuje větvení podmínek.

   .. py:method:: _get_fedora_transaction()

      Vrací fedora transaction.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``isinstance()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Načtená data odpovídající zadaným vstupům.

          :raises ValueError: Vyvolá se s textem "No Fedora transaction"; nebo s textem "fedora_transaction must be a FedoraTransaction class object".

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``_get_fedora_transaction()``, ``FedoraRepositoryConnector()``, pracuje se s atributy ``mark_transaction_as_closed``.
      :param close_transaction: Parametr ``close_transaction`` ovlivňuje větvení podmínek.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param old_ident_cely: Identifikátor ``old_ident_cely`` používaný pro dohledání cílového záznamu.
      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``debug()``, ``isinstance()``, pracuje se s atributy ``uid``, ``post_commit_tasks``, ovlivňuje větvení podmínek.
      :param new_ident_cely: Identifikátor ``new_ident_cely`` používaný pro dohledání cílového záznamu.
      :param delete_container: Parametr ``delete_container`` předává se do volání ``record_ident_change()``.

          :raises ValueError: Vyvolá se s textem "No Fedora transaction"; nebo s textem "fedora_transaction must be a FedoraTransaction class object".

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.


Funkce
------

.. py:function:: check_if_task_queued(class_name, pk, task_name)

   Ověří if task queued.

   :param class_name: Parametr ``class_name`` předává se do volání ``warning()``, ``debug()``, ovlivňuje větvení podmínek.
   :param pk: Primární klíč zpracovávaného záznamu.
   :param task_name: Textový název nebo klíč ``task_name`` používaný v rámci operace.

       :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
