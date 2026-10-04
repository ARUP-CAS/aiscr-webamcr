JavaScript knihovny
===================

.. BEGIN GENERATED NODEJS LIBRARIES

Knihovny instalované pomocí Node.js
------------------------------------

.. list-table:: Knihovny v jazyce Javascript instalované pomocí Node.js
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Odkaz
   * - bootstrap
     - 5.3.8
     - MIT
     - https://getbootstrap.com/
   * - bootstrap-datepicker
     - 1.10.1
     - Apache-2.0
     - https://github.com/uxsolutions/bootstrap-datepicker
   * - bootstrap-icons
     - 1.13.1
     - MIT
     - https://icons.getbootstrap.com/
   * - bootstrap-select
     - 1.14.0-beta3
     - MIT
     - https://developer.snapappointments.com/bootstrap-select
   * - bs-stepper
     - 1.7.0
     - MIT
     - https://github.com/Johann-S/bs-stepper
   * - daterangepicker
     - 3.1.0
     - MIT
     - https://github.com/dangrossman/daterangepicker
   * - dropzone
     - 6.3.4
     - MIT
     - http://www.dropzonejs.com
   * - jquery
     - 4.0.0
     - 
     - https://jquery.com
   * - jquery-migrate
     - 4.0.2
     - 
     - https://github.com/jquery/jquery-migrate
   * - leaflet
     - 1.9.4
     - BSD-2-Clause
     - https://leafletjs.com/
   * - leaflet-draw
     - 1.0.4
     - MIT
     - https://github.com/Leaflet/Leaflet.draw
   * - leaflet-easybutton
     - 2.4.0
     - MIT
     - https://github.com/CliffCloud/Leaflet.EasyButton
   * - leaflet-fullscreen
     - 1.0.2
     - ISC
     - https://github.com/Leaflet/Leaflet.fullscreen
   * - leaflet-spin
     - 1.1.2
     - MIT
     - http://makinacorpus.github.io/Leaflet.Spin/
   * - leaflet.featuregroup.subgroup
     - 1.0.2
     - BSD-2-Clause
     - https://github.com/ghybs/Leaflet.FeatureGroup.SubGroup#readme
   * - leaflet.markercluster
     - 1.5.3
     - MIT
     - https://github.com/Leaflet/Leaflet.markercluster
   * - moment
     - 2.31.0
     - MIT
     - https://momentjs.com
   * - spin.js
     - 2.3.2
     - BSD-2-Clause
     - https://github.com/fgnass/spin.js
   * - vanilla-cookieconsent
     - 3.0.0
     - MIT
     - https://cookieconsent.orestbida.com

.. END GENERATED NODEJS LIBRARIES

.. BEGIN GENERATED STATIC LIBRARIES

Knihovny vkládané jako statické soubory
----------------------------------------

Generováno z ``webclient/static_vendor.json``; soulad s obsahem ``webclient/static/``
hlídá ``scripts/check_static_vendor_manifest.py``.

