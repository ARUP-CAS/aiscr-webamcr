CORE utils
==========

Modul utils.

Třídy
------

.. py:class:: CannotFindCadasterCentre

   Popis není k dispozici.


.. py:class:: SearchTable

   Základní setup pro tabulky používané v aplikaci.
Obsahuje metodu na získaní sloupců které mají byt zobrazeny.

   **Metody:**

   .. py:method:: get_column_default_show()

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů záznamů tabulky.


.. py:class:: SessionIdentifier

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clear_cached_files()

   .. py:method:: set_ident()

   .. py:method:: get_ident()

   .. py:method:: add_file_reference()

   .. py:method:: file_exists()

   .. py:method:: remove_file_reference()

   .. py:method:: get_cached_files()

   .. py:method:: set_project_ownership()

      Uloží vlastnictví projektu pro anonymního uživatele do Redis.
      Používá se pro ověření, že anonymní uživatel může nahrávat soubory pouze k projektu, který sám vytvořil.
      
      Args:
          ident_cely: identifikátor projektu
          timeout: timeout v sekundách (defaultně 2 hodiny)

   .. py:method:: verify_project_ownership()

      Ověří, zda anonymní uživatel vlastní daný projekt.
      
      Args:
          ident_cely: identifikátor projektu
      
      Returns:
          bool: True pokud uživatel vlastní projekt, jinak False


Funkce
------

.. py:function:: file_validate_epsg(epsg)

   Popis není k dispozici.

.. py:function:: balanced_parentheses(expression)

   Popis není k dispozici.

.. py:function:: load_database_translation_strings()

   Popis není k dispozici.

.. py:function:: validate_and_split_geometry(geom)

   Funkce pro validaci řetězce s WKT geometrií.

.. py:function:: get_mime_type(file_name)

   Funkce pro získaní mime typu pro soubor.

.. py:function:: get_cadastre_from_point(point)

   Funkce pro získaní katastru z bodu geomu.

.. py:function:: get_cadastre_from_point_with_geometry(point)

   Funkce pro získaní katastru s geometrií z bodu geomu.

.. py:function:: get_all_pians_with_akce(ident_cely)

   Funkce pro získaní všech pianů s akci.

.. py:function:: update_main_katastr_within_ku(ident_cely, katastr)

   Funkce pro update katastru u akce podle katastrálního území.

.. py:function:: update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)

   Funkce pro update katastru u akce a lokalit.

.. py:function:: get_pians_from_akce(katastr, akce_ident_cely)

   Funkce pro bodu, geomu a presnosti z akce.

.. py:function:: get_dj_pians_centroid(ident_cely, lat, lng)

   Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.

.. py:function:: get_num_pians_from_envelope(left, bottom, right, top)

   Funkce pro získaní počtu pianů ze čtverce.

.. py:function:: get_dj_pians_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů ze čtverce.

.. py:function:: get_project_geom(ident_cely)

   Funkce pro získaní geometrie projekt.
   Bez pristupnosti

.. py:function:: get_num_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní počtu projektů ze čtverce.
   Bez pristupnosti

.. py:function:: get_projects_from_envelope(left, bottom, right, top, stavy, request)

   Funkce pro získaní projektů ze čtverce.
   Bez pristupnosti

.. py:function:: get_project_pas_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pas projekt ze čtverce.
   @janhnat zohlednit pristupnost - zohledneno v ProjectPasFromEnvelopeView

.. py:function:: get_project_pian_from_envelope(left, bottom, right, top, ident_cely)

   Funkce pro získaní pianů projektu ze čtverce.
   @janhnat zohlednit pristupnost - zohledneno v ProjectPianFromEnvelopeView

.. py:function:: get_3d_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní 3d ze čtverce.
   Bez pristupnosti

.. py:function:: get_num_pass_from_envelope(left, bottom, right, top, request)

   Funkce pro získaní počtu pas ze čtverce.
   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

.. py:function:: get_pas_from_envelope(bounds, request)

   Funkce pro získaní pas ze čtverce.
   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pas]

.. py:function:: get_pian_from_envelope(bounds, zoom, request)

   Funkce pro získaní pianů ze čtverce.
   @janhnat zohlednit pristupnost - done
   musi zohlednit pristupnost [mapa_pian]

.. py:function:: get_dj_akce_for_pian(pian_ident_cely, request)

   Funkce pro pro ziskani dj/akce pro pian_ident_cely

.. py:function:: dictfetchall(cursor)

   Return all rows from a cursor as a dict

.. py:function:: get_heatmap_pian(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pianů ze čtverce.

.. py:function:: get_heatmap_pas(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy pass ze čtverce.

.. py:function:: get_heatmap_project(left, bottom, right, top, zoom)

   Funkce pro získaní heat mapy projektů ze čtverce.

.. py:function:: get_validation_messages(text)

   Funkce pro získaní textu validační chyby.

.. py:function:: get_message(az, message)

   Funkce pro získaní textu správy podle záznamu.

.. py:function:: find_pos_with_backup(lang, project_apps, django_apps, third_party_apps)

   scans a couple possible repositories of gettext catalogs for the given
   language code

.. py:function:: replace_last(source_string, old, new)

   Popis není k dispozici.

.. py:function:: get_set_maintenance_in_cache()

   Funkce pro získání nastavení údržby z cache.

.. py:function:: is_maintenance_in_progress()

   Funkce pro zjištění, zda je údržba v průběhu.

.. py:function:: get_timezone()

   Funkce pro získání časového pásma z nastavení.
