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

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.

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
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: clear_cached_files()

      Provádí operaci clear cached files.

   .. py:method:: set_ident()

      Nastaví ident. v aplikaci.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :param timeout: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.

   .. py:method:: get_ident()

      Vrací ident. v aplikaci.

   .. py:method:: add_file_reference()

      Provádí operaci add file reference.

      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
      :param timeout: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.

   .. py:method:: file_exists()

      Provádí operaci file exists.

      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: remove_file_reference()

      Provádí operaci remove file reference.

      :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: get_cached_files()

      Vrací cached files.

   .. py:method:: set_project_ownership()

      Nastaví project ownership.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :param timeout: Časový údaj ``timeout`` použitý při filtrování nebo výpočtu.

   .. py:method:: verify_project_ownership()

      Ověří, zda anonymní uživatel vlastní daný projekt.

      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
      :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.


Funkce
------

.. py:function:: file_validate_epsg(epsg)

   Provádí operaci file validate epsg.

   :param epsg: Číselná nebo geometrická hodnota `epsg` použitá při výpočtu nebo transformaci.

.. py:function:: balanced_parentheses(expression)

   Provádí operaci balanced parentheses.

   :param expression: Číselná hodnota ``expression`` použitá při výpočtu nebo transformaci.

.. py:function:: load_database_translation_strings()

   Načte database translation strings.

.. py:function:: validate_and_split_geometry(geom)

   Funkce pro validaci řetězce s WKT geometrií.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.

.. py:function:: get_mime_type(file_name)

   Funkce pro získaní mime typu pro soubor.

   :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.

.. py:function:: get_cadastre_from_point(point)

   Funkce pro získaní katastru z bodu geomu.

   :param point: Doménový objekt `point`, se kterým funkce pracuje.

.. py:function:: get_cadastre_from_point_with_geometry(point)

   Funkce pro získaní katastru s geometrií z bodu geomu.

   :param point: Doménový objekt `point`, se kterým funkce pracuje.

.. py:function:: get_all_pians_with_akce(ident_cely)

   Funkce pro získaní všech pianů s akci.

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: update_main_katastr_within_ku(ident_cely, katastr)

   Funkce pro update katastru u akce podle katastrálního území.

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :param katastr: Doménový objekt `katastr`, se kterým funkce pracuje.

.. py:function:: update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)

   Funkce pro update katastru u akce a lokalit.

   :param dj: Doménový objekt `dj`, se kterým funkce pracuje.
   :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.

.. py:function:: get_pians_from_akce(katastr, akce_ident_cely)

   Funkce pro bodu, geomu a presnosti z akce.

   :param katastr: Doménový objekt `katastr`, se kterým funkce pracuje.
   :param akce_ident_cely: Identifikátor ``akce_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_dj_pians_centroid(ident_cely, lat, lng)

   Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :param lat: Číselná nebo geometrická hodnota `lat` použitá při výpočtu nebo transformaci.
   :param lng: Číselná nebo geometrická hodnota `lng` použitá při výpočtu nebo transformaci.

.. py:function:: get_num_pians_from_envelope(left, bottom, right, top)

   Funkce pro získaní počtu pianů ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.

.. py:function:: get_dj_pians_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_project_geom(ident_cely)

   Funkce pro získaní geometrie projekt.

   Bez pristupnosti

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_num_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní počtu projektů ze čtverce.

   Bez pristupnosti

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param stavy: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní projektů ze čtverce.

   Bez pristupnosti

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param stavy: Číselná hodnota ``stavy`` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_project_pas_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pas projekt ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_project_pian_from_envelope(left, bottom, right, top, ident_cely)

   @janhnat zohlednit pristupnost - zohledneno v ProjectPasFromEnvelopeView

   Funkce pro získaní pianů projektu ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :return: ``True``, pokud anonymní session vlastní projekt se zadaným identifikátorem.

.. py:function:: get_3d_from_envelope(left, bottom, right, top, request)

   @janhnat zohlednit pristupnost - zohledneno v ProjectPianFromEnvelopeView

   Funkce pro získaní 3d ze čtverce.
   Bez pristupnosti

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_num_pass_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní počtu pas ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_pas_from_envelope(bounds, request)

   Funkce pro získaní pas ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

   :param bounds: Doménový objekt `bounds`, se kterým funkce pracuje.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_pian_from_envelope(bounds, zoom, request)

   Funkce pro získaní pianů ze čtverce.

   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pian]

   :param bounds: Doménový objekt `bounds`, se kterým funkce pracuje.
   :param zoom: Číselná nebo geometrická hodnota `zoom` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_dj_akce_for_pian(pian_ident_cely, request)

   Funkce pro pro ziskani dj/akce pro pian_ident_cely

   :param pian_ident_cely: Identifikátor ``pian_ident_cely`` používaný pro dohledání cílového záznamu.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: dictfetchall(cursor)

   Return all rows from a cursor as a dict

   :param cursor: Číselná nebo geometrická hodnota `cursor` použitá při výpočtu nebo transformaci.

.. py:function:: get_heatmap_pian(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pianů ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param zoom: Číselná nebo geometrická hodnota `zoom` použitá při výpočtu nebo transformaci.

.. py:function:: get_heatmap_pas(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pass ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param zoom: Číselná nebo geometrická hodnota `zoom` použitá při výpočtu nebo transformaci.

.. py:function:: get_heatmap_project(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy projektů ze čtverce.

   :param left: Číselná nebo geometrická hodnota `left` použitá při výpočtu nebo transformaci.
   :param bottom: Číselná nebo geometrická hodnota `bottom` použitá při výpočtu nebo transformaci.
   :param right: Číselná nebo geometrická hodnota `right` použitá při výpočtu nebo transformaci.
   :param top: Číselná nebo geometrická hodnota `top` použitá při výpočtu nebo transformaci.
   :param zoom: Číselná nebo geometrická hodnota `zoom` použitá při výpočtu nebo transformaci.

.. py:function:: get_message(az, message)

   Funkce pro získaní textu správy podle záznamu.

   :param az: Číselná nebo geometrická hodnota `az` použitá při výpočtu nebo transformaci.
   :param message: Textová zpráva ``message`` používaná pro hlášení stavu nebo chyby.

.. py:function:: find_pos_with_backup(lang, project_apps, django_apps, third_party_apps)

   scans a couple possible repositories of gettext catalogs for the given

   language code

   :param lang: Textová hodnota `lang` používaná pro vyhledání, pojmenování nebo hlášení stavu.
   :param project_apps: Název nebo typ ``project_apps`` používaný pro volbu cílové logiky.
   :param django_apps: Název nebo typ ``django_apps`` používaný pro volbu cílové logiky.
   :param third_party_apps: Název nebo typ ``third_party_apps`` používaný pro volbu cílové logiky.

.. py:function:: replace_last(source_string, old, new)

   Provádí operaci replace last.

   :param source_string: Textový nebo strukturální vstup `source_string` používaný při sestavení nebo zpracování obsahu.
   :param old: Číselná nebo geometrická hodnota `old` použitá při výpočtu nebo transformaci.
   :param new: Nová hodnota porovnávaná nebo nastavovaná oproti původnímu stavu.

.. py:function:: get_set_maintenance_in_cache()

   Funkce pro získání nastavení údržby z cache.

.. py:function:: is_maintenance_in_progress()

   Funkce pro zjištění, zda je údržba v průběhu.

.. py:function:: get_timezone()

   Funkce pro získání časového pásma z nastavení.
