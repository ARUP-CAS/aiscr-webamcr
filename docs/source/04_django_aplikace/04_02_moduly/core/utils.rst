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

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Popis parametru ``value``.
      :param record: Popis parametru ``record``.

   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů záznamů tabulky.


.. py:class:: SessionIdentifier

   Implementuje komponentu ``SessionIdentifier`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: _generate_session_key()

      Vygeneruje session key.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: clear_cached_files()

      Provádí operaci clear cached files.

   .. py:method:: set_ident()

      Nastaví ident. v aplikaci.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :param timeout: Vstupní hodnota ``timeout`` pro danou operaci.

   .. py:method:: get_ident()

      Vrací ident. v aplikaci.

   .. py:method:: add_file_reference()

      Provádí operaci add file reference.

      :param ident: Vstupní hodnota ``ident`` pro danou operaci.
      :param timeout: Vstupní hodnota ``timeout`` pro danou operaci.

   .. py:method:: file_exists()

      Provádí operaci file exists.

      :param ident: Vstupní hodnota ``ident`` pro danou operaci.

   .. py:method:: remove_file_reference()

      Provádí operaci remove file reference.

      :param ident: Vstupní hodnota ``ident`` pro danou operaci.

   .. py:method:: get_cached_files()

      Vrací cached files.

   .. py:method:: set_project_ownership()

      Nastaví project ownership.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :param timeout: Vstupní hodnota ``timeout`` pro danou operaci.

   .. py:method:: verify_project_ownership()

      Ověří, zda anonymní uživatel vlastní daný projekt.


      **Argumenty:**

      - ``ident_cely``: identifikátor projektu

      **Návratová hodnota:**

      *bool*: True pokud uživatel vlastní projekt, jinak False


Funkce
------

.. py:function:: file_validate_epsg(epsg)

   Provádí operaci file validate epsg.

   :param epsg: Vstupní hodnota ``epsg`` pro danou operaci.

.. py:function:: balanced_parentheses(expression)

   Provádí operaci balanced parentheses.

   :param expression: Vstupní hodnota ``expression`` pro danou operaci.

.. py:function:: load_database_translation_strings()

   Načte database translation strings.

.. py:function:: validate_and_split_geometry(geom)

   Funkce pro validaci řetězce s WKT geometrií.

   :param geom: Popis parametru ``geom``.

.. py:function:: get_mime_type(file_name)

   Funkce pro získaní mime typu pro soubor.

   :param file_name: Popis parametru ``file_name``.

.. py:function:: get_cadastre_from_point(point)

   Funkce pro získaní katastru z bodu geomu.

   :param point: Popis parametru ``point``.

.. py:function:: get_cadastre_from_point_with_geometry(point)

   Funkce pro získaní katastru s geometrií z bodu geomu.

   :param point: Popis parametru ``point``.

.. py:function:: get_all_pians_with_akce(ident_cely)

   Funkce pro získaní všech pianů s akci.

   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: update_main_katastr_within_ku(ident_cely, katastr)

   Funkce pro update katastru u akce podle katastrálního území.

   :param ident_cely: Popis parametru ``ident_cely``.
   :param katastr: Popis parametru ``katastr``.

.. py:function:: update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)

   Funkce pro update katastru u akce a lokalit.

   :param dj: Popis parametru ``dj``.
   :param fedora_transaction: Popis parametru ``fedora_transaction``.

.. py:function:: get_pians_from_akce(katastr, akce_ident_cely)

   Funkce pro bodu, geomu a presnosti z akce.

   :param katastr: Popis parametru ``katastr``.
   :param akce_ident_cely: Popis parametru ``akce_ident_cely``.

.. py:function:: get_dj_pians_centroid(ident_cely, lat, lng)

   Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.

   :param ident_cely: Popis parametru ``ident_cely``.
   :param lat: Popis parametru ``lat``.
   :param lng: Popis parametru ``lng``.

.. py:function:: get_num_pians_from_envelope(left, bottom, right, top)

   Funkce pro získaní počtu pianů ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.

.. py:function:: get_dj_pians_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: get_project_geom(ident_cely)

   Funkce pro získaní geometrie projekt.

   Bez pristupnosti

   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: get_num_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní počtu projektů ze čtverce.

   Bez pristupnosti

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param stavy: Popis parametru ``stavy``.
   :param request: Popis parametru ``request``.

.. py:function:: get_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní projektů ze čtverce.

   Bez pristupnosti

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param stavy: Popis parametru ``stavy``.
   :param request: Popis parametru ``request``.

.. py:function:: get_project_pas_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pas projekt ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: get_project_pian_from_envelope(left, bottom, right, top, ident_cely)

   @janhnat zohlednit pristupnost - zohledneno v ProjectPasFromEnvelopeView

   Funkce pro získaní pianů projektu ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: get_3d_from_envelope(left, bottom, right, top, request)

   @janhnat zohlednit pristupnost - zohledneno v ProjectPianFromEnvelopeView

   Funkce pro získaní 3d ze čtverce.
   Bez pristupnosti

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param request: Popis parametru ``request``.

.. py:function:: get_num_pass_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní počtu pas ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param request: Popis parametru ``request``.

.. py:function:: get_pas_from_envelope(bounds, request)

   Funkce pro získaní pas ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

   :param bounds: Popis parametru ``bounds``.
   :param request: Popis parametru ``request``.

.. py:function:: get_pian_from_envelope(bounds, zoom, request)

   Funkce pro získaní pianů ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pian]

   :param bounds: Popis parametru ``bounds``.
   :param zoom: Popis parametru ``zoom``.
   :param request: Popis parametru ``request``.

.. py:function:: get_dj_akce_for_pian(pian_ident_cely, request)

   Funkce pro pro ziskani dj/akce pro pian_ident_cely

   :param pian_ident_cely: Popis parametru ``pian_ident_cely``.
   :param request: Popis parametru ``request``.

.. py:function:: dictfetchall(cursor)

   Return all rows from a cursor as a dict

   :param cursor: Popis parametru ``cursor``.

.. py:function:: get_heatmap_pian(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pianů ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param zoom: Popis parametru ``zoom``.

.. py:function:: get_heatmap_pas(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pass ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param zoom: Popis parametru ``zoom``.

.. py:function:: get_heatmap_project(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy projektů ze čtverce.

   :param left: Popis parametru ``left``.
   :param bottom: Popis parametru ``bottom``.
   :param right: Popis parametru ``right``.
   :param top: Popis parametru ``top``.
   :param zoom: Popis parametru ``zoom``.

.. py:function:: get_message(az, message)

   Funkce pro získaní textu správy podle záznamu.

   :param az: Popis parametru ``az``.
   :param message: Popis parametru ``message``.

.. py:function:: find_pos_with_backup(lang, project_apps, django_apps, third_party_apps)

   scans a couple possible repositories of gettext catalogs for the given

   language code

   :param lang: Popis parametru ``lang``.
   :param project_apps: Popis parametru ``project_apps``.
   :param django_apps: Popis parametru ``django_apps``.
   :param third_party_apps: Popis parametru ``third_party_apps``.

.. py:function:: replace_last(source_string, old, new)

   Provádí operaci replace last.

   :param source_string: Vstupní hodnota ``source_string`` pro danou operaci.
   :param old: Vstupní hodnota ``old`` pro danou operaci.
   :param new: Vstupní hodnota ``new`` pro danou operaci.

.. py:function:: get_set_maintenance_in_cache()

   Funkce pro získání nastavení údržby z cache.

.. py:function:: is_maintenance_in_progress()

   Funkce pro zjištění, zda je údržba v průběhu.

.. py:function:: get_timezone()

   Funkce pro získání časového pásma z nastavení.
