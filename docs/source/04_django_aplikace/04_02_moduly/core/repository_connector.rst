CORE repository_connector
=========================

Modul repository_connector.

Třídy
------

.. py:class:: FedoraValidationError

   Implementuje komponentu ``FedoraValidationError`` v rámci aplikace.


.. py:class:: FedoraError

   Implementuje komponentu ``FedoraError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param url: Vstupní hodnota ``url`` pro danou operaci.
      :param message: Vstupní hodnota ``message`` pro danou operaci.
      :param code: Vstupní hodnota ``code`` pro danou operaci.
      :param headers: Vstupní hodnota ``headers`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.


.. py:class:: FedoraUpdatedByAnotherTransactionError

   Implementuje komponentu ``FedoraUpdatedByAnotherTransactionError`` v rámci aplikace.


.. py:class:: IdentChangeFedoraError

   Implementuje komponentu ``IdentChangeFedoraError`` v rámci aplikace.


.. py:class:: FedoraNoResponseError

   Implementuje komponentu ``FedoraNoResponseError`` v rámci aplikace.


.. py:class:: RepositoryBinaryFile

   Implementuje komponentu ``RepositoryBinaryFile`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_url_without_domain()

      Vrací url without domain.

      :param url: Vstupní hodnota ``url`` pro danou operaci.

   .. py:method:: url_without_domain()

      Provádí operaci url without domain.

   .. py:method:: uuid()

      Provádí operaci uuid.

   .. py:method:: _calculate_sha_512()

      Provádí operaci calculate sha 512.

      :return: Vrací výsledek provedené operace.

   .. py:method:: size_mb()

      Provádí operaci size mb.

   .. py:method:: mime_type()

      Provádí operaci mime type.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param url: Vstupní hodnota ``url`` pro danou operaci.
      :param content: Vstupní hodnota ``content`` pro danou operaci.
      :param filename: Vstupní hodnota ``filename`` pro danou operaci.


.. py:class:: FedoraRequestType

   Implementuje komponentu ``FedoraRequestType`` v rámci aplikace.


