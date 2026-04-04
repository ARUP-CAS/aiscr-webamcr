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

      Vrátí navázaný objekt podle typu vazby.

      **Návratová hodnota:**

      Navázaný objekt (Projekt, Dokument nebo SamostatnyNalez).



.. py:class:: Soubor

   Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.

   **Metody:**

   .. py:method:: url()

      Vrátí URL pro přístup k souboru.

      **Návratová hodnota:**

      URL souboru nebo prázdný řetězec.


   .. py:method:: repository_uuid()

      Vrátí UUID souboru v repozitáři.

      **Návratová hodnota:**

      Vrací vybranou hodnotu z kolekce.


   .. py:method:: calculate_sha_512()

      Vrátí SHA-512 hash souboru uloženého v Fedora repozitáři.

      **Návratová hodnota:**

      Haš souboru ze skladiště nebo prázdný řetězec, pokud soubor neexistuje.


   .. py:method:: delete()

      Odstraní záznam objektu.

      **Parametry:**

      - ``using``: Alias databázového spojení použitý při operaci.
      - ``keep_parents``: Parametr ``keep_parents`` se předává do volání ``delete()``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: create_soubor_vazby()

      Metoda pro vytvoření vazby na historii.

   .. py:method:: vytvoreno()

      Vrátí záznam historie s typem zmény "Nahrání SBR" (prvního nahrání souboru).

      **Návratová hodnota:**

      Záznam historie nebo ``None``, pokud soubor nevlastní historii.


   .. py:method:: get_repository_content()

      Vrací repository content.

      **Parametry:**

      - ``ident_cely_old``: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
      - ``thumb_small``: Parametr ``thumb_small`` se předává do volání ``get_binary_file()``.
      - ``thumb_large``: Parametr ``thumb_large`` se předává do volání ``get_binary_file()``.
      - ``timestamp``: Časový údaj použitý při filtrování nebo výpočtu.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: zaznamenej_nahrani()

      Metoda pro zapsáni vytvoření souboru do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``file_name``: Parametr ``file_name`` se předává do volání ``Historie()``.


   .. py:method:: zaznamenej_nahrani_nove_verze()

      Metoda pro zapsáni nahrání nové verze souboru do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``nazev``: Parametr ``nazev`` se předává do volání ``Historie()``, ovlivňuje větvení podmínek.


   .. py:method:: get_file_extension_by_mime()

      Vrací file extension by mime.

      **Parametry:**

      - ``file``: Soubor nebo cesta k souboru používaná při operaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: get_thumb_icon()

      Vrací thumb icon.

      **Parametry:**

      - ``file``: Soubor nebo cesta k souboru používaná při operaci.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: get_mime_types()

      Vrací mime types.

      **Parametry:**

      - ``file``: Soubor nebo cesta k souboru používaná při operaci.
      - ``check_archive``: Parametr ``check_archive`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: remove_gps_data()

      Odstraní GPS metadata z fotografie uložené v paměti.

      Funkce načte EXIF data z obrázku, odstraní GPS informace a pokusí se
      znovu uložit EXIF. Pokud narazí na nevalidní nebo nekompatibilní EXIF
      tagy (např. UserComment, MakerNote apod.), automaticky je odstraní,
      aby bylo možné obrázek úspěšně uložit.

      V případě jakékoli chyby vrací původní vstupní soubor beze změny.

      **Parametry:**

      - ``bytes_io``: Obsah souboru připravený ke kontrole antivirem.

      **Návratová hodnota:**

      Vrací výsledek operace odstranění.


   .. py:method:: check_mime_for_url()

      Ověří mime for url.

      **Parametry:**

      - ``file``: Soubor nebo cesta k souboru používaná při operaci.
      - ``source_url``: Parametr ``source_url`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``mime``, bool.


   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.

      **Parametry:**

      - ``bytes_io``: Obsah souboru připravený ke kontrole antivirem.

      **Návratová hodnota:**

      Výsledek antivirové kontroly (`PASSES`, `VIRUS_FOUND`, `CHECK_FAILED` nebo `SKIPPED`).


   .. py:method:: _create_file_response()

      Vytvoří file response.

      **Parametry:**

      - ``rep_bin_file``: Parametr ``rep_bin_file`` pracuje se s atributy ``content``.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: large_thumbnail()

      Vrátí větší náhled obrázku.

      **Návratová hodnota:**

      FileResponse s náhledem nebo None.


   .. py:method:: small_thumbnail()

      Vrátí menší náhled obrázku.

      **Návratová hodnota:**

      FileResponse s náhledem nebo None.


   .. py:method:: content_file_response()

      Vrátí soubor jako HTTP response.

      **Návratová hodnota:**

      FileResponse se souborem nebo None.


   .. py:method:: getMock()

      Vrátí mock reprezentaci souboru.

      **Návratová hodnota:**

      Slovník s daty souboru.


   .. py:method:: get_historicke_verze()

      Metoda k získání údajů o historických verzích ve Fedoře pro tabulku historie

      **Návratová hodnota:**

      Vrací proměnná ``results``.


   .. py:method:: get_soubor_historicky()

      Metoda k získání vlastního souboru dané verze z Fedory

      **Parametry:**

      - ``timestamp``: Časový údaj použitý při filtrování nebo výpočtu.

      **Návratová hodnota:**

      Vrací výsledek operace.



.. py:class:: ProjektSekvence

   Model pro tabulku se sekvencemi projektu.


.. py:class:: OdstavkaSystemu

   Model pro tabulku s odstávkami systému.

   **Metody:**

   .. py:method:: clean()

      Metoda clean, kde se navíc kontrolu, jestli už není jedna odstávka uložena.

      **Výjimky:**

      - ``ValidationError``: Vyvolá se při splnění podmínky ``odstavky.first().pk != self.pk``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      **Návratová hodnota:**

      Textová reprezentace odstávky systému.



.. py:class:: Permissions

   Implementuje komponentu ``Permissions`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_concrete_permission()

      Ověří, zda má uživatel konkrétní oprávnění na daný záznam a typ.

      **Parametry:**

      - ``user``: Uživatel, pro kterého se kontroluje oprávnění.
      - ``ident``: Identifikátor archeologického záznamu (např. C-XX-YYYYNNNNN).
      - ``typ``: Typ objektu, pro který se kontroluje oprávnění (např. projekt, lokalita).

      **Návratová hodnota:**

      ``True`` pokud má uživatel oprávnění, ``False`` jinak.


   .. py:method:: check_base()

      Ověří base. v aplikaci.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: check_status()

      Ověří status. v aplikaci.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: check_ownership()

      Ověří ownership. v aplikaci.

      **Parametry:**

      - ``ownership``: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: check_accessibility()

      Ověří accessibility. v aplikaci.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: check_permission_skip()

      Ověří permission skip.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: permission_override()

      Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.



.. py:class:: PermissionsSkip

   Implementuje komponentu ``PermissionsSkip`` v rámci aplikace.


Funkce
------

.. py:function:: get_upload_to(instance, filename)

   Určí cestu pro uložení souboru.

   **Parametry:**

   - ``instance``: Instance souboru.
   - ``filename``: Název souboru.

   **Návratová hodnota:**

   Cesta pro uložení souboru.


.. py:function:: check_permissions(action, user, ident)

   Ověří permissions. v aplikaci.

   **Parametry:**

   - ``action``: Identifikátor akce, která se má provést.
   - ``user``: Parametr ``user`` se předává do volání ``filter()``, ``append()``, pracuje se s atributy ``hlavni_role``.
   - ``ident``: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