.. list-table:: Knihovny v jazyce Javascript vkládané jako statické soubory
   :widths: 20 12 13 35 20
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Úpravy
     - Odkaz
   * - Bootstrap-datepicker – česká lokalizace
     - 1.10.1
     - Apache-2.0
     - Upraveno. Formát data změněn na d.m.yyyy.
     - https://github.com/uxsolutions/bootstrap-datepicker/blob/v1.10.1/js/locales/bootstrap-datepicker.cs.js
   * - Bootstrap-select – lokalizace cs/en
     - 1.13.17
     - MIT
     - Upraveno. Výchozí nastavení AMČR (actionsBox, oddělovač u en); jádro knihovny je z npm.
     - https://github.com/snapappointments/bootstrap-select/tree/v1.13.17/js/i18n
   * - Django admin – DateTimeShortcuts
     - 5.1.1
     - BSD-3-Clause
     - Upraveno. Přepisuje soubor Django adminu (cesta je závazná); tlačítko Dnes používá první formát z DATE_INPUT_FORMATS.
     - https://github.com/django/django/blob/5.1.1/django/contrib/admin/static/admin/js/admin/DateTimeShortcuts.js
   * - Easytimer.js
     - 4.5.1
     - MIT
     - Upraveno. Zdrojový ES soubor bez importů (TimeCounter a EventEmitter vloženy), verze odvozena z data vložení.
     - https://github.com/albert-gonzalez/easytimer.js
   * - Heatmap.js a Leaflet Heatmap Overlay
     - 2.0.5
     - MIT
     - Upraveno. Canvas s willReadFrequently, omezení poloměru na 5000, rozšířené hranice mapy (pad(1)).
     - https://github.com/pa7/heatmap.js
   * - html-to-rtf-browser
     - 1.6.1
     - MIT
     - Upraveno. Browserify bundle; závislosti odpovídají cheerio 1.0.0-rc.12, parse5 7.2.1, juice 7.0.0 (ověřeno rekonstrukcí buildu). Úpravy AMČR jen v app/src (allowed-html-tags, html-tags.module, color, charset, rtf.class): mapování tříd výpisu na RTF, ignorované třídy, absolutní odkazy, barva odkazů, obrázky nahrazeny textem „Stáhnout soubor“ (cs/en). Náhrada řeší #3648.
     - https://github.com/antoniolucasnobar/html-to-rtf-browser
   * - Leaflet Context Menu
     - 1.5.1
     - MIT
     - Na npm je nejnovější 1.4.0.
     - https://github.com/aratcliffe/Leaflet.contextmenu/tree/v1.5.1
   * - Leaflet Control Search
     - 3.0.2
     - MIT
     - Upraveno. Vyhledávání přes služby ČÚZK (RÚIAN); verze odvozena porovnáním s npm.
     - https://github.com/stefanocudini/leaflet-search
   * - Leaflet Coordinates
     - 0.1.5
     - CC-BY-3.0
     - Upraveno. Doplněno zobrazení souřadnic S-JTSK.
     - https://github.com/MrMufflon/Leaflet.Coordinates
   * - Leaflet Measure
     - c31cafb
     - neuvedena
     - Upraveno. Upstream nemá vydání ani licenci; upravené volby (title, keyboard) a doplněná událost measure:start.
     - https://github.com/aprilandjan/leaflet.measure
   * - Leaflet Messagebox
     - 1.1
     - BSD-3-Clause
     - Upraveno. Doplněna metoda hide() a parametr timeout v show().
     - https://github.com/tinuzz/leaflet-messagebox
   * - Leaflet TileLayer Grayscale
     - 97d1417
     - WTFPL
     - Upstream nemá vydání; verze je commit v master.
     - https://github.com/Zverik/leaflet-grayscale

.. END GENERATED STATIC LIBRARIES

Pravidla pro knihovny třetích stran
-----------------------------------

- Knihovna dostupná na npm v použitelné podobě patří do ``package.json`` (verze přesně,
  aktualizace hlídá Dependabot). Soubory se načítají přes ``{% static '<balíček>/<cesta>' %}``.
- Knihovna, kterou nelze vzít z npm (neexistuje, nebo obsahuje úpravy AMČR), patří do
  ``webclient/static/vendor/<knihovna>/`` a musí mít záznam ve ``webclient/static_vendor.json``
  (verze, licence, zdroj, informace o úpravách). Jinde ve ``static/`` jsou povolené jen
  záznamy uvedené v manifestu (přepis souboru Django adminu, ``html-to-rtf-browser`` – #3648).
- Stejná knihovna nesmí být zároveň v ``package.json`` i vendorovaná.

Knihovny z jiných zdrojů
------------------------

- **Django Autocomplete Light** a **Select2** – statické soubory dodává Python balíček
  ``django-autocomplete-light`` a Django admin (``admin/js/vendor/select2``), verze určuje
  ``webclient/requirements.txt``.
- **Google Tag Manager** (gtag.js) – vzdálený skript třetí strany načítaný z
  ``googletagmanager.com`` podle souhlasu s cookies; nemá verzi.
