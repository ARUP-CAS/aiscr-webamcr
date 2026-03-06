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

      :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, str.

   .. py:method:: repository_uuid()

      Provádí operaci repository uuid.

      :return: Vrací vybranou hodnotu z kolekce.

   .. py:method:: calculate_sha_512()

      Provádí operaci calculate sha 512.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: delete()

      Odstraní záznam objektu.

      :param using: Alias databázového spojení použitý při operaci.
      :param keep_parents: Parametr ``keep_parents`` se předává do volání ``delete()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: create_soubor_vazby()

      Metoda pro vytvoření vazby na historii.

   .. py:method:: vytvoreno()

      Provádí operaci vytvoreno.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``first()``, None.

   .. py:method:: get_repository_content()

      Vrací repository content.

      :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      :param thumb_small: Parametr ``thumb_small`` se předává do volání ``get_binary_file()``.
      :param thumb_large: Parametr ``thumb_large`` se předává do volání ``get_binary_file()``.
      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: zaznamenej_nahrani()

      Metoda pro zapsáni vytvoření souboru do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param file_name: Parametr ``file_name`` se předává do volání ``Historie()``.

   .. py:method:: zaznamenej_nahrani_nove_verze()

      Metoda pro zapsáni nahrání nové verze souboru do historie.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param nazev: Parametr ``nazev`` se předává do volání ``Historie()``, ovlivňuje větvení podmínek.

   .. py:method:: get_file_extension_by_mime()

      Vrací file extension by mime.

      :param file: Soubor nebo cesta k souboru používaná při operaci.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_thumb_icon()

      Vrací thumb icon.

      :param file: Soubor nebo cesta k souboru používaná při operaci.

      :return: Vrací n-tici.

   .. py:method:: get_mime_types()

      Vrací mime types.

      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param check_archive: Parametr ``check_archive`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: remove_gps_data()

      Provádí operaci remove gps data.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: check_mime_for_url()

      Ověří mime for url.

      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param source_url: Parametr ``source_url`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``mime``, bool.

   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Výsledek antivirové kontroly (`PASSES`, `VIRUS_FOUND`, `CHECK_FAILED` nebo `SKIPPED`).

   .. py:method:: _create_file_response()

      Vytvoří file response.

      :param rep_bin_file: Parametr ``rep_bin_file`` pracuje se s atributy ``content``.
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

      :return: Vrací slovník.

   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích ve Fedoře pro tabulku historie

      :return: Vrací proměnná ``results``.

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

      :raises ValidationError: Vyvolá se při splnění podmínky ``odstavky.first().pk != self.pk``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Textová reprezentace odstávky systému.


.. py:class:: Permissions

   Implementuje komponentu ``Permissions`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_concrete_permission()

      Ověří concrete permission.

      :param user: Parametr ``user`` slouží jako vstup pro logiku funkce ``check_concrete_permission``.
      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
      :param typ: Parametr ``typ`` slouží jako vstup pro logiku funkce ``check_concrete_permission``.

      :return: Vrací hodnotu podle větve zpracování, typicky: bool, proměnná ``perm_check``.

   .. py:method:: check_base()

      Ověří base. v aplikaci.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: check_status()

      Ověří status. v aplikaci.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: check_ownership()

      Ověří ownership. v aplikaci.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: check_accessibility()

      Ověří accessibility. v aplikaci.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: check_permission_skip()

      Ověří permission skip.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: permission_override()

      Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:class:: PermissionsSkip

   Implementuje komponentu ``PermissionsSkip`` v rámci aplikace.


Funkce
------

.. py:function:: get_upload_to(instance, filename)

   Funkce pro získaní cesty, kde se ma daný typ souboru uložit.

   :param instance: Parametr ``instance`` předává se do volání ``fullmatch()``, ``join()``, pracuje se s atributy ``vazba``, ``nazev``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param filename: Parametr ``filename`` slouží jako vstup pro logiku funkce ``get_upload_to``.

   :return: Vrací výsledek volání ``join()``.

.. py:function:: check_permissions(action, user, ident)

   Ověří permissions. v aplikaci.

   :param action: Identifikátor akce, která se má provést.
   :param user: Parametr ``user`` se předává do volání ``filter()``, ``append()``, pracuje se s atributy ``hlavni_role``.
   :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
