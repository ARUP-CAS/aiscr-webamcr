CORE modely
===========

Definice modelů.

Třídy
------

.. py:class:: AntivirusCheckResult

   Popis není k dispozici.


.. py:class:: SouborVazby

   Model pro relační tabulku mezi souborem a záznamem.
   Obsahuje typ vazby podle typu záznamu.

   **Metody:**

   .. py:method:: navazany_objekt()


.. py:class:: Soubor

   Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.

   **Metody:**

   .. py:method:: url()

   .. py:method:: repository_uuid()

   .. py:method:: calculate_sha_512()

   .. py:method:: delete()

   .. py:method:: __init__()

   .. py:method:: __str__()

   .. py:method:: create_soubor_vazby()

      Metoda pro vytvoření vazby na historii.

   .. py:method:: vytvoreno()

   .. py:method:: get_repository_content()

   .. py:method:: zaznamenej_nahrani()

      Metoda pro zapsáni vytvoření souboru do historie.

   .. py:method:: zaznamenej_nahrani_nove_verze()

      Metoda pro zapsáni nahrání nové verze souboru do historie.

   .. py:method:: get_file_extension_by_mime()

   .. py:method:: get_thumb_icon()

   .. py:method:: get_mime_types()

   .. py:method:: remove_gps_data()

      Odstraní GPS metadata z fotografie uložené v paměti.

      Funkce načte EXIF data z obrázku, odstraní GPS informace a pokusí se
      znovu uložit EXIF. Pokud narazí na nevalidní nebo nekompatibilní EXIF
      tagy (např. UserComment, MakerNote apod.), automaticky je odstraní,
      aby bylo možné obrázek úspěšně uložit.

      V případě jakékoli chyby vrací původní vstupní soubor beze změny.

      :param bytes_io: Vstupní obrázek jako BytesIO objekt
      :return: BytesIO objekt s odstraněnými GPS daty (nebo původní soubor při chybě)

   .. py:method:: check_mime_for_url()

   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.


      **Argumenty:**

      - ``bytes_io``: souborový objekt ke skenování

      **Návratová hodnota:**

      *AntivirusCheckResult*: výsledek kontroly

   .. py:method:: _create_file_response()

   .. py:method:: large_thumbnail()

   .. py:method:: small_thumbnail()

   .. py:method:: content_file_response()

   .. py:method:: getMock()

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


.. py:class:: Permissions

   Popis není k dispozici.

   **Metody:**

   .. py:method:: check_concrete_permission()

   .. py:method:: check_base()

   .. py:method:: check_status()

   .. py:method:: check_ownership()

   .. py:method:: check_accessibility()

   .. py:method:: check_permission_skip()

   .. py:method:: get_permission_object()

   .. py:method:: permission_override()

      Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.


.. py:class:: PermissionsSkip

   Popis není k dispozici.


Funkce
------

.. py:function:: get_upload_to(instance, filename)

   Funkce pro získaní cesty, kde se ma daný typ souboru uložit.

.. py:function:: check_permissions(action, user, ident)

   Popis není k dispozici.
