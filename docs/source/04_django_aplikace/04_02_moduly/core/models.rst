CORE modely
===========

Definice modelů.

Třídy
------

.. py:class:: AntivirusCheckResult

   Implementuje komponentu ``AntivirusCheckResult`` v rámci aplikace.


.. py:class:: SouborVazby

   Model pro relační tabulku mezi souborem a záznamem.

   Obsahuje typ vazby podle typu záznamu.

   **Metody:**

   .. py:method:: navazany_objekt()

      Provádí operaci navazany objekt.

      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: Soubor

   Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.

   **Metody:**

   .. py:method:: url()

      Provádí operaci url.

   .. py:method:: repository_uuid()

      Provádí operaci repository uuid.

   .. py:method:: calculate_sha_512()

      Provádí operaci calculate sha 512.

   .. py:method:: delete()

      Odstraní záznam objektu.

      :param using: Alias databázového spojení použitý při operaci.
      :param keep_parents: Číselná nebo geometrická hodnota `keep_parents` použitá při výpočtu nebo transformaci.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: create_soubor_vazby()

      Metoda pro vytvoření vazby na historii.

   .. py:method:: vytvoreno()

      Provádí operaci vytvoreno.

   .. py:method:: get_repository_content()

      Vrací repository content.

      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param thumb_small: Číselná nebo geometrická hodnota `thumb_small` použitá při výpočtu nebo transformaci.
      :param thumb_large: Číselná nebo geometrická hodnota `thumb_large` použitá při výpočtu nebo transformaci.
      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: zaznamenej_nahrani()

      Metoda pro zapsáni vytvoření souboru do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: zaznamenej_nahrani_nove_verze()

      Metoda pro zapsáni nahrání nové verze souboru do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param nazev: Číselná nebo geometrická hodnota `nazev` použitá při výpočtu nebo transformaci.

   .. py:method:: get_file_extension_by_mime()

      Vrací file extension by mime.

      :param file: Soubor nebo cesta k souboru používaná při operaci.

   .. py:method:: get_thumb_icon()

      Vrací thumb icon.

      :param file: Soubor nebo cesta k souboru používaná při operaci.

   .. py:method:: get_mime_types()

      Vrací mime types.

      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param check_archive: Příznak ``check_archive`` určující průběh nebo rozsah zpracování.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: remove_gps_data()

      Provádí operaci remove gps data.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: check_mime_for_url()

      Ověří mime for url.

      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param source_url: Cesta, URL nebo název zdroje ``source_url``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Výsledek antivirové kontroly (`PASSES`, `VIRUS_FOUND`, `CHECK_FAILED` nebo `SKIPPED`).

   .. py:method:: _create_file_response()

      Vytvoří file response.

      :param rep_bin_file: Cesta, URL nebo název zdroje ``rep_bin_file``, ze kterého funkce čte nebo kam zapisuje.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: content_file_response()

      Provádí operaci content file response.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: getMock()

      Provádí operaci getMock.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích ve Fedoře pro tabulku historie

   .. py:method:: get_soubor_historicky()

      Metoda k získání vlastního souboru dané verze z Fedory

      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
      :return: Vrací výsledek operace.


.. py:class:: ProjektSekvence

   Model pro tabulku se sekvencemi projektu.


.. py:class:: OdstavkaSystemu

   Model pro tabulku s odstávkami systému.

   **Metody:**

   .. py:method:: clean()

      Metoda clean, kde se navíc kontrolu, jestli už není jedna odstávka uložena.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Textová reprezentace odstávky systému.


.. py:class:: Permissions

   Implementuje komponentu ``Permissions`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_concrete_permission()

      Ověří concrete permission.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
      :param typ: Název nebo typ ``typ`` používaný pro volbu cílové logiky.

   .. py:method:: check_base()

      Ověří base. v aplikaci.

   .. py:method:: check_status()

      Ověří status. v aplikaci.

   .. py:method:: check_ownership()

      Ověří ownership. v aplikaci.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.

   .. py:method:: check_accessibility()

      Ověří accessibility. v aplikaci.

   .. py:method:: check_permission_skip()

      Ověří permission skip.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: permission_override()

      Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.


.. py:class:: PermissionsSkip

   Implementuje komponentu ``PermissionsSkip`` v rámci aplikace.


Funkce
------

.. py:function:: get_upload_to(instance, filename)

   Funkce pro získaní cesty, kde se ma daný typ souboru uložit.

   :param instance: Instance modelu, které se operace týká.
   :param filename: Cesta, URL nebo název zdroje ``filename``, ze kterého funkce čte nebo kam zapisuje.

.. py:function:: check_permissions(action, user, ident)

   Ověří permissions. v aplikaci.

   :param action: Identifikátor akce, která se má provést.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
