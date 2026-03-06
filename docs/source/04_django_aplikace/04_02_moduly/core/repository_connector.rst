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

      :param url: Cesta, URL nebo název zdroje ``url``, ze kterého funkce čte nebo kam zapisuje.
      :param message: Textová zpráva ``message`` používaná pro hlášení stavu nebo chyby.
      :param code: Aplikační nebo HTTP kód, který funkce převádí na odpověď.
      :param headers: Textový nebo strukturální vstup `headers` používaný při sestavení nebo zpracování obsahu.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.


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

      :param url: Cesta, URL nebo název zdroje ``url``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: url_without_domain()

      Provádí operaci url without domain.

   .. py:method:: uuid()

      Provádí operaci uuid.

   .. py:method:: _calculate_sha_512()

      Provádí operaci calculate sha 512.

      :return: Textová reprezentace UID transakce.

   .. py:method:: size_mb()

      Provádí operaci size mb.

   .. py:method:: mime_type()

      Provádí operaci mime type.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param url: Cesta, URL nebo název zdroje ``url``, ze kterého funkce čte nebo kam zapisuje.
      :param content: Textový nebo strukturální vstup `content` používaný při sestavení nebo zpracování obsahu.
      :param filename: Cesta, URL nebo název zdroje ``filename``, ze kterého funkce čte nebo kam zapisuje.


.. py:class:: FedoraRequestType

   Implementuje komponentu ``FedoraRequestType`` v rámci aplikace.


