PAS modely
==========

Definice modelů.

Třídy
------

.. py:class:: SamostatnyNalez

   Databázový model samostatného nálezu.

   **Metody:**

   .. py:method:: initial_pristupnost()

      Provádí operaci initial pristupnost.

   .. py:method:: initial_pristupnost()

      Provádí operaci initial pristupnost.

      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro samostatný nález.

      :param user: Popis parametru ``user``.

   .. py:method:: set_vracen()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro samostatný nález.

      :param user: Popis parametru ``user``.
      :param new_state: Popis parametru ``new_state``.
      :param poznamka: Popis parametru ``poznamka``.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro samostatný nález.

      :param user: Popis parametru ``user``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený a uložení změny do historie pro samostatný nález.

      :param user: Popis parametru ``user``.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie pro samostatný nález.

      :param user: Popis parametru ``user``.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

   .. py:method:: check_pred_archivaci()

      Ověří pred archivaci.

   .. py:method:: check_pred_potvrzenim()

      Ověří pred potvrzenim.

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: obdobi, datum_nalezu, lokalizace, okolnosti, specifikace, druh_nalezu, nalezce, geom, hloubka, katastr jsou vyplněna.

      Samostaný nález má připojený alespoň jeden soubor.

   .. py:method:: nahled_soubor()

      Provádí operaci nahled soubor.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

   .. py:method:: generate_coord_forms_initial()

      Vygeneruje coord forms initial.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: set_igsn()

      Nastaví igsn. v aplikaci.

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


.. py:class:: UzivatelSpoluprace

   Databázový model spolupráce.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: aktivni()

      Provádí operaci aktivni.

   .. py:method:: set_aktivni()

      Metoda pro nastavení stavu aktivní a uložení změny do historie pro spolupráci.

      :param user: Popis parametru ``user``.

   .. py:method:: set_neaktivni()

      Metoda pro nastavení stavu neaktivní a uložení změny do historie pro spolupráci.

      :param user: Popis parametru ``user``.
      :param duvod: Popis parametru ``duvod``.

   .. py:method:: check_pred_aktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu aktivní.

      Kontrola že stav není aktivný.

   .. py:method:: check_pred_deaktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu neaktivní.

      Kontrola že stav není neaktivný.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param pk: Primární klíč zpracovávaného záznamu.

