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

      :param url: Parametr ``url`` slouží jako vstup pro logiku funkce ``__init__``.
      :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
      :param code: Aplikační nebo HTTP kód, který funkce převádí na odpověď.
      :param headers: Textový nebo strukturální vstup `headers` používaný při sestavení nebo zpracování obsahu.
      :param fedora_transaction: Parametr ``fedora_transaction`` pracuje se s atributy ``main_record``, ``redirect_on_error``.


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

      :param url: Parametr ``url`` se předává do volání ``join()``, pracuje se s atributy ``split``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``join()``.

   .. py:method:: url_without_domain()

      Provádí operaci url without domain.

      :return: Vrací výsledek volání ``get_url_without_domain()``.

   .. py:method:: uuid()

      Provádí operaci uuid.

      :return: Vrací vybranou hodnotu z kolekce.

   .. py:method:: _calculate_sha_512()

      Provádí operaci calculate sha 512.

      :return: Textová reprezentace UID transakce.

   .. py:method:: size_mb()

      Provádí operaci size mb.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: mime_type()

      Provádí operaci mime type.

      :return: Vrací výsledek volání ``get_mime_type()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param url: Parametr ``url`` slouží jako vstup pro logiku funkce ``__init__``.
      :param content: Textový nebo strukturální vstup `content` používaný při sestavení nebo zpracování obsahu.
      :param filename: Parametr ``filename`` slouží jako vstup pro logiku funkce ``__init__``.


.. py:class:: FedoraRequestType

   Implementuje komponentu ``FedoraRequestType`` v rámci aplikace.


