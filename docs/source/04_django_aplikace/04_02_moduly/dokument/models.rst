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

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu dokumentu.

   .. py:method:: set_doi()

      Nastaví doi. v aplikaci.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: set_permanent_identificator()

      Nastaví permanent identificator.

      :param dokument: Doménový objekt `dokument`, se kterým funkce pracuje.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param messages: Textová zpráva ``messages`` používaná pro hlášení stavu nebo chyby.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      Výsledek provedené změny nad cílovým objektem.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      :param poznamka: Číselná nebo geometrická hodnota `poznamka` použitá při výpočtu nebo transformaci.

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

      :param region: Číselná nebo geometrická hodnota `region` použitá při výpočtu nebo transformaci.
      :param rada: Číselná nebo geometrická hodnota `rada` použitá při výpočtu nebo transformaci.

   .. py:method:: set_datum_zverejneni()

      metoda pro nastavení datumu zvěřejnení.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: thumbnail_image()

      Provádí operaci thumbnail image.

   .. py:method:: thumbnail_image_file()

      Provádí operaci thumbnail image file.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: _get_doi_client()

      Vrací doi client.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: doi_exists()

      Provádí operaci doi exists.

   .. py:method:: doi_delete()

      Provádí operaci doi delete.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: doi_hide()

      Provádí operaci doi hide.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: doi_publish()

      Provádí operaci doi publish.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: doi_update()

      Provádí operaci doi update.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.
      :param reload_record: Záznam/objekt ``reload_record``, který funkce čte, validuje nebo upravuje.

   .. py:method:: doi_url()

      Provádí operaci doi url.


.. py:class:: DokumentCast

   Databázový model části dokumentu.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: initial_archeologicky_zaznam()

      Vrátí objekt dokument na základě initial_archeologicky_zaznam_id (líné načtení).

      :return: Vrací výsledek operace.

   .. py:method:: initial_projekt()

      Provádí operaci initial projekt.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
      :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.

   .. py:method:: dokument_doi()

      Provádí operaci dokument doi.


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


.. py:class:: DokumentOsoba

   Databázový model osob dokumentu.


.. py:class:: DokumentPosudek

   Databázový model posudků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.


.. py:class:: Tvar

   Databázový model tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
      :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.


.. py:class:: DokumentSekvence

   Databázový model sekvence dokumentu podle roku a řady.


.. py:class:: Let

   Databázový model letu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_absolute_url()

      Vrací absolute url.


Funkce
------

.. py:function:: get_dokument_soubor_name(dokument, filename, add_to_index)

   Funkce pro získaní správného jména souboru.

   :param dokument: Doménový objekt `dokument`, se kterým funkce pracuje.
   :param filename: Cesta, URL nebo název zdroje ``filename``, ze kterého funkce čte nebo kam zapisuje.
   :param add_to_index: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.
