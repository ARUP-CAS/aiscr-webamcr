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


.. py:class:: FedoraTransaction

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: __str__()

   .. py:method:: get_transaction_redis_key()

   .. py:method:: _transaction_redis_key()

   .. py:method:: status()

   .. py:method:: _save_transaction_result_to_redis()

   .. py:method:: _send_transaction_request()

   .. py:method:: rollback_transaction()

   .. py:method:: mark_transaction_as_closed()

   .. py:method:: _perform_post_commit_tasks()

   .. py:method:: __create_transaction()

   .. py:method:: call_digiarchiv_update()