.. py:class:: FedoraRepositoryConnector

   Implementuje komponentu ``FedoraRepositoryConnector`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Parametr ``record`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``.
      :param transaction: Parametr ``transaction`` se předává do volání ``isinstance()``, ``FedoraTransaction()``, pracuje se s atributy ``uid``, ``main_record``, ovlivňuje větvení podmínek.
      :param skip_container_check: Parametr ``skip_container_check`` slouží jako vstup pro logiku funkce ``__init__``.

   .. py:method:: _get_model_name()

      Vrací model name.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_creator_rdf_data()

      Vrací rdf inset data.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_creator()

      Vrací creator.

      :param url: Parametr ``url`` se předává do volání ``_send_request()``.
      :return: Načtená data odpovídající zadaným vstupům.

      :param only_uri: Parametr ``only_uri`` ovlivňuje větvení podmínek.

   .. py:method:: _update_creator()

      Aktualizuje creator.

      :param request_type: Parametr ``request_type`` předává se do volání ``_get_request_url()``, ``_send_request()``.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``_get_request_url()``.
      :return: Textová reprezentace UID transakce.

   .. py:method:: get_base_url()

      Vrací base url.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: _get_request_url()

      Vrací request url.

      :param request_type: Parametr ``request_type`` předává se do volání ``error()``, ovlivňuje větvení podmínek.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely: Parametr ``ident_cely`` ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: check_container_deleted()

      Ověří container deleted.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``_send_request()``.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: check_container_deleted_or_not_exists()

      Ověří container deleted or not exists.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``send_request()``.
      :param model_name: Název modelu používaný pro cílení operace.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: _get_auth()

      Vrací auth.

      :param request_type: Parametr ``request_type`` ovlivňuje větvení podmínek.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _send_request()

      Odešle request.

      :param url: Parametr ``url`` se předává do volání ``post()``, ``get()``.
      :param request_type: Parametr ``request_type`` předává se do volání ``_get_auth()``, pracuje se s atributy ``value``, ovlivňuje větvení podmínek.
      :param headers: Textový nebo strukturální vstup `headers` používaný při sestavení nebo zpracování obsahu.
      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :return: Textová reprezentace UID transakce.

      :raises FedoraUpdatedByAnotherTransactionError: Vyvolá se při splnění podmínky ``response.status_code == 409``.
      :raises FedoraError: Vyvolá se při splnění podmínky ``response.status_code == 409``.

   .. py:method:: _create_container()

      Vytvoří container.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: create_link()

      Vytvoří link. v aplikaci.

      :param ident_cely_proxy: Identifikátor ``ident_cely_proxy`` používaný pro dohledání cílového záznamu.

   .. py:method:: container_exists()

      Provádí operaci container exists.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: _connect_deleted_container()

      Provádí operaci connect deleted container.

      :return: Textová reprezentace UID transakce.

   .. py:method:: link_exists()

      Provádí operaci link exists.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

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

      :return: Vrací atribut objektu.

   .. py:method:: parse_historie()

      Zpracuje historie. v aplikaci.

      :param response_text: Číselná hodnota ``response_text`` použitá při výpočtu nebo transformaci.

      :return: Vrací proměnná ``result``.

   .. py:method:: get_historie_metadat()

      Metoda k získání info o verzích metadat

      :return: Vrací proměnná ``result``.

   .. py:method:: get_historie_file()

      Metoda k získání info o verzích souborů

      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.

      :return: Vrací proměnná ``result``.

   .. py:method:: save_metadata()

      Uloží metadata. v aplikaci.

      :param update: Časový údaj ``update`` použitý při filtrování nebo výpočtu.

      :raises FedoraNoResponseError: Vyvolá se při splnění podmínky ``result is None``.

   .. py:method:: save_binary_file()

      Uloží binary file.

      :param file_name: Parametr ``file_name`` se předává do volání ``debug()``, ``RepositoryBinaryFile()``.
      :param content_type: Parametr ``content_type`` slouží jako vstup pro logiku funkce ``save_binary_file``.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param save_thumbs: Parametr ``save_thumbs`` ovlivňuje větvení podmínek.
      :return: Textová reprezentace UID transakce.

   .. py:method:: __generate_thumb()

      Vygeneruje thumb. v aplikaci.

      :param file_name: Parametr ``file_name`` se předává do volání ``debug()``, ``__generate_thumb_from_icon()``, pracuje se s atributy ``lower``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param file_content: Parametr ``file_content`` se předává do volání ``convert_from_bytes()``, ``__generate_thumb_from_icon()``, pracuje se s atributy ``getvalue``, vstupuje do návratové hodnoty.
      :param large: Parametr ``large`` se předává do volání ``debug()``, ``resize_image()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``thumbnail``, výsledek volání ``__generate_thumb_from_icon()``.

   .. py:method:: save_thumbs()

      Uloží thumbs. v aplikaci.

      :param file_name: Parametr ``file_name`` se předává do volání ``debug()``, ``__generate_thumb()``, pracuje se s atributy ``rfind``.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param update: Časový údaj ``update`` použitý při filtrování nebo výpočtu.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.

   .. py:method:: migrate_binary_file()

      Provádí operaci migrate binary file.

      :param soubor: Parametr ``soubor`` se předává do volání ``debug()``, ``open()``, pracuje se s atributy ``pk``, ``repository_uuid``, ovlivňuje větvení podmínek.
      :param include_content: Parametr ``include_content`` ovlivňuje větvení podmínek.
      :param check_if_exists: Parametr ``check_if_exists`` ovlivňuje větvení podmínek.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :return: Textová reprezentace UID transakce.

   .. py:method:: get_binary_file()

      Vrací binary file.

      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param thumb_small: Parametr ``thumb_small`` se předává do volání ``debug()``, ovlivňuje větvení podmínek.
      :param thumb_large: Parametr ``thumb_large`` se předává do volání ``debug()``, ovlivňuje větvení podmínek.
      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: update_binary_file()

      Aktualizuje binary file.

      :param file_name: Parametr ``file_name`` se předává do volání ``debug()``, ``RepositoryBinaryFile()``.
      :param content_type: Parametr ``content_type`` slouží jako vstup pro logiku funkce ``update_binary_file``.
      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param uuid: Identifikátor ``uuid`` používaný pro dohledání cílového záznamu.
      :param save_thumbs: Parametr ``save_thumbs`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
      :return: Textová reprezentace UID transakce.

   .. py:method:: delete_binary_file()

      Odstraní binary file.

      :param soubor: Parametr ``soubor`` se předává do volání ``debug()``, ``_get_request_url()``, pracuje se s atributy ``repository_uuid``, ``pk``, ovlivňuje větvení podmínek.

   .. py:method:: delete_binary_file_completely()

      Odstraní binary file completely.

      :param soubor: Parametr ``soubor`` se předává do volání ``debug()``, ``_get_request_url()``, pracuje se s atributy ``repository_uuid``.

   .. py:method:: delete_container()

      Odstraní container. v aplikaci.

      :param delete_tombstone: Parametr ``delete_tombstone`` ovlivňuje větvení podmínek.

   .. py:method:: _delete_link()

      Odstraní link.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``_get_request_url()``.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: record_deletion()

      Provádí operaci record deletion.

   .. py:method:: record_ident_change()

      Provádí operaci record ident change.

      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param delete_container: Parametr ``delete_container`` ovlivňuje větvení podmínek.

      :raises IdentChangeFedoraError: Vyvolá se při splnění podmínky ``ident_cely_old is None or self.record.ident_cely == ident_cely_old``.

   .. py:method:: generate_thumb_for_single_file()

      Vygeneruje thumb for single file.

      :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``get()``, pracuje se s atributy ``vazba``, ``active_transaction``, ovlivňuje větvení podmínek.


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

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``add()``.


.. py:class:: FedoraTransaction

   Třída pro správu transakcí ve Fedora repozitáři.

   Zapouzdřuje vytvoření, commit a rollback transakce v Fedora repozitáři.
   Při inicializaci vytváří novou transakci ve Fedoře (pokud není předáno
   existující uid). Výsledek transakce se ukládá do Redis pro zobrazení uživateli.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param main_record: Parametr ``main_record`` slouží jako vstup pro logiku funkce ``__init__``.
      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Parametr ``success_message`` slouží jako vstup pro logiku funkce ``__init__``.
      :param error_message: Parametr ``error_message`` slouží jako vstup pro logiku funkce ``__init__``.
      :param uid: Identifikátor `uid` používaný pro dohledání cílového záznamu.
      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``__init__``.
      :param suppress_message: Pokud ``True``, výsledek transakce se neukládá do Redis.
      :param redirect_on_error: Pokud ``True``, při chybě se použije přesměrování.
      :param redirect_url: URL pro přesměrování při chybě transakce.
      :raises FedoraTransactionNoIDError: Pokud se nepodaří vytvořit transakci nebo získat její UID.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Textová reprezentace UID transakce.

   .. py:method:: get_transaction_redis_key()

      Vrací transaction redis key.

      :param ident_cely: Parametr ``ident_cely`` vstupuje do návratové hodnoty.
      :param transaction_user_id: Identifikátor objektu ``transaction_user``.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: _transaction_redis_key()

      Provádí operaci transaction redis key.

      :return: Textová reprezentace UID transakce.

   .. py:method:: status()

      Provádí operaci status.

      :return: Vrací atribut objektu.

   .. py:method:: _save_transaction_result_to_redis()

      Uloží transaction result to redis.

      :param result: Výsledek transakce určený k uložení do Redis.
      :return: Textová reprezentace UID transakce.

   .. py:method:: _send_transaction_request()

      Odešle transaction request.

      :param operation: Parametr ``operation`` se předává do volání ``FedoraTransactionUnsupportedOperationError()``, ovlivňuje větvení podmínek.
      :return: Textová reprezentace UID transakce.

      :raises FedoraTransactionUnsupportedOperationError: Vyvolá se při splnění podmínky ``operation == FedoraTransactionOperation.ROLLBACK``.
      :raises FedoraTransactionCommitFailedError: Vyvolá se při splnění podmínky ``not str(response.status_code).startswith('2')``.

   .. py:method:: rollback_transaction()

      Provede rollback transakce ve Fedora repozitáři, pokud transakce ještě nebyla zrušena.

   .. py:method:: mark_transaction_as_closed()

      Uzavře transakci: provede commit, spustí post-commit úlohy a případně aktualizaci digiarchívu.

   .. py:method:: _perform_post_commit_tasks()

      Provede úlohy naplánované po commitu transakce (např. vytvoření linků) v nové transakci.

   .. py:method:: __create_transaction()

      Vytvoří transaction. v aplikaci.

      :raises FedoraTransactionNoIDError: Vyvolá se při splnění podmínky ``not str(response.status_code).startswith('2')``; nebo při splnění podmínky ``match``.

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

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``add()``.

