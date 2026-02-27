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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu dokumentu.

   .. py:method:: set_doi()

      Nastaví doi.

      :return: Vrací výsledek provedené operace.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

   .. py:method:: set_permanent_identificator()

      Nastaví permanent identificator.

      :param dokument: Vstupní hodnota ``dokument`` pro danou operaci.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param messages: Vstupní hodnota ``messages`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: format, popis, duveryhodnost, obdobi, areal jsou vyplněna pro model 3D.

      polia: pristupnost, popis, ulozeni_originalu jsou vyplněna pro model 3D.

      Dokument má aspoň jeden dokument.

   .. py:method:: check_pred_archivaci()

      Metoda na kontrolu prerekvizit pred archivací:

      kontrola jako před odesláním

   .. py:method:: has_extra_data()

      Metoda na zjištení že dokument má extra data.

   .. py:method:: get_komponenta()

      Metoda na získaní všech komponent dokumentu.

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro dokument.
      Metoda bere pořadoví číslo z db dokument sekvence.
      Metoda zmení i ident připojených souborů.

   .. py:method:: set_datum_zverejneni()

      metoda pro nastavení datumu zvěřejnení.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: thumbnail_image()

      Provádí operaci thumbnail image.

      :return: Vrací výsledek provedené operace.

   .. py:method:: thumbnail_image_file()

      Provádí operaci thumbnail image file.

      :return: Vrací výsledek provedené operace.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

      :return: Vrací výsledek provedené operace.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

      :return: Vrací výsledek provedené operace.

   .. py:method:: set_snapshots()

      Nastaví snapshots.

      :return: Vrací výsledek provedené operace.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací výsledek provedené operace.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _get_doi_client()

      Vrací doi client.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: doi_exists()

      Provádí operaci doi exists.

      :return: Vrací výsledek provedené operace.

   .. py:method:: doi_delete()

      Provádí operaci doi delete.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: doi_hide()

      Provádí operaci doi hide.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: doi_publish()

      Provádí operaci doi publish.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: doi_update()

      Provádí operaci doi update.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :param reload_record: Vstupní hodnota ``reload_record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: doi_url()

      Provádí operaci doi url.

      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentCast

   Databázový model části dokumentu.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: initial_archeologicky_zaznam()

      Vrátí objekt dokument na základě initial_archeologicky_zaznam_id (líné načtení).

   .. py:method:: initial_projekt()

      Provádí operaci initial projekt.

      :return: Vrací výsledek provedené operace.

   .. py:method:: create_transaction()

      Vytvoří transaction.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: dokument_doi()

      Provádí operaci dokument doi.

      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentExtraData

   Databázový model doplňkových dat dokumentu.


.. py:class:: DokumentAutor

   Databázový model autorů dokumentu (včetně pořadí).


.. py:class:: DokumentJazyk

   Databázový model jazyků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentOsoba

   Databázový model osob dokumentu.


.. py:class:: DokumentPosudek

   Databázový model posudků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: Tvar

   Databázový model tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: create_transaction()

      Vytvoří transaction.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.


.. py:class:: DokumentSekvence

   Databázový model sekvence dokumentu podle roku a řady.


.. py:class:: Let

   Databázový model letu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: get_dokument_soubor_name(dokument, filename, add_to_index)

   Funkce pro získaní správného jména souboru.
