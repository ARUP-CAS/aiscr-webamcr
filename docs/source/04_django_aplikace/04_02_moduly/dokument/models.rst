DOKUMENT modely
===============

Definice modelů.

Třídy
------

.. py:class:: Dokument

   Databázový model dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu dokumentu.

      :return: Vrací výsledek volání ``reverse()``.

   .. py:method:: set_doi()

      Nastaví doi. v aplikaci.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_permanent_identificator()

      Nastaví permanent identificator.

      :param dokument: Parametr ``dokument`` předává se do volání ``get_dokument_rada()``, ``set_permanent_ident_cely()``, pracuje se s atributy ``ident_cely``, ``typ_dokumentu``.
      :param request: Parametr ``request`` předává se do volání ``add_message()``.
      :param messages: Parametr ``messages`` předává se do volání ``add_message()``, pracuje se s atributy ``add_message``, ``SUCCESS``.
      :param fedora_transaction: Parametr ``fedora_transaction`` pracuje se s atributy ``rollback_transaction``.
      Výsledek provedené změny nad cílovým objektem.

      :return: Vrací hodnotu typu ``Optional[JsonResponse]`` (výsledek volání ``JsonResponse()``).

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: format, popis, duveryhodnost, obdobi, areal jsou vyplněna pro model 3D.

      polia: pristupnost, popis, ulozeni_originalu jsou vyplněna pro model 3D.

      Dokument má aspoň jeden dokument.

      :return: Vrací proměnná ``result``.

   .. py:method:: check_pred_archivaci()

      Metoda na kontrolu prerekvizit pred archivací:

      kontrola jako před odesláním

      :return: Vrací proměnná ``result``.

   .. py:method:: has_extra_data()

      Metoda na zjištení že dokument má extra data.

      :return: Vrací proměnná ``has_extra_data``.

   .. py:method:: get_komponenta()

      Metoda na získaní všech komponent dokumentu.

      :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, None.
      :raises UnexpectedDataRelations: Vyvolá se s textem "Neleze ziskat komponentu modelu 3D.".

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro dokument.

      Metoda bere pořadoví číslo z db dokument sekvence.
      Metoda zmení i ident připojených souborů.

      :param region: Parametr ``region`` se předává do volání ``get()``, ``create()``.
      :param rada: Parametr ``rada`` se předává do volání ``get()``, ``create()``, pracuje se s atributy ``zkratka``.

      :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.

   .. py:method:: set_datum_zverejneni()

      metoda pro nastavení datumu zvěřejnení.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací proměnná ``self``.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací n-tici.

   .. py:method:: thumbnail_image()

      Provádí operaci thumbnail image.

      :return: Vrací atribut objektu.

   .. py:method:: thumbnail_image_file()

      Provádí operaci thumbnail image file.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

   .. py:method:: _get_doi_client()

      Vrací doi client.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: doi_exists()

      Provádí operaci doi exists.

      :return: Vrací výsledek volání ``check_record_exists()``.

   .. py:method:: doi_delete()

      Provádí operaci doi delete.

      :param check_status: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``delete_record()``.

   .. py:method:: doi_hide()

      Provádí operaci doi hide.

      :param check_status: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``hide_record()``.

   .. py:method:: doi_publish()

      Provádí operaci doi publish.

      :param check_status: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``publish_record()``.

   .. py:method:: doi_update()

      Provádí operaci doi update.

      :param check_status: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
      :param reload_record: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``update_record()``.

   .. py:method:: doi_url()

      Provádí operaci doi url.

      :return: Vrací výsledek volání ``get_record_url()``.


.. py:class:: DokumentCast

   Databázový model části dokumentu.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_absolute_url()``, výsledek volání ``reverse()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací výsledek volání ``get_permission_object()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: initial_archeologicky_zaznam()

      Vrátí objekt dokument na základě initial_archeologicky_zaznam_id (líné načtení).

      :return: Vrací výsledek operace.

   .. py:method:: initial_projekt()

      Provádí operaci initial projekt.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      :param error_message: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.

      :return: Vrací atribut objektu.

   .. py:method:: dokument_doi()

      Provádí operaci dokument doi.

      :return: Vrací atribut objektu.


.. py:class:: DokumentExtraData

   Databázový model doplňkových dat dokumentu.


.. py:class:: DokumentAutor

   Databázový model autorů dokumentu (včetně pořadí).


.. py:class:: DokumentJazyk

   Databázový model jazyků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování.


.. py:class:: DokumentOsoba

   Databázový model osob dokumentu.


.. py:class:: DokumentPosudek

   Databázový model posudků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování.


.. py:class:: Tvar

   Databázový model tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      :param error_message: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.

      :return: Vrací atribut objektu.


.. py:class:: DokumentSekvence

   Databázový model sekvence dokumentu podle roku a řady.


.. py:class:: Let

   Databázový model letu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'let')``.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací výsledek volání ``reverse()``.


Funkce
------

.. py:function:: get_dokument_soubor_name(dokument, filename, add_to_index)

   Funkce pro získaní správného jména souboru.

   :param dokument: Parametr ``dokument`` předává se do volání ``debug()``, ``filter()``, pracuje se s atributy ``ident_cely``, ``soubory``, vstupuje do návratové hodnoty.
   :param filename: Parametr ``filename`` se předává do volání ``splitext()``, vstupuje do návratové hodnoty.
   :param add_to_index: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.

   :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, bool.
