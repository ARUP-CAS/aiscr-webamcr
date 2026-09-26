HESLAR views
============

Definice views.

Třídy
------

.. py:class:: RuianKatastrAutocomplete

   Třída pohledu pro autocomplete ruian katastru.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: DokumentTypAutocomplete

   Třída pohledu pro autocomplete dokument typu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: DokumentFormatAutocomplete

   Třída pohledu pro autocomplete dokument formatu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: PristupnostAutocomplete

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: HeslarAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: HeslarNazevAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: ContinueKatastrProcessing

   Async processor pro hromadný přepočet katastrů u Projekt/AZ/SN.

   Volá se z admin stránky ``/admin/update-katastry/`` opakovaným polováním
   z JS – každé volání zpracuje další záznam v Redis frontě (klíč
   ``update_katastry_<token>``).

   Vlastní protokol (čtení fronty, posun indexu, progres, ošetření chyb)
   dodává :class:`~fedora_management.views.AdminRecordProcessingView`; tahle
   třída doplňuje jen oprávnění a to, co se s jedním záznamem stane.

   **Metody:**

   .. py:method:: test_func()

      Endpoint smí volat jen superuživatel, stejně jako zakládání úlohy.

      Job vzniká v ``core.admin_sites.update_katastry_file_upload`` pod
      podmínkou ``request.user.is_superuser``; kdyby pokračování stačilo
      běžnému přihlášenému uživateli, dala by se cizí úloha posouvat
      i dokončovat. Zpracování navíc mění data a metadata ve Fedoře.

      :return: ``True``, když je přihlášený uživatel superuživatel.

   .. py:method:: process_record()

      Přepočítá katastr jednoho záznamu a doplní výsledek do odpovědi.

      :param record: Instance Projekt/ArcheologickyZaznam/SamostatnyNalez.
      :param result: Slovník s průběhem, který se vrací do JSON odpovědi.
      :param kwargs: Klíčové argumenty z URL.
      :return: Doplněný slovník ``result``.

   .. py:method:: _process()

      Vyvolá příslušnou ``reassign_*`` funkci podle typu záznamu.

      Záznam se zapíše pouze pokud došlo ke změně oproti původnímu stavu
      (porovnává se ``hlavni_katastr_id`` resp. ``katastr_id``).

      :param record: Instance Projekt/ArcheologickyZaznam/SamostatnyNalez.
      :param reassign_mod: Modul ``heslar.ruian_sync.reassign`` (předáno
          kvůli lazy importu).

      :return: ``True`` pokud reassign vrátil katastr odlišný od původního.


Funkce
------

.. py:function:: merge_heslare(first, second)

   Vytvoří dvoustupňový select z dvou sad hesel.

   :param first: První sada hesel s ID a názvy
   :param second: Druhá sada hesel hierarchicky podřazena první sadě

   :return: Seznam dvojic (název, možnosti) pro dvoustupňový select

.. py:function:: heslar_12(druha, prvni_kat, id)

   Funkce pro vytvoření dvoustupňového selectu.

   :param druha: Parametr ``druha`` se předává do volání ``filter()``, ``merge_heslare()``, vstupuje do návratové hodnoty.
   :param prvni_kat: Parametr ``prvni_kat`` se předává do volání ``filter()``.
   :param id: Identifikátor ``id`` používaný pro dohledání cílového záznamu.

   :return: Vrací výsledek volání ``merge_heslare()``.

.. py:function:: _souradnice_ze_starych_parametru(request)

   Převede zastaralé parametry ``long``/``lat`` (EPSG:4326) na JTSK.

   Endpoint dřív bral WGS84; kontrakt se změnil naráz, takže prohlížeč
   s cachovaným starším skriptem posílá stále původní jména. Bez tohohle
   přemostění by dostal prázdnou odpověď a uživatel by jen viděl, že se
   katastr „nedoplnil“.

   :param request: HTTP GET požadavek.
   :return: Dvojice ``(x, y)`` v EPSG:5514, nebo ``None`` když staré
       parametry chybí nebo je nejde převést.

.. py:function:: zjisti_katastr_souradnic(request)

   Vrátí katastr obsahující zadaný bod v EPSG:5514 (S-JTSK).

   Volá se AJAX z ``mapa_projekty.js`` po kliknutí do Leaflet mapy (mapa
   je v JTSK CRS ``mapa_settings_jtsk.js``). Vstupem jsou GET parametry
   ``x`` a ``y`` v EPSG:5514 v konvenci projektu (záporné hodnoty).

   Přechodně se přijímají i původní parametry ``long``/``lat``. Kontrakt se
   měnil z WGS84 na JTSK v jednom kroku, takže prohlížeč s cachovaným starším
   ``mapa_projekty.js`` posílá pořád stará jména – dostal by prázdný objekt
   a políčko katastru by zůstalo nevyplněné bez jakékoli hlášky. Souřadnice
   se v takovém případě převedou přes ``core.coordTransform``; až cache
   doběhne, dá se větev odstranit.

   :param request: GET s parametry ``x`` a ``y`` v EPSG:5514, nebo přechodně
       ``long`` a ``lat`` v EPSG:4326.

   :return: JsonResponse s ``id`` a ``value`` katastru, nebo prázdný.

.. py:function:: zjisti_vychozi_hodnotu(request)

   Funkce pohledu pro zjištení výchozí hodnoty z heslaře.

   :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: zjisti_nadrazenou_hodnotu(request)

   Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

   :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: heslar_list(heslo_nazev, filter, use_exclude)

   Vrací seznam hesel z heslaře filtrovaných podle kritérií.

   :param heslo_nazev: Název heslaře, ze kterého se načítají hesla
   :param filter: Slovník kritérií pro filtrování záznamů
   :param use_exclude: Má-li být použita metoda exclude namíste filter

   :return: Seznam dvojic (ID, název hesla) ve zvolném jazyce