.. py:class:: FedoraRepositoryConnector

   Implementuje komponentu ``FedoraRepositoryConnector`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param transaction: Číselná nebo geometrická hodnota `transaction` použitá při výpočtu nebo transformaci.
      :param skip_container_check: Příznak ``skip_container_check`` určující průběh nebo rozsah zpracování.

   .. py:method:: _get_model_name()

      Vrací model name.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_creator_rdf_data()

      Vrací rdf inset data.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_creator()

      Vrací creator.

      :param url: Cesta, URL nebo název zdroje ``url``, ze kterého funkce čte nebo kam zapisuje.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _update_creator()

      Aktualizuje creator.

      :param request_type: Název nebo typ ``request_type`` používaný pro volbu cílové logiky.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :return: Textová reprezentace UID transakce.

   .. py:method:: get_base_url()

      Vrací base url.

   .. py:method:: _get_request_url()

      Vrací request url.

      :param request_type: Název nebo typ ``request_type`` používaný pro volbu cílové logiky.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: check_container_deleted()

      Ověří container deleted.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

   .. py:method:: check_container_deleted_or_not_exists()

      Ověří container deleted or not exists.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :param model_name: Název modelu používaný pro cílení operace.

   .. py:method:: _get_auth()

      Vrací auth.

      :param request_type: Název nebo typ ``request_type`` používaný pro volbu cílové logiky.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _send_request()

      Odešle request.

      :param url: Cesta, URL nebo název zdroje ``url``, ze kterého funkce čte nebo kam zapisuje.
      :param request_type: Název nebo typ ``request_type`` používaný pro volbu cílové logiky.
      :param headers: Textový nebo strukturální vstup `headers` používaný při sestavení nebo zpracování obsahu.
      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :return: Textová reprezentace UID transakce.

   .. py:method:: _create_container()

      Vytvoří container.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: create_link()

      Vytvoří link. v aplikaci.

      :param ident_cely_proxy: Identifikátor ``ident_cely_proxy`` používaný pro dohledání cílového záznamu.

   .. py:method:: container_exists()

      Provádí operaci container exists.

   .. py:method:: _connect_deleted_container()

      Provádí operaci connect deleted container.

      :return: Textová reprezentace UID transakce.

   .. py:method:: link_exists()

      Provádí operaci link exists.

   .. py:method:: _check_container()

      Ověří container.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _create_binary_file_container()

      Vytvoří binary file container.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _check_binary_file_container()

      Ověří binary file container.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _generate_metadata()

      Vygeneruje metadata.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: get_metadata()

      Vrací metadata. v aplikaci.

      :param update: Časový údaj ``update`` použitý při filtrování nebo výpočtu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_metadata_historicka()

      Metoda varacející konkrétní verzi metadat

      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.

   .. py:method:: parse_historie()

      Zpracuje historie. v aplikaci.

      :param response_text: Číselná hodnota ``response_text`` použitá při výpočtu nebo transformaci.

   .. py:method:: get_historie_metadat()

      Metoda k získání info o verzích metadat

   .. py:method:: get_historie_file()

      Metoda k získání info o verzích souborů

      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param update: Časový údaj ``update`` použitý při filtrování nebo výpočtu.

   .. py:method:: save_binary_file()

      Uloží binary file.

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.
      :param content_type: Název nebo typ ``content_type`` používaný pro volbu cílové logiky.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param save_thumbs: Příznak ``save_thumbs`` určující průběh nebo rozsah zpracování.
      :return: Textová reprezentace UID transakce.

   .. py:method:: __generate_thumb()

      Vygeneruje thumb. v aplikaci.

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.
      :param file_content: Cesta, URL nebo název zdroje ``file_content``, ze kterého funkce čte nebo kam zapisuje.
      :param large: Číselná nebo geometrická hodnota `large` použitá při výpočtu nebo transformaci.

   .. py:method:: save_thumbs()

      Uloží thumbs. v aplikaci.

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param update: Časový údaj ``update`` použitý při filtrování nebo výpočtu.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.

   .. py:method:: migrate_binary_file()

      Provádí operaci migrate binary file.

      :param soubor: Cesta, URL nebo název zdroje ``soubor``, ze kterého funkce čte nebo kam zapisuje.
      :param include_content: Příznak ``include_content`` určující průběh nebo rozsah zpracování.
      :param check_if_exists: Příznak ``check_if_exists`` určující průběh nebo rozsah zpracování.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :return: Textová reprezentace UID transakce.

   .. py:method:: get_binary_file()

      Vrací binary file.

      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param thumb_small: Číselná nebo geometrická hodnota `thumb_small` použitá při výpočtu nebo transformaci.
      :param thumb_large: Číselná nebo geometrická hodnota `thumb_large` použitá při výpočtu nebo transformaci.
      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: update_binary_file()

      Aktualizuje binary file.

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.
      :param content_type: Název nebo typ ``content_type`` používaný pro volbu cílové logiky.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param save_thumbs: Příznak ``save_thumbs`` určující průběh nebo rozsah zpracování.
      :return: Textová reprezentace UID transakce.

   .. py:method:: delete_binary_file()

      Odstraní binary file.

      :param soubor: Cesta, URL nebo název zdroje ``soubor``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: delete_binary_file_completely()

      Odstraní binary file completely.

      :param soubor: Cesta, URL nebo název zdroje ``soubor``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: delete_container()

      Odstraní container. v aplikaci.

      :param delete_tombstone: Příznak ``delete_tombstone`` určující průběh nebo rozsah zpracování.

   .. py:method:: _delete_link()

      Odstraní link.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param delete_container: Příznak ``delete_container`` určující průběh nebo rozsah zpracování.

   .. py:method:: generate_thumb_for_single_file()

      Vygeneruje thumb for single file.

      :param record: Záznam, který funkce čte nebo upravuje.


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

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.


.. py:class:: FedoraTransaction

   Třída pro správu transakcí ve Fedora repozitáři.

   Zapouzdřuje vytvoření, commit a rollback transakce v Fedora repozitáři.
   Při inicializaci vytváří novou transakci ve Fedoře (pokud není předáno
   existující uid). Výsledek transakce se ukládá do Redis pro zobrazení uživateli.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param main_record: Záznam/objekt ``main_record``, který funkce čte, validuje nebo upravuje.
      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
      :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.
      :param uid: Identifikátor `uid` používaný pro dohledání cílového záznamu.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param suppress_message: Pokud ``True``, výsledek transakce se neukládá do Redis.
      :param redirect_on_error: Pokud ``True``, při chybě se použije přesměrování.
      :param redirect_url: URL pro přesměrování při chybě transakce.
      :raises FedoraTransactionNoIDError: Pokud se nepodaří vytvořit transakci nebo získat její UID.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Textová reprezentace UID transakce.

   .. py:method:: get_transaction_redis_key()

      Vrací transaction redis key.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :param transaction_user_id: Identifikátor objektu ``transaction_user``.

   .. py:method:: _transaction_redis_key()

      Provádí operaci transaction redis key.

      :return: Textová reprezentace UID transakce.

   .. py:method:: status()

      Provádí operaci status.

   .. py:method:: _save_transaction_result_to_redis()

      Uloží transaction result to redis.

      :param result: Výsledek transakce určený k uložení do Redis.
      :return: Textová reprezentace UID transakce.

   .. py:method:: _send_transaction_request()

      Odešle transaction request.

      :param operation: Číselná nebo geometrická hodnota `operation` použitá při výpočtu nebo transformaci.
      :return: Textová reprezentace UID transakce.

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

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

