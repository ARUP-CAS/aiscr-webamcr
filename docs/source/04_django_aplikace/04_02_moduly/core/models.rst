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

      :return: Navázaný objekt (Projekt, Dokument nebo SamostatnyNalez).


.. py:class:: Soubor

   Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.

   **Metody:**

   .. py:method:: url()

      Vrátí URL pro přístup k souboru.

      :return: URL souboru nebo prázdný řetězec.

   .. py:method:: repository_uuid()

      Vrátí UUID souboru v repozitáři.

      :return: Vrací vybranou hodnotu z kolekce.

   .. py:method:: calculate_sha_512()

      Vrátí SHA-512 hash souboru uloženého v Fedora repozitáři.

      :return: Haš souboru ze skladiště nebo prázdný řetězec, pokud soubor neexistuje.

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

      Vrátí záznam historie s typem zmény "Nahrání SBR" (prvního nahrání souboru).

      :return: Záznam historie nebo ``None``, pokud soubor nevlastní historii.

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

   .. py:method:: zaznamenej_prejmenovani()

      Metoda pro zapsání přejmenování souboru do historie.

      Do poznámky se uloží změna ve tvaru ``původní_název -> nový_název``.

      :param user: Uživatel, který přejmenování provedl.
      :param old_nazev: Původní název souboru.
      :param new_nazev: Nový název souboru.

   .. py:method:: get_file_extension_by_mime()

      Vrací file extension by mime.

      :param file: Soubor nebo cesta k souboru používaná při operaci.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: _detect_mime()

      Detekuje MIME typ souboru pomocí ``libmagic`` s workaroundem pro regresi v ``libmagic >= 5.46``,
      kde běžný ZIP s obsahem je vrácen jako ``application/octet-stream``.

      :param file: File-like objekt s podporou ``seek`` a ``read``.
      :return: Detekovaný MIME typ.

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

      Odstraní GPS metadata z fotografie uložené v paměti.

      Funkce načte EXIF data z obrázku, odstraní GPS informace a pokusí se
      znovu uložit EXIF. Pokud narazí na nevalidní nebo nekompatibilní EXIF
      tagy (např. UserComment, MakerNote apod.), automaticky je odstraní,
      aby bylo možné obrázek úspěšně uložit.

      V případě jakékoli chyby vrací původní vstupní soubor beze změny.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Vrací výsledek operace odstranění.

   .. py:method:: check_mime_for_url()

      Ověří, zda detekovaný MIME typ souboru spadá do whitelistu pro danou upload URL.

      Whitelisty per větev musí odpovídat seznamům v ``static/js/dz.js``.

      :param file: Soubor nebo cesta k souboru používaná při operaci.
      :param source_url: URL uploadu — určuje, který whitelist se použije
          (``pas``, ``dokument``, ``model3d`` nebo výchozí ``projekt``).
      :return: ``True``/``False`` podle výsledku kontroly, případně řetězec
          ``"encrypted"`` u zaheslovaných archivů.

   .. py:method:: check_antivirus()

      Zkontroluje soubor na přítomnost virů pomocí ClamAV.

      :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
      :return: Výsledek antivirové kontroly (`PASSES`, `VIRUS_FOUND`, `CHECK_FAILED` nebo `SKIPPED`).

   .. py:method:: _create_file_response()

      Vytvoří file response.

      :param rep_bin_file: Parametr ``rep_bin_file`` pracuje se s atributy ``content``.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: large_thumbnail()

      Vrátí větší náhled obrázku.

      :return: FileResponse s náhledem nebo None.

   .. py:method:: small_thumbnail()

      Vrátí menší náhled obrázku.

      :return: FileResponse s náhledem nebo None.

   .. py:method:: content_file_response()

      Vrátí soubor jako HTTP response.

      :return: FileResponse se souborem nebo None.

   .. py:method:: getMock()

      Vrátí mock reprezentaci souboru.

      :return: Slovník s daty souboru.

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

      Ověří, zda má uživatel konkrétní oprávnění na daný záznam a typ.

      :param user: Uživatel, pro kterého se kontroluje oprávnění.
      :param ident: Identifikátor archeologického záznamu (např. C-XX-YYYYNNNNN).
      :param typ: Typ objektu, pro který se kontroluje oprávnění (např. projekt, lokalita).
      :param skip_status: Pokud ``True``, přeskočí stavovou podmínku oprávnění a vyhodnotí pouze
          základ, vlastnictví a přístupnost.
      :return: ``True`` pokud má uživatel oprávnění, ``False`` jinak.

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

   Určí cestu pro uložení souboru.

   :param instance: Instance souboru.
   :param filename: Název souboru.
   :return: Cesta pro uložení souboru.

.. py:function:: soubor_nazev_razeni_klic(soubor)

   Vrátí řadicí klíč souboru podle názvu.

   Při porovnání se tečka chová jako znak ``0``, což zachovává dosavadní pořadí
   výpisu souborů v detailu záznamu (např. ``foto.jpg`` před ``foto2.jpg``). Používá
   se pro jednotné určení pořadí souborů i výběr náhledového souboru napříč
   dokumenty, 3D modely i samostatnými nálezy.

   :param soubor: Soubor, z jehož názvu se klíč sestaví.
   :return: N-tice použitelná jako ``key`` pro ``sorted`` nebo ``min``.

.. py:function:: prvni_soubor_dle_nazvu(soubory)

   Vrátí náhledový soubor jako první soubor seřazený podle názvu.

   Pořadí odpovídá výpisu souborů v detailu (viz :func:`soubor_nazev_razeni_klic`),
   takže náhled je vždy první soubor v seznamu.

   :param soubory: Iterovatelná kolekce souborů.
   :return: Soubor s nejnižším řadicím klíčem názvu, nebo None pro prázdný vstup.

.. py:function:: check_permissions(action, user, ident, skip_status)

   Ověří permissions. v aplikaci.

   :param action: Identifikátor akce, která se má provést.
   :param user: Parametr ``user`` se předává do volání ``filter()``, ``append()``, pracuje se s atributy ``hlavni_role``.
   :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
   :param skip_status: Pokud ``True``, přeskočí stavovou podmínku při vyhodnocení konkrétního oprávnění.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
