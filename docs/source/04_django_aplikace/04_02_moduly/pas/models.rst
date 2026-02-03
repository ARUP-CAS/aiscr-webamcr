PAS modely
==========

Definice modelů.

Třídy
------

.. py:class:: SamostatnyNalez

   Class pro db model samostantý nález.

   **Metody:**

   .. py:method:: initial_pristupnost()

   .. py:method:: initial_pristupnost()

   .. py:method:: save()

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro samostatný nález.

   .. py:method:: set_vracen()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro samostatný nález.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro samostatný nález.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený a uložení změny do historie pro samostatný nález.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie pro samostatný nález.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

   .. py:method:: check_pred_archivaci()

   .. py:method:: check_pred_potvrzenim()

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: obdobi, datum_nalezu, lokalizace, okolnosti, specifikace, druh_nalezu, nalezce, geom, hloubka, katastr jsou vyplněna.

      Samostaný nález má připojený alespoň jeden soubor.

   .. py:method:: nahled_soubor()

   .. py:method:: large_thumbnail()

   .. py:method:: small_thumbnail()

   .. py:method:: generate_coord_forms_initial()

   .. py:method:: __str__()

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: set_igsn()

   .. py:method:: _get_igsn_client()

   .. py:method:: igsn_exists()

   .. py:method:: igsn_delete()

   .. py:method:: igsn_hide()

   .. py:method:: igsn_publish()

   .. py:method:: igsn_update()

   .. py:method:: igsn_url()


.. py:class:: UzivatelSpoluprace

   Class pro db model spolupráce.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: aktivni()

   .. py:method:: set_aktivni()

      Metoda pro nastavení stavu aktivní a uložení změny do historie pro spolupráci.

   .. py:method:: set_neaktivni()

      Metoda pro nastavení stavu neaktivní a uložení změny do historie pro spolupráci.

   .. py:method:: check_pred_aktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu aktivní.
      Kontrola že stav není aktivný.

   .. py:method:: check_pred_deaktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu neaktivní.
      Kontrola že stav není neaktivný.

   .. py:method:: __str__()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: get_by_ident_cely()

