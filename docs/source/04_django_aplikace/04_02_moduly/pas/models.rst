PAS modely
==========

Definice modelů.

Třídy
------

.. py:class:: SamostatnyNalez

   Databázový model samostatného nálezu.

   **Metody:**

   .. py:method:: initial_pristupnost()

      Vrací výchozí hodnotu dostupnosti.

      :return: Vrací atribut objektu.

   .. py:method:: initial_pristupnost()

      Provádí operaci initial pristupnost.

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``initial_pristupnost``.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro samostatný nález.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_vracen()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro samostatný nález.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro samostatný nález.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený a uložení změny do historie pro samostatný nález.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie pro samostatný nález.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

      :return: Vrací výsledek volání ``reverse()``.

   .. py:method:: check_pred_archivaci()

      Ověří pred archivaci.

      :return: Vrací proměnná ``resp``.

   .. py:method:: check_pred_potvrzenim()

      Ověří pred potvrzenim.

      :param skip_soubory_check: Pokud ``True``, kontrola přítomnosti souborů se přeskočí,
          což prakticky způsobí, že metoda neprovede žádnou kontrolu. Parametr je přidán
          pro zachování konzistence s :meth:`check_pred_odeslanim` a může být užitečný
          v budoucnu.
      :return: Vrací proměnná ``resp``.

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: obdobi, datum_nalezu, lokalizace, okolnosti, specifikace, druh_nalezu, nalezce, geom, hloubka, katastr jsou vyplněna.

      Samostaný nález má připojený alespoň jeden soubor (pokud ``skip_soubory_check`` není ``True``).

      :param skip_soubory_check: Pokud ``True``, kontrola přítomnosti souborů se přeskočí.

      :return: Vrací proměnná ``resp``.

   .. py:method:: nahled_soubor()

      Vrací cestu k miniaturnímu náhledu souboru.

      :return: První soubor nebo None, pokud žádný neexistuje.

   .. py:method:: large_thumbnail()

      Vrací cestu k velké miniaturě obrázku.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.

   .. py:method:: small_thumbnail()

      Vrací cestu k malé miniaturě obrázku.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.

   .. py:method:: generate_coord_forms_initial()

      Vygeneruje coord forms initial.

      :return: Vrací slovník.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací proměnná ``self``.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      Zahrnuje organizaci projektu i cílovou organizaci nálezu (``predano_organizace``), pokud je nastavena.

      :return: Vrací n-tici.

   .. py:method:: redis_snapshot_id()

      Vrací identifikátor snímku v Redisu.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

   .. py:method:: set_igsn()

      Nastaví igsn. v aplikaci.

   .. py:method:: _get_igsn_client()

      Vrací igsn client.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: igsn_exists()

      Určuje, zda existuje IGSN identifikátor.

   .. py:method:: igsn_delete()

      Provádí operaci igsn delete.

      :param check_status: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``delete_record()``.

   .. py:method:: igsn_hide()

      Provádí operaci igsn hide.

      :param check_status: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``hide_record()``.

   .. py:method:: igsn_publish()

      Provádí operaci igsn publish.

      :param check_status: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``publish_record()``.

   .. py:method:: igsn_update()

      Provádí operaci igsn update.

      :param check_status: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
      :param reload_record: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``update_record()``.

   .. py:method:: igsn_url()

      Vrací URL odkaz na nález v IGSN databázi.


.. py:class:: UzivatelSpoluprace

   Databázový model spolupráce.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: aktivni()

      Vrací hodnotu určující, zda je spolupráce aktivní.

   .. py:method:: set_aktivni()

      Metoda pro nastavení stavu aktivní a uložení změny do historie pro spolupráci.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_neaktivni()

      Metoda pro nastavení stavu neaktivní a uložení změny do historie pro spolupráci.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param duvod: Textový důvod prováděné operace.

   .. py:method:: check_pred_aktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu aktivní.

      Kontrola že stav není aktivný.

      :return: Vrací proměnná ``result``.

   .. py:method:: check_pred_deaktivaci()

      Metoda na kontrolu prerekvizit pred posunem do stavu neaktivní.

      Kontrola že stav není neaktivný.

      :return: Vrací proměnná ``result``.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací n-tici.

   .. py:method:: redis_snapshot_id()

      Vrací identifikátor snímku v Redisu.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param pk: Primární klíč zpracovávaného záznamu.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.

