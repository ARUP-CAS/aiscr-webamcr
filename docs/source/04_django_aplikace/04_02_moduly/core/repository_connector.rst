CORE repository_connector
=========================

Modul repository_connector.

Třídy
------

.. py:class:: FedoraValidationError

   Popis není k dispozici.


.. py:class:: FedoraError

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: FedoraUpdatedByAnotherTransactionError

   Popis není k dispozici.


.. py:class:: IdentChangeFedoraError

   Popis není k dispozici.


.. py:class:: FedoraNoResponseError

   Popis není k dispozici.


.. py:class:: RepositoryBinaryFile

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_url_without_domain()

   .. py:method:: url_without_domain()

   .. py:method:: uuid()

   .. py:method:: _calculate_sha_512()

   .. py:method:: size_mb()

   .. py:method:: mime_type()

   .. py:method:: __init__()


.. py:class:: FedoraRequestType

   Popis není k dispozici.


.. py:class:: FedoraRepositoryConnector

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _get_model_name()

   .. py:method:: _get_rdf_inset_data()

   .. py:method:: _get_creator()

   .. py:method:: _update_creator()

   .. py:method:: get_base_url()

   .. py:method:: _get_request_url()

   .. py:method:: check_container_deleted()

   .. py:method:: check_container_deleted_or_not_exists()

   .. py:method:: _get_auth()

   .. py:method:: _send_request()

   .. py:method:: _create_container()

   .. py:method:: create_link()

   .. py:method:: container_exists()

   .. py:method:: _connect_deleted_container()

   .. py:method:: link_exists()

   .. py:method:: _check_container()

   .. py:method:: _create_binary_file_container()

   .. py:method:: _check_binary_file_container()

   .. py:method:: _generate_metadata()

   .. py:method:: get_metadata()

   .. py:method:: get_metadata_historicka()

      Metoda varacející konkrétní verzi metadat

   .. py:method:: parse_historie()

      Metoda k parsování odpovědi s verzemi
      Vrací list dictů: {"datetime": datetime, "timestamp": str}

   .. py:method:: get_historie_metadat()

      Metoda k získání info o verzích metadat

   .. py:method:: get_historie_file()

      Metoda k získání info o verzích souborů

   .. py:method:: save_metadata()

   .. py:method:: save_binary_file()

   .. py:method:: __generate_thumb()

   .. py:method:: save_thumbs()

   .. py:method:: migrate_binary_file()

   .. py:method:: get_binary_file()

   .. py:method:: update_binary_file()

   .. py:method:: delete_binary_file()

   .. py:method:: delete_binary_file_completely()

   .. py:method:: delete_container()

   .. py:method:: _delete_link()

   .. py:method:: record_deletion()

   .. py:method:: record_ident_change()

   .. py:method:: generate_thumb_for_single_file()


.. py:class:: FedoraTransactionQueueClosedError

   Popis není k dispozici.


.. py:class:: FedoraTransactionNoIDError

   Popis není k dispozici.


.. py:class:: FedoraTransactionCommitFailedError

   Popis není k dispozici.


.. py:class:: FedoraTransactionUnsupportedOperationError

   Popis není k dispozici.


.. py:class:: FedoraTransactionOperation

   Popis není k dispozici.


.. py:class:: FedoraTransactionPostCommitTasks

   Popis není k dispozici.


.. py:class:: FedoraTransactionResult

   Popis není k dispozici.


.. py:class:: FedoraTransactionStatus

   Popis není k dispozici.


.. py:class:: BaseFedoraTransaction

   Abstraktní základní třída pro Fedora transakce.

   Definuje společné rozhraní pro všechny typy Fedora transakcí.
   Podtřídy implementují konkrétní chování pro skutečné, testovací (dry-run)
   a mazací transakce.

   **Metody:**

   .. py:method:: __init__()

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

   .. py:method:: __str__()

   .. py:method:: get_transaction_redis_key()

      Vytvoří klíč pro uložení výsledku transakce do Redis.


      **Argumenty:**

      - ``ident_cely``: identifikátor záznamu
      - ``transaction_user_id``: ID uživatele provádějícího transakci

   .. py:method:: _transaction_redis_key()

   .. py:method:: status()

   .. py:method:: _save_transaction_result_to_redis()

      Uloží výsledek transakce (COMMITED/ABORTED) do Redis.


      **Argumenty:**

      - ``result``: výsledek transakce (FedoraTransactionResult)

   .. py:method:: _send_transaction_request()

      Odešle požadavek na commit nebo rollback transakce do Fedory.


      **Argumenty:**

      - ``operation``: typ operace (COMMIT nebo ROLLBACK)

      **Výjimky:**

      *FedoraTransactionUnsupportedOperationError*: pokud je zadána neplatná operace
      *FedoraTransactionCommitFailedError*: pokud Fedora vrátí chybový status

   .. py:method:: rollback_transaction()

      Provede rollback transakce ve Fedora repozitáři, pokud transakce ještě nebyla zrušena.

   .. py:method:: mark_transaction_as_closed()

      Uzavře transakci: provede commit, spustí post-commit úlohy a případně aktualizaci digiarchívu.

   .. py:method:: _perform_post_commit_tasks()

      Provede úlohy naplánované po commitu transakce (např. vytvoření linků) v nové transakci.

   .. py:method:: __create_transaction()

      Vytvoří novou transakci ve Fedoře.


      **Výjimky:**

      *FedoraTransactionNoIDError*: pokud se nepodaří vytvořit transakci nebo získat její UID

   .. py:method:: call_digiarchiv_update()

      Spustí asynchronní aktualizaci digiarchívu přes Celery.

      Kontroluje, zda úloha již není naplánovaná nebo běží, aby nedocházelo k duplicitnímu spuštění.


.. py:class:: FedoraDeletionOnlyTransaction

   Fedora transakce určená pouze pro mazání záznamů při importu dat.

   Na rozdíl od běžné FedoraTransaction sbírá identifikátory dotčených záznamů, které jsou navázané
   na mazaný záznam a musejí být aktualizovány v následujícím kroku,
   podobně jako DryRunFedoraTransaction.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: add_updated_ident_cely()

      Přidá identifikátor záznamu do množiny dotčených záznamů.


      **Argumenty:**

      - ``ident_cely``: identifikátor záznamu (ident_cely)

