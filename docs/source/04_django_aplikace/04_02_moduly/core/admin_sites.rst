CORE admin_sites
================

Modul admin_sites.

Třídy
------

.. py:class:: AmcrCustomAdminSite

   Vlastní admin site AMČR s reorganizovanou strukturou menu a správou dat.

   **Metody:**

   .. py:method:: get_app_list()

      Reorganizuje seznam aplikací v admin rozhraní do požadované struktury menu.

      :param request: HTTP požadavek.
      :param app_label: Volitelný label aplikace pro filtrování.
      :return: Vrací reorganizovaný seznam aplikací.

   .. py:method:: _read_file()

      Načte CSV/XLSX soubor se seznamem identifikátorů a převede jej na DataFrame.

      :param uploaded_file: Nahraný soubor z formuláře; podle ``content_type`` se načte jako CSV nebo Excel.
      :param context: Slovník kontextu pro šablonu; při chybě čtení nebo neplatném formátu se do něj uloží klíč ``error``.
      :return: DataFrame s jedním sloupcem ``ident_cely`` indexovaným touto hodnotou, nebo ``None`` při chybě.

   .. py:method:: update_doi()

      Zpracuje hromadnou aktualizaci DOI/IGSN podle nahraného seznamu identifikátorů.

      :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
      :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.

   .. py:method:: update_metadata_file_upload()

      Zpracuje hromadnou aktualizaci metadat ve Fedora repozitáři.

      :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
      :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.

   .. py:method:: _import_performed_action_labels()

      Vrátí mapu kódů akcí importu na jejich lidsky čitelné popisky.

      :return: Slovník ``{kód akce: přeložený popisek}`` pro zobrazení ve stavu importu.

   .. py:method:: _import_directory_configured()

      Zjistí, zda je nakonfigurovaný a dostupný adresář pro import binárních souborů.

      :return: ``True``, pokud je ``DIRECTORY_PATH`` nastavený a ukazuje na existující adresář.

   .. py:method:: _render_import_polling_ui()

      Vykreslí polling UI navázané na běžící nebo terminální importní úlohu ``job_id``.

      Do kontextu vkládá pouze ne-datové položky (URL, popisek akce, konfigurace adresáře);
      veškerá importní a validační data si stránka tahá z progress endpointu (požadavek 3, §4.1).

      :param request: HTTP požadavek.
      :param context: Základní kontext šablony (``app_list``, ``maintenance`` …).
      :param job_id: Identifikátor importní úlohy, na kterou se stránka naváže.
      :return: ``TemplateResponse`` s polling UI bez validačních dat v kontextu.

   .. py:method:: import_data()

      Přijme nahraný ZIP hromadného importu a zařadí jeho validaci do fronty (accept-and-enqueue).

      Validace ani import už neběží v HTTP požadavku (viz #391): POST komprimovaný ZIP nastageuje
      do Redis po chuncích, získá globální importní lock, nastaví fázi ``validating`` a dispatchne
      ``cron.tasks.run_data_import_validation``. Stránka pak jen pollује progress endpoint —
      žádná importní ani validační data se nevykreslují z kontextu POSTu (požadavek 3).

      Znovuotevření stránky (GET) se naváže na běžící úlohu daného uživatele přes
      ``import_data_current_job_{user_id}`` (požadavek 2).

      Paměťová charakteristika (§8): ``data_file.read()`` načte celý komprimovaný upload
      (~200-330 MB pro max. úlohu) najednou do RAM web workeru a slicing chunků drží druhou
      referenci — přechodný špičkový nárůst ~250-500 MB na jeden upload. Globální lock serializuje
      uploady, takže špičkuje jen jeden uWSGI worker; buffery se uvolní návratem požadavku.

      :param request: HTTP požadavek; při ``POST`` od superuživatele zvaliduje formulář a zařadí
          validaci do fronty.
      :return: ``TemplateResponse`` s polling UI, upload formulářem nebo chybovou hláškou.
      :raises PermissionDenied: Pokud přihlášený uživatel není superuživatel.

   .. py:method:: get_urls()

      Vrátí vlastní URL cesty admin site pro hromadné operace.

      :return: Seznam URL vzorů rozšířený o cesty pro aktualizaci metadat,
          aktualizaci DOI/IGSN a hromadný import dat.

