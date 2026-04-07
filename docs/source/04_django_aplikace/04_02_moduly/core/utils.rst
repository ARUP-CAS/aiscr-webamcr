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

      :return: Vrací výsledek volání ``get_column_default_show()``.

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      :param record: Parametr ``record`` předává se do volání ``reverse()``, pracuje se s atributy ``soubory``, ``ident_cely``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.

   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů záznamů tabulky.

      :return: Vrací výsledek volání ``join()``.


.. py:class:: SessionIdentifier

   Implementuje komponentu ``SessionIdentifier`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param request: Parametr ``request`` předává se do volání ``_generate_session_key()``.

   .. py:method:: _generate_session_key()

      Vygeneruje session key.

      :param request: Parametr ``request`` pracuje se s atributy ``session``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: clear_cached_files()

      Provádí operaci clear cached files.

   .. py:method:: set_ident()

      Uloží identifikátor záznamu do session cache.

      Při změně identifikátoru vymaže cache souborů.

      :param ident_cely: Identifikátor záznamu ukládaný do cache.
      :param timeout: Platnost hodnoty v cache v sekundách.

   .. py:method:: get_ident()

      Vrací ident. v aplikaci.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: add_file_reference()

      Provádí operaci add file reference.

      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
      :param timeout: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.

   .. py:method:: file_exists()

      Zjistí, zda je identifikátor mezi referencemi na soubory v session cache.

      :param ident: Identifikátor souboru nebo záznamu k ověření.

   .. py:method:: remove_file_reference()

      Provádí operaci remove file reference.

      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: get_cached_files()

      Vrací cached files.

      :return: Vrací proměnná ``files``.

   .. py:method:: set_project_ownership()

      Uloží vlastnictví projektu pro anonymního uživatele do Redis.
      Používá se pro ověření, že anonymní uživatel může nahrávat soubory pouze k projektu, který sám vytvořil.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``set()``.
      :param timeout: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.

   .. py:method:: verify_project_ownership()

      Ověří, zda anonymní uživatel vlastní daný projekt.

      :param ident_cely: Parametr ``ident_cely`` vstupuje do návratové hodnoty.
      :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


Funkce
------

.. py:function:: file_validate_epsg(epsg)

   Ověří, zda je zadaný EPSG kód podporován (aktuálně pouze WGS-84/4326).

   :param epsg: EPSG kód souřadnicového systému k ověření.
   :return: ``True`` pokud je EPSG=4326, ``False`` jinak.

.. py:function:: balanced_parentheses(expression)

   Ověří, zda má výraz vyrovnané závorky (stejný počet otevíracích a zavíracích).

   :param expression: Řetězec výrazu k ověření.
   :return: ``True`` pokud jsou závorky vyrovnané, ``False`` jinak.

.. py:function:: load_database_translation_strings()

   Načte database translation strings.

   :return: Vrací seznam.

.. py:function:: validate_and_split_geometry(geom)

   Funkce pro validaci řetězce s WKT geometrií.

   :param geom: Parametr ``geom`` předává se do volání ``isinstance()``, ``append()``, pracuje se s atributy ``iloc``, ``copy``, ovlivňuje větvení podmínek.

   :return: Vrací proměnná ``new_rows``.

.. py:function:: get_mime_type(file_name)

   Funkce pro získaní mime typu pro soubor.

   :param file_name: Parametr ``file_name`` se předává do volání ``guess_type()``, pracuje se s atributy ``endswith``, ovlivňuje větvení podmínek.

   :return: Vrací proměnná ``mime_type``.

.. py:function:: get_cadastre_from_point(point)

   Funkce pro získaní katastru z bodu geomu.

   :param point: Parametr ``point`` předává se do volání ``raw()``, ``debug()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``katastr``, None.

.. py:function:: get_cadastre_from_point_with_geometry(point)

   Funkce pro získaní katastru s geometrií z bodu geomu.

   :param point: Parametr ``point`` předává se do volání ``debug()``, ``execute()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: seznam, None.

.. py:function:: get_all_pians_with_akce(ident_cely)

   Funkce pro získaní všech pianů s akci.

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``execute()``.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: update_main_katastr_within_ku(ident_cely, katastr)

   Funkce pro update katastru u akce podle katastrálního území.

   :param ident_cely: Parametr ``ident_cely`` pracuje se s atributy ``split``.
   :param katastr: Parametr ``katastr`` předává se do volání ``execute()``, pracuje se s atributy ``pk``.

.. py:function:: update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)

   Aktualizuje katastry pro všechny akce a lokality související s dokumentační jednotkou.

   :param dj: Dokumentační jednotka obsahující odkaz na akci/lokalitu.
   :param fedora_transaction: Aktivní Fedora transakce pro uložení metadat.

.. py:function:: get_pians_from_akce(katastr, akce_ident_cely)

   Funkce pro bodu, geomu a presnosti z akce.

   :param katastr: Parametr ``katastr`` předává se do volání ``debug()``, ``raw()``, pracuje se s atributy ``pk``.
   :param akce_ident_cely: Identifikátor ``akce_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací proměnná ``pians``.
   :raises CannotFindCadasterCentre: Vyvolá se při zpracování zachycené výjimky typu ``IndexError``.

.. py:function:: get_dj_pians_centroid(ident_cely, lat, lng)

   Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``raw()``, pracuje se s atributy ``rindex``.
   :param lat: Parametr ``lat`` se předává do volání ``raw()``.
   :param lng: Parametr ``lng`` se předává do volání ``raw()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``pians``, None.

.. py:function:: get_num_pians_from_envelope(left, bottom, right, top)

   Funkce pro získaní počtu pianů ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, None.

.. py:function:: get_dj_pians_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``raw()``, ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``raw()``, ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``raw()``, ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``raw()``, ``debug()``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``raw()``.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_project_geom(ident_cely)

   Funkce pro získaní geometrie projekt.

   Bez pristupnosti

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``Q()``, ``debug()``.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_num_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní počtu projektů ze čtverce.

   Bez pristupnosti

   :param left: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   :param right: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   :param top: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   :param stavy: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_num_projects_from_envelope``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``count()``, None.

.. py:function:: get_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní projektů ze čtverce.

   Bez pristupnosti

   :param left: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   :param right: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   :param top: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   :param stavy: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_projects_from_envelope``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.

.. py:function:: get_project_pas_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pas projekt ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``debug()``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``Q()``.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_project_pian_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů projektu ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``debug()``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_3d_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní 3d ze čtverce.
   Bez pristupnosti

   :param left: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   :param right: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   :param top: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_3d_from_envelope``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.

.. py:function:: get_num_pass_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní počtu pas ze čtverce.

   musi zohlednit pristupnost [mapa_pas]

   :param left: Parametr ``left`` se předává do volání ``Q()``, ``from_bbox()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``Q()``, ``from_bbox()``.
   :param right: Parametr ``right`` se předává do volání ``Q()``, ``from_bbox()``.
   :param top: Parametr ``top`` se předává do volání ``Q()``, ``from_bbox()``.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_num_pass_from_envelope``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``count()``, None.

.. py:function:: get_pas_from_envelope(bounds, request)

   Funkce pro získaní pas ze čtverce.

   musi zohlednit pristupnost [mapa_pas]

   :param bounds: Parametr ``bounds`` předává se do volání ``Q()``, ``Polygon()``.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_pas_from_envelope``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``only()``, None.

.. py:function:: get_pian_from_envelope(bounds, zoom, request)

   Funkce pro získaní pianů ze čtverce.

   musi zohlednit pristupnost [mapa_pian]

   :param bounds: Parametr ``bounds`` slouží jako vstup pro logiku funkce ``get_pian_from_envelope``.
   :param zoom: Parametr ``zoom`` ovlivňuje větvení podmínek.
   :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.

   :return: Vrací n-tici.

.. py:function:: get_dj_akce_for_pian(pian_ident_cely, request)

   Funkce pro pro ziskani dj/akce pro pian_ident_cely

   :param pian_ident_cely: Identifikátor ``pian_ident_cely`` používaný pro dohledání cílového záznamu.
   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_dj_akce_for_pian``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values()``, None.

.. py:function:: dictfetchall(cursor)

   Return all rows from a cursor as a dict

   :param cursor: Parametr ``cursor`` pracuje se s atributy ``description``, ``fetchall``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování.

.. py:function:: get_heatmap_pian(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pianů ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   :param zoom: Parametr ``zoom`` ovlivňuje větvení podmínek.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.

.. py:function:: get_heatmap_pas(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pass ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   :param zoom: Parametr ``zoom`` ovlivňuje větvení podmínek.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.

.. py:function:: get_heatmap_project(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy projektů ze čtverce.

   :param left: Parametr ``left`` se předává do volání ``execute()``, ``debug()``.
   :param bottom: Parametr ``bottom`` se předává do volání ``execute()``, ``debug()``.
   :param right: Parametr ``right`` se předává do volání ``execute()``, ``debug()``.
   :param top: Parametr ``top`` se předává do volání ``execute()``, ``debug()``.
   :param zoom: Parametr ``zoom`` ovlivňuje větvení podmínek.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``dictfetchall()``, None.

.. py:function:: get_message(az, message)

   Funkce pro získaní textu správy podle záznamu.

   :param az: Parametr ``az`` se předává do volání ``str()``, ``getattr()``, pracuje se s atributy ``typ_zaznamu``, vstupuje do návratové hodnoty.
   :param message: Parametr ``message`` předává se do volání ``str()``, ``getattr()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``str()``.

.. py:function:: find_pos_with_backup(lang, project_apps, django_apps, third_party_apps)

   scans a couple possible repositories of gettext catalogs for the given

   language code

   :param lang: Textová hodnota `lang` používaná pro vyhledání, pojmenování nebo hlášení stavu.
   :param project_apps: Parametr ``project_apps`` ovlivňuje větvení podmínek.
   :param django_apps: Parametr ``django_apps`` ovlivňuje větvení podmínek.
   :param third_party_apps: Parametr ``third_party_apps`` ovlivňuje větvení podmínek.

   :return: Vrací výsledek volání ``list()``.

.. py:function:: replace_last(source_string, old, new)

   Nahradí poslední výskyt řetězce v textu novým řetězcem.

   :param source_string: Vstupní text.
   :param old: Řetězec k nahrazení.
   :param new: Nový řetězec.
   :return: Text s nahrazeným poslední výskytem.

.. py:function:: get_set_maintenance_in_cache()

   Funkce pro získání nastavení údržby z cache.

   :return: Vrací proměnná ``maintenance``.

.. py:function:: is_maintenance_in_progress()

   Funkce pro zjištění, zda je údržba v průběhu.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: get_timezone()

   Funkce pro získání časového pásma z nastavení.

   :return: Vrací výsledek volání ``timezone()``.
