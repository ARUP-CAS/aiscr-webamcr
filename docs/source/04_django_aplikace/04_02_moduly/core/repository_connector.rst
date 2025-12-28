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

   .. py:method:: size_mb()

   .. py:method:: mime_type()

   .. py:method:: __init__()


.. py:class:: FedoraRequestType

   Popis není k dispozici.


.. py:class:: FedoraRepositoryConnector

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_base_url()

   .. py:method:: check_container_deleted()

   .. py:method:: check_container_deleted_or_not_exists()

   .. py:method:: create_link()

   .. py:method:: container_exists()

   .. py:method:: link_exists()

   .. py:method:: get_metadata()

   .. py:method:: save_metadata()

   .. py:method:: save_binary_file()

   .. py:method:: save_thumbs()

   .. py:method:: migrate_binary_file()

   .. py:method:: get_binary_file()

   .. py:method:: update_binary_file()

   .. py:method:: delete_binary_file()

   .. py:method:: delete_binary_file_completely()

   .. py:method:: delete_container()

   .. py:method:: record_deletion()

   .. py:method:: record_ident_change()

   .. py:method:: generate_thumb_for_single_file()

   .. py:method:: generate_thumbs()

   .. py:method:: save_single_file_from_storage()

   .. py:method:: save_files_from_storage()

   .. py:method:: create_missing_thumbnail()

   .. py:method:: remove_GPS_data_from_existing_files()


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

   .. py:method:: get_transaction_redis_key()

   .. py:method:: status()

   .. py:method:: rollback_transaction()

   .. py:method:: mark_transaction_as_closed()

   .. py:method:: call_digiarchiv_update()

