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

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: igsn_exists()

      Provádí operaci igsn exists.

   .. py:method:: igsn_delete()

      Provádí operaci igsn delete.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: igsn_hide()

      Provádí operaci igsn hide.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: igsn_publish()

      Provádí operaci igsn publish.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: igsn_update()

      Provádí operaci igsn update.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.
      :param reload_record: Záznam/objekt ``reload_record``, který funkce čte, validuje nebo upravuje.

   .. py:method:: igsn_url()

      Provádí operaci igsn url.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

