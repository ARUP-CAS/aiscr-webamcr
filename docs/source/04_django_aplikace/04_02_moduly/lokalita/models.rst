LOKALITA modely
===============

Definice modelů.

Třídy
------

.. py:class:: Lokalita

   Databázový model lokality.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

   .. py:method:: set_igsn()

      Nastaví igsn. v aplikaci.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: _get_igsn_client()

      Vrací igsn client.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: igsn_exists()

      Provádí operaci igsn exists.

   .. py:method:: igsn_delete()

      Provádí operaci igsn delete.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.

   .. py:method:: igsn_hide()

      Provádí operaci igsn hide.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.

   .. py:method:: igsn_publish()

      Provádí operaci igsn publish.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.

   .. py:method:: igsn_update()

      Provádí operaci igsn update.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :param reload_record: Vstupní hodnota ``reload_record`` pro danou operaci.

   .. py:method:: igsn_url()

      Provádí operaci igsn url.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.

