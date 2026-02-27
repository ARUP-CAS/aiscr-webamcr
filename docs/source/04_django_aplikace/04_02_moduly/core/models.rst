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

      :return: Vrací výsledek provedené operace.


.. py:class:: Soubor

   Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.

   **Metody:**

   .. py:method:: url()

      Provádí operaci url.

      :return: Vrací výsledek provedené operace.

   .. py:method:: repository_uuid()

      Provádí operaci repository uuid.

      :return: Vrací výsledek provedené operace.

   .. py:method:: calculate_sha_512()

      Provádí operaci calculate sha 512.

      :return: Vrací výsledek provedené operace.

   .. py:method:: delete()

      Odstraní záznam objektu.

      :param using: Vstupní hodnota ``using`` pro danou operaci.
      :param keep_parents: Vstupní hodnota ``keep_parents`` pro danou operaci.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: create_soubor_vazby()

      Metoda pro vytvoření vazby na historii.

   .. py:method:: vytvoreno()

      Provádí operaci vytvoreno.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_repository_content()

      Vrací repository content.

      :param ident_cely_old: Vstupní hodnota ``ident_cely_old`` pro danou operaci.
      :param thumb_small: Vstupní hodnota ``thumb_small`` pro danou operaci.
      :param thumb_large: Vstupní hodnota ``thumb_large`` pro danou operaci.
      :param timestamp: Vstupní hodnota ``timestamp`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: zaznamenej_nahrani()

      Metoda pro zapsáni vytvoření souboru do historie.

   .. py:method:: zaznamenej_nahrani_nove_verze()

      Metoda pro zapsáni nahrání nové verze souboru do historie.

   .. py:method:: get_file_extension_by_mime()

      Vrací file extension by mime.

      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_thumb_icon()

      Vrací thumb icon.

      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_mime_types()

      Vrací mime types.

      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :param check_archive: Vstupní hodnota ``check_archive`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: remove_gps_data()

      Provádí operaci remove gps data.

      :param bytes_io: Vstupní hodnota ``bytes_io`` pro danou operaci.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: check_mime_for_url()

      Ověří mime for url.

      :param file: Vstupní hodnota ``file`` pro danou operaci.
      :param source_url: Vstupní hodnota ``source_url`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.


      **Argumenty:**

      - ``bytes_io``: souborový objekt ke skenování

      **Návratová hodnota:**

      *AntivirusCheckResult*: výsledek kontroly

   .. py:method:: _create_file_response()

      Vytvoří file response.

      :param rep_bin_file: Vstupní hodnota ``rep_bin_file`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: large_thumbnail()

      Provádí operaci large thumbnail.

      :return: Vrací výsledek provedené operace.

   .. py:method:: small_thumbnail()

      Provádí operaci small thumbnail.

      :return: Vrací výsledek provedené operace.

   .. py:method:: content_file_response()

      Provádí operaci content file response.

      :return: Vrací výsledek provedené operace.

   .. py:method:: getMock()

      Provádí operaci getMock.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích ve Fedoře pro tabulku historie

   .. py:method:: get_soubor_historicky()

      Metoda k získání vlastního souboru dané verze z Fedory


.. py:class:: ProjektSekvence

   Model pro tabulku se sekvencemi projektu.


.. py:class:: OdstavkaSystemu

   Model pro tabulku s odstávkami systému.

   **Metody:**

   .. py:method:: clean()

      Metoda clean, kde se navíc kontrolu, jestli už není jedna odstávka uložena.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: Permissions

   Implementuje komponentu ``Permissions`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_concrete_permission()

      Ověří concrete permission.

      :param user: Vstupní hodnota ``user`` pro danou operaci.
      :param ident: Vstupní hodnota ``ident`` pro danou operaci.
      :param typ: Vstupní hodnota ``typ`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_base()

      Ověří base.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_status()

      Ověří status.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_ownership()

      Ověří ownership.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_accessibility()

      Ověří accessibility.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: check_permission_skip()

      Ověří permission skip.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: permission_override()

      Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.


.. py:class:: PermissionsSkip

   Implementuje komponentu ``PermissionsSkip`` v rámci aplikace.


Funkce
------

.. py:function:: get_upload_to(instance, filename)

   Funkce pro získaní cesty, kde se ma daný typ souboru uložit.

.. py:function:: check_permissions(action, user, ident)

   Ověří permissions.

   :param action: Vstupní hodnota ``action`` pro danou operaci.
   :param user: Vstupní hodnota ``user`` pro danou operaci.
   :param ident: Vstupní hodnota ``ident`` pro danou operaci.
   :return: Vrací výsledek ověření nebo validačního pravidla.