.. py:class:: FedoraRepositoryConnector

   Implementuje komponentu ``FedoraRepositoryConnector`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param transaction: Vstupní hodnota ``transaction`` pro danou operaci.
      :param skip_container_check: Vstupní hodnota ``skip_container_check`` pro danou operaci.

   .. py:method:: _get_model_name()

      Vrací model name.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_rdf_inset_data()

      Vrací rdf inset data.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_creator()

      Vrací creator.

      :param url: Vstupní hodnota ``url`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _update_creator()

      Aktualizuje creator.

      :param request_type: Vstupní hodnota ``request_type`` pro danou operaci.
      :param uuid: Vstupní hodnota ``uuid`` pro danou operaci.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_base_url()

      Vrací base url.

   .. py:method:: _get_request_url()

      Vrací request url.

      :param request_type: Vstupní hodnota ``request_type`` pro danou operaci.
      :param uuid: Vstupní hodnota ``uuid`` pro danou operaci.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: check_container_deleted()

      Ověří container deleted.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.

   .. py:method:: check_container_deleted_or_not_exists()

      Ověří container deleted or not exists.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.

   .. py:method:: _get_auth()

      Vrací auth.

      :param request_type: Vstupní hodnota ``request_type`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _send_request()

      Odešle request.

      :param url: Vstupní hodnota ``url`` pro danou operaci.
      :param request_type: Vstupní hodnota ``request_type`` pro danou operaci.
      :param headers: Vstupní hodnota ``headers`` pro danou operaci.
      :param data: Vstupní hodnota ``data`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _create_container()

      Vytvoří container.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: create_link()

      Vytvoří link. v aplikaci.

      :param ident_cely_proxy: Vstupní hodnota ``ident_cely_proxy`` pro danou operaci.

   .. py:method:: container_exists()

      Provádí operaci container exists.

   .. py:method:: _connect_deleted_container()

      Provádí operaci connect deleted container.

      :return: Vrací výsledek provedené operace.

   .. py:method:: link_exists()

      Provádí operaci link exists.

   .. py:method:: _check_container()

      Ověří container.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _create_binary_file_container()

      Vytvoří binary file container.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _check_binary_file_container()

      Ověří binary file container.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _generate_metadata()

      Vygeneruje metadata.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: get_metadata()

      Vrací metadata. v aplikaci.

      :param update: Vstupní hodnota ``update`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_metadata_historicka()

      Metoda varacející konkrétní verzi metadat

      :param timestamp: Popis parametru ``timestamp``.

   .. py:method:: parse_historie()

      Zpracuje historie. v aplikaci.

      :param response_text: Vstupní hodnota ``response_text`` pro danou operaci.

   .. py:method:: get_historie_metadat()

      Metoda k získání info o verzích metadat

   .. py:method:: get_historie_file()

      Metoda k získání info o verzích souborů

      :param uuid: Popis parametru ``uuid``.

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param update: Vstupní hodnota ``update`` pro danou operaci.

   .. py:method:: save_binary_file()

      Uloží binary file.

      :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.
      :param content_type: Vstupní hodnota ``content_type`` pro danou operaci.
      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :param save_thumbs: Vstupní hodnota ``save_thumbs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: __generate_thumb()

      Vygeneruje thumb. v aplikaci.

      :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.
      :param file_content: Vstupní hodnota ``file_content`` pro danou operaci.
      :param large: Vstupní hodnota ``large`` pro danou operaci.

   .. py:method:: save_thumbs()

      Uloží thumbs. v aplikaci.

      :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.
      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :param uuid: Vstupní hodnota ``uuid`` pro danou operaci.
      :param update: Vstupní hodnota ``update`` pro danou operaci.
      :param ident_cely_old: Vstupní hodnota ``ident_cely_old`` pro danou operaci.

   .. py:method:: migrate_binary_file()

      Provádí operaci migrate binary file.

      :param soubor: Vstupní hodnota ``soubor`` pro danou operaci.
      :param include_content: Vstupní hodnota ``include_content`` pro danou operaci.
      :param check_if_exists: Vstupní hodnota ``check_if_exists`` pro danou operaci.
      :param ident_cely_old: Vstupní hodnota ``ident_cely_old`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_binary_file()

      Vrací binary file.

      :param uuid: Vstupní hodnota ``uuid`` pro danou operaci.
      :param ident_cely_old: Vstupní hodnota ``ident_cely_old`` pro danou operaci.
      :param thumb_small: Vstupní hodnota ``thumb_small`` pro danou operaci.
      :param thumb_large: Vstupní hodnota ``thumb_large`` pro danou operaci.
      :param timestamp: Vstupní hodnota ``timestamp`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: update_binary_file()

      Aktualizuje binary file.

      :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.
      :param content_type: Vstupní hodnota ``content_type`` pro danou operaci.
      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :param uuid: Vstupní hodnota ``uuid`` pro danou operaci.
      :param save_thumbs: Vstupní hodnota ``save_thumbs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: delete_binary_file()

      Odstraní binary file.

      :param soubor: Vstupní hodnota ``soubor`` pro danou operaci.

   .. py:method:: delete_binary_file_completely()

      Odstraní binary file completely.

      :param soubor: Vstupní hodnota ``soubor`` pro danou operaci.

   .. py:method:: delete_container()

      Odstraní container. v aplikaci.

      :param delete_tombstone: Vstupní hodnota ``delete_tombstone`` pro danou operaci.

   .. py:method:: _delete_link()

      Odstraní link.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param ident_cely_old: Vstupní hodnota ``ident_cely_old`` pro danou operaci.
      :param delete_container: Vstupní hodnota ``delete_container`` pro danou operaci.

   .. py:method:: generate_thumb_for_single_file()

      Vygeneruje thumb for single file.

      :param record: Vstupní hodnota ``record`` pro danou operaci.


.. py:class:: FedoraTransactionQueueClosedError

   Implementuje komponentu ``FedoraTransactionQueueClosedError`` v rámci aplikace.


.. py:class:: FedoraTransactionNoIDError

   Implementuje komponentu ``FedoraTransactionNoIDError`` v rámci aplikace.


.. py:class:: FedoraTransactionCommitFailedError

   Implementuje komponentu ``FedoraTransactionCommitFailedError`` v rámci aplikace.


.. py:class:: FedoraTransactionUnsupportedOperationError

   Implementuje komponentu ``FedoraTransactionUnsupportedOperationError`` v rámci aplikace.


.. py:class:: FedoraTransactionOperation

   Implementuje komponentu ``FedoraTransactionOperation`` v rámci aplikace.


.. py:class:: FedoraTransactionPostCommitTasks

   Implementuje komponentu ``FedoraTransactionPostCommitTasks`` v rámci aplikace.


.. py:class:: FedoraTransactionResult

   Implementuje komponentu ``FedoraTransactionResult`` v rámci aplikace.


.. py:class:: FedoraTransactionStatus

   Implementuje komponentu ``FedoraTransactionStatus`` v rámci aplikace.


.. py:class:: BaseFedoraTransaction

   Abstraktní základní třída pro Fedora transakce.

   Definuje společné rozhraní pro všechny typy Fedora transakcí.
   Podtřídy implementují konkrétní chování pro skutečné, testovací (dry-run)
   a mazací transakce.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: mark_transaction_as_closed()

      Označí transakci jako uzavřenou. Výchozí implementace neprovádí žádnou akci.

   .. py:method:: rollback_transaction()

      Provede rollback transakce. Výchozí implementace neprovádí žádnou akci.


.. py:class:: DryRunFedoraTransaction

   Testovací (dry-run) Fedora transakce, která nevytváří skutečnou transakci v repozitáři.

   Používá se při importu dat, kdy se zápisy do Fedory provádí až samostatném kroku,
   aby nedocházelo k duplicitním úpravám jednotlivých kontejnerů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: add_updated_ident_cely()

      Přidá identifikátor záznamu do množiny dotčených záznamů.


      **Argumenty:**

      - ``ident_cely``: identifikátor záznamu (ident_cely)


.. py:class:: FedoraTransaction

   Třída pro správu transakcí ve Fedora repozitáři.

   Zapouzdřuje vytvoření, commit a rollback transakce v Fedora repozitáři.
   Při inicializaci vytváří novou transakci ve Fedoře (pokud není předáno
   existující uid). Výsledek transakce se ukládá do Redis pro zobrazení uživateli.


   **Argumenty:**

   - ``main_record``: hlavní záznam (ModelWithMetadata), ke kterému se transakce váže
   - ``transaction_user``: uživatel provádějící transakci
   - ``success_message``: zpráva zobrazená při úspěšném dokončení
   - ``error_message``: zpráva zobrazená při chybě
   - ``uid``: existující UID transakce; pokud není zadáno, vytvoří se nová transakce
   - ``request``: HTTP request pro předání kontextu
   - ``suppress_message``: pokud True, neukládá výsledek transakce do Redis
   - ``redirect_on_error``: pokud True, při chybě provede přesměrování
   - ``redirect_url``: URL pro přesměrování při chybě

   **Výjimky:**

   *FedoraTransactionNoIDError*: pokud se nepodaří vytvořit transakci nebo získat její UID

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param main_record: Vstupní hodnota ``main_record`` pro danou operaci.
      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
      :param uid: Vstupní hodnota ``uid`` pro danou operaci.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param suppress_message: Vstupní hodnota ``suppress_message`` pro danou operaci.
      :param redirect_on_error: Vstupní hodnota ``redirect_on_error`` pro danou operaci.
      :param redirect_url: Vstupní hodnota ``redirect_url`` pro danou operaci.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_transaction_redis_key()

      Vrací transaction redis key.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :param transaction_user_id: Identifikátor objektu ``transaction_user``.

   .. py:method:: _transaction_redis_key()

      Provádí operaci transaction redis key.

      :return: Vrací výsledek provedené operace.

   .. py:method:: status()

      Provádí operaci status.

   .. py:method:: _save_transaction_result_to_redis()

      Uloží transaction result to redis.

      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _send_transaction_request()

      Odešle transaction request.

      :param operation: Vstupní hodnota ``operation`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: rollback_transaction()

      Provede rollback transakce ve Fedora repozitáři, pokud transakce ještě nebyla zrušena.

   .. py:method:: mark_transaction_as_closed()

      Uzavře transakci: provede commit, spustí post-commit úlohy a případně aktualizaci digiarchívu.

   .. py:method:: _perform_post_commit_tasks()

      Provede úlohy naplánované po commitu transakce (např. vytvoření linků) v nové transakci.

   .. py:method:: __create_transaction()

      Vytvoří transaction. v aplikaci.

   .. py:method:: call_digiarchiv_update()

      Provádí operaci call digiarchiv update.


.. py:class:: FedoraDeletionOnlyTransaction

   Fedora transakce určená pouze pro mazání záznamů při importu dat.

   Na rozdíl od běžné FedoraTransaction sbírá identifikátory dotčených záznamů, které jsou navázané
   na mazaný záznam a musejí být aktualizovány v následujícím kroku,
   podobně jako DryRunFedoraTransaction.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: add_updated_ident_cely()

      Přidá identifikátor záznamu do množiny dotčených záznamů.


      **Argumenty:**

      - ``ident_cely``: identifikátor záznamu (ident_cely)

