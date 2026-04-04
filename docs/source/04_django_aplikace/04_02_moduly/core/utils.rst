CORE utils
==========

Modul utils.

Třídy
------

.. py:class:: CannotFindCadasterCentre

   Implementuje komponentu ``CannotFindCadasterCentre`` v rámci aplikace.


.. py:class:: SearchTable

   Základní setup pro tabulky používané v aplikaci.

   Obsahuje metodu na získaní sloupců které mají byt zobrazeny.

   **Metody:**

   .. py:method:: get_column_default_show()

      Vrací column default show.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_column_default_show()``.


   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      **Parametry:**

      - ``value``: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      - ``record``: Parametr ``record`` předává se do volání ``reverse()``, pracuje se s atributy ``soubory``, ``ident_cely``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.


   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů záznamů tabulky.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.



.. py:class:: SessionIdentifier

   Implementuje komponentu ``SessionIdentifier`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``_generate_session_key()``.


   .. py:method:: _generate_session_key()

      Vygeneruje session key.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``session``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: clear_cached_files()

      Provádí operaci clear cached files.

   .. py:method:: set_ident()

      Uloží identifikátor záznamu do session cache.

      Při změně identifikátoru vymaže cache souborů.

      **Parametry:**

      - ``ident_cely``: Identifikátor záznamu ukládaný do cache.
      - ``timeout``: Platnost hodnoty v cache v sekundách.


   .. py:method:: get_ident()

      Vrací ident. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: add_file_reference()

      Provádí operaci add file reference.

      **Parametry:**

      - ``ident``: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
      - ``timeout``: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.


   .. py:method:: file_exists()

      Zjistí, zda je identifikátor mezi referencemi na soubory v session cache.

      **Parametry:**

      - ``ident``: Identifikátor souboru nebo záznamu k ověření.


   .. py:method:: remove_file_reference()

      Provádí operaci remove file reference.

      **Parametry:**

      - ``ident``: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.


   .. py:method:: get_cached_files()

      Vrací cached files.

      **Návratová hodnota:**

      Vrací proměnná ``files``.


   .. py:method:: set_project_ownership()

      Uloží vlastnictví projektu pro anonymního uživatele do Redis.
      Používá se pro ověření, že anonymní uživatel může nahrávat soubory pouze k projektu, který sám vytvořil.

      **Parametry:**

      - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``set()``.
      - ``timeout``: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.


   .. py:method:: verify_project_ownership()

      Ověří, zda anonymní uživatel vlastní daný projekt.

      **Parametry:**

      - ``ident_cely``: Parametr ``ident_cely`` vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.



Funkce
------

.. py:function:: file_validate_epsg(epsg)

   Ověří, zda je zadaný EPSG kód podporován (aktuálně pouze WGS-84/4326).

   **Parametry:**

   - ``epsg``: EPSG kód souřadnicového systému k ověření.

   **Návratová hodnota:**

   ``True`` pokud je EPSG=4326, ``False`` jinak.


.. py:function:: balanced_parentheses(expression)

   Ověří, zda má výraz vyrovnané závorky (stejný počet otevíracích a zavíracích).

   **Parametry:**

   - ``expression``: Řetězec výrazu k ověření.

   **Návratová hodnota:**

   ``True`` pokud jsou závorky vyrovnané, ``False`` jinak.


.. py:function:: load_database_translation_strings()

   Načte database translation strings.

   **Návratová hodnota:**

   Vrací seznam.


.. py:function:: validate_and_split_geometry(geom)

   Funkce pro validaci řetězce s WKT geometrií.

   **Parametry:**

   - ``geom``: Parametr ``geom`` předává se do volání ``isinstance()``, ``append()``, pracuje se s atributy ``iloc``, ``copy``, ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací proměnná ``new_rows``.


.. py:function:: get_mime_type(file_name)

   Funkce pro získaní mime typu pro soubor.

   **Parametry:**

   - ``file_name``: Parametr ``file_name`` se předává do volání ``guess_type()``, pracuje se s atributy ``endswith``, ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací proměnná ``mime_type``.


.. py:function:: get_cadastre_from_point(point)

   Funkce pro získaní katastru z bodu geomu.

   **Parametry:**

   - ``point``: Parametr ``point`` předává se do volání ``raw()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: proměnná ``katastr``, None.


.. py:function:: get_cadastre_from_point_with_geometry(point)

   Funkce pro získaní katastru s geometrií z bodu geomu.

   **Parametry:**

   - ``point``: Parametr ``point`` předává se do volání ``debug()``, ``execute()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: seznam, None.


.. py:function:: get_all_pians_with_akce(ident_cely)

   Funkce pro získaní všech pianů s akci.

   **Parametry:**

   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``execute()``.

   **Návratová hodnota:**

   ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


.. py:function:: update_main_katastr_within_ku(ident_cely, katastr)

   Funkce pro update katastru u akce podle katastrálního území.

   **Parametry:**

   - ``ident_cely``: Parametr ``ident_cely`` pracuje se s atributy ``split``.
   - ``katastr``: Parametr ``katastr`` předává se do volání ``execute()``, pracuje se s atributy ``pk``.


.. py:function:: update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)

   Aktualizuje katastry pro všechny akce a lokality související s dokumentační jednotkou.

   **Parametry:**

   - ``dj``: Dokumentační jednotka obsahující odkaz na akci/lokalitu.
   - ``fedora_transaction``: Aktivní Fedora transakce pro uložení metadat.


.. py:function:: get_pians_from_akce(katastr, akce_ident_cely)

   Funkce pro bodu, geomu a presnosti z akce.

   **Parametry:**

   - ``katastr``: Parametr ``katastr`` předává se do volání ``debug()``, ``raw()``, pracuje se s atributy ``pk``.
   - ``akce_ident_cely``: Identifikátor ``akce_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací proměnná ``pians``.

   **Výjimky:**

   - ``CannotFindCadasterCentre``: Vyvolá se při zpracování zachycené výjimky typu ``IndexError``.


.. py:function:: get_dj_pians_centroid(ident_cely, lat, lng)

   Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.

   **Parametry:**

   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``raw()``, pracuje se s atributy ``rindex``.
   - ``lat``: Parametr ``lat`` se předává do volání ``raw()``.
   - ``lng``: Parametr ``lng`` se předává do volání ``raw()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: proměnná ``pians``, None.


.. py:function:: get_num_pians_from_envelope(left, bottom, right, top)

   Funkce pro získaní počtu pianů ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, None.


.. py:function:: get_dj_pians_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``raw()``, ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``raw()``, ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``raw()``, ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``raw()``, ``debug()``.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``raw()``.

   **Návratová hodnota:**

   ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


.. py:function:: get_project_geom(ident_cely)

   Funkce pro získaní geometrie projekt.

   Bez pristupnosti

   **Parametry:**

   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``Q()``, ``debug()``.

   **Návratová hodnota:**

   ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


.. py:function:: get_num_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní počtu projektů ze čtverce.

   Bez pristupnosti

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``right``: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``top``: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``stavy``: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_num_projects_from_envelope``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``count()``, None.


.. py:function:: get_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní projektů ze čtverce.

   Bez pristupnosti

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``right``: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``top``: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``stavy``: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_projects_from_envelope``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.


.. py:function:: get_project_pas_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pas projekt ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``debug()``.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``Q()``.

   **Návratová hodnota:**

   ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


.. py:function:: get_project_pian_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů projektu ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``debug()``.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``filter()``.

   **Návratová hodnota:**

   ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


.. py:function:: get_3d_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní 3d ze čtverce.
   Bez pristupnosti

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``right``: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``top``: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_3d_from_envelope``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.


.. py:function:: get_num_pass_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní počtu pas ze čtverce.

   musi zohlednit pristupnost [mapa_pas]

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``right``: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``top``: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_num_pass_from_envelope``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``count()``, None.


.. py:function:: get_pas_from_envelope(bounds, request)

   Funkce pro získaní pas ze čtverce.

   musi zohlednit pristupnost [mapa_pas]

   **Parametry:**

   - ``bounds``: Parametr ``bounds`` předává se do volání ``Q()``, ``Polygon()``.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_pas_from_envelope``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``only()``, None.


.. py:function:: get_pian_from_envelope(bounds, zoom, request)

   Funkce pro získaní pianů ze čtverce.

   musi zohlednit pristupnost [mapa_pian]

   **Parametry:**

   - ``bounds``: Parametr ``bounds`` slouží jako vstup pro logiku funkce ``get_pian_from_envelope``.
   - ``zoom``: Parametr ``zoom`` ovlivňuje větvení podmínek.
   - ``request``: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací n-tici.


.. py:function:: get_dj_akce_for_pian(pian_ident_cely, request)

   Funkce pro pro ziskani dj/akce pro pian_ident_cely

   **Parametry:**

   - ``pian_ident_cely``: Identifikátor ``pian_ident_cely`` používaný pro dohledání cílového záznamu.
   - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_dj_akce_for_pian``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.


.. py:function:: dictfetchall(cursor)

   Return all rows from a cursor as a dict

   **Parametry:**

   - ``cursor``: Parametr ``cursor`` pracuje se s atributy ``description``, ``fetchall``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování.


.. py:function:: get_heatmap_pian(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pianů ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   - ``zoom``: Parametr ``zoom`` ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.


.. py:function:: get_heatmap_pas(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pass ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   - ``zoom``: Parametr ``zoom`` ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.


.. py:function:: get_heatmap_project(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy projektů ze čtverce.

   **Parametry:**

   - ``left``: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   - ``bottom``: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   - ``right``: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   - ``top``: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   - ``zoom``: Parametr ``zoom`` ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.


.. py:function:: get_message(az, message)

   Funkce pro získaní textu správy podle záznamu.

   **Parametry:**

   - ``az``: Parametr ``az`` se předává do volání ``str()``, ``getattr()``, pracuje se s atributy ``typ_zaznamu``, vstupuje do návratové hodnoty.
   - ``message``: Parametr ``message`` předává se do volání ``str()``, ``getattr()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací výsledek volání ``str()``.


.. py:function:: find_pos_with_backup(lang, project_apps, django_apps, third_party_apps)

   scans a couple possible repositories of gettext catalogs for the given

   language code

   **Parametry:**

   - ``lang``: Textová hodnota `lang` používaná pro vyhledání, pojmenování nebo hlášení stavu.
   - ``project_apps``: Parametr ``project_apps`` ovlivňuje větvení podmínek.
   - ``django_apps``: Parametr ``django_apps`` ovlivňuje větvení podmínek.
   - ``third_party_apps``: Parametr ``third_party_apps`` ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací výsledek volání ``list()``.


.. py:function:: replace_last(source_string, old, new)

   Nahradí poslední výskyt řetězce v textu novým řetězcem.

   **Parametry:**

   - ``source_string``: Vstupní text.
   - ``old``: Řetězec k nahrazení.
   - ``new``: Nový řetězec.

   **Návratová hodnota:**

   Text s nahrazeným poslední výskytem.


.. py:function:: get_set_maintenance_in_cache()

   Funkce pro získání nastavení údržby z cache.

   **Návratová hodnota:**

   Vrací proměnná ``maintenance``.


.. py:function:: is_maintenance_in_progress()

   Funkce pro zjištění, zda je údržba v průběhu.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:function:: get_timezone()

   Funkce pro získání časového pásma z nastavení.

   **Návratová hodnota:**

   Vrací výsledek volání ``timezone()``.

