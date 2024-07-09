Použité knihovny a licence
==========================

Knihovny jsou do aplikace instalovány s využitím systému `pip` a jako statické soubory s využitím tagu `<script>`.

Níže je přehled licencí, které knihovny v aplikaci používají.

**MIT Licence** je velmi liberální licence, která umožňuje širokou škálu použití. Umožňuje uživatelům používat, kopírovat,
upravovat, spojovat, publikovat, distribuovat, sublicencovat a/nebo prodávat kopie softwaru a dovoluje uživatelům
držet u sebe zdrojový kód, pokud v souborech softwaru zachovají původní oznámení o autorských právech a licenci.

**GNU General Public License (GPL)** je *copyleft licence*, která vyžaduje, aby modifikované verze open source
software byly distribuovány pod stejnou licencí. To znamená, že každý software, který je odvozen od kódu pod GPL,
musí být také uvolněn pod GPL, pokud je distribuován. GPL zajišťuje, že software a jeho odvozené práce zůstanou
volně dostupné a chrání autorská práva autorů.

**BSD Licence** je sada *permissive* licencí, které jsou méně restriktivní než GPL. Povolují distribuci zdrojového
i binárního kódu s málo omezeními, což znamená, že software může být použit, modifikován a distribuován pro soukromé
i komerční účely. BSD licence obvykle vyžadují pouze zachování oznámení o autorských právech a seznamů podmínek
v redistribuovaných kódech.

**Apache Software License** je *permissive* licence podobná MIT a BSD licencím, ale obsahuje klauzuli o ochraně
proti zneužití jména. To znamená, že uživatelé mohou kopírovat, modifikovat a distribuovat software,
ale nesmí používat jméno projektu nebo jeho přispěvatelů k propagaci odvozených produktů bez předchozího písemného
souhlasu. Licence také explicitně deklaruje, že software je poskytován "tak, jak je", což chrání vývojáře
před právními nároky.

**Mozilla Public License 2.0** je *copyleft* licence, která umožňuje kombinaci MPL kódu s ne-MPL kódem v jednom
projektu. Na rozdíl od GPL, MPL nevyžaduje, aby celý software byl distribuován pod MPL, pokud používá MPL kód.
To umožňuje větší flexibilitu při integraci do různých projektů. Licence chrání vývojáře a zajišťuje, že kód
zůstane otevřený a přístupný pro komunitu.

Knihovny instalované pomocí pip
-------------------------------

Tabulka obsahuje přehled knihoven použitých v projektu, které byly nainstalovány prostřednictvím systému `pip`,
a jejich příslušné licence. Každý řádek v souboru představuje jednu knihovnu a obsahuje následující informace:

1. **Název knihovny**: Toto pole obsahuje oficiální název knihovny nebo softwarového balíčku použitého v projektu.
2. **Verze**: Verze knihovny, která je v projektu použita. Verze je důležitá pro určení kompatibility a zabezpečení knihovny.
3. **Licence**: Typ licence, pod kterou je knihovna distribuována. Licence může určovat, jak může být knihovna použita, modifikována a distribuována. Některé běžné typy licencí zahrnují MIT, GPL, Apache License atd.
4. **Odkaz**: Odkaz na domovskou stránku knihovny

Tento soubor je důležitý pro porozumění právním aspektům použitých knihoven a pro zajištění, že projekt dodržuje licenční požadavky všech použitých závislostí. Je důležité pravidelně aktualizovat tento soubor, aby odrážel jakékoli změny v použitých knihovnách nebo jejich licencích.

.. list-table:: Knihovny instalované s využitím `pip`
   :widths: 25 25 25 25
   :header-rows: 1

@licence_table

Knihovny vkládané jako statické soubory
---------------------------------------

.. list-table:: Knihovny v jazyce Javascript
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Odkaz
   * - Bootstrap
     - 4.5.3
     - MIT License
     - https://getbootstrap.com/
   * - Bootstrap Icons
     - 1.5.0
     - MIT License
     - https://icons.getbootstrap.com/
   * - Bootstrap Select
     - 1.13.14
     - MIT License
     - https://developer.snapappointments.com/bootstrap-select/
   * - Bootstrap Datepicker
     - 1.9.0
     - Apache License
     - https://bootstrap-datepicker.readthedocs.io/en/latest/
   * - Django Autocomplete Light
     -
     - MIT License
     - https://github.com/yourlabs/django-autocomplete-light
   * - Dropzone
     -
     - MIT License
     - https://www.dropzone.dev/
   * - Easytimer
     -
     - MIT License
     - https://albert-gonzalez.github.io/easytimer.js/
   * - Google Tag Manager
     -
     -
     - https://tagmanager.google.com/#/home
   * - Heatmap.js
     - 2.0.5
     - MIT License
     - https://www.patrick-wied.at/static/heatmapjs/
   * - jQuery
     - 3.5.1
     - MIT License
     - https://jquery.com/
   * - Leaflet
     - 1.9.4
     - BSD License
     - https://leafletjs.com/
   * - Leaflet Context Menu
     - 1.5.1
     - MIT License
     - https://github.com/aratcliffe/Leaflet.contextmenu
   * - Leaflet Control Search
     -
     - MIT License
     - https://github.com/stefanocudini/leaflet-search
   * - Leaflet Coordinates
     -
     - Creative Commons Attribution 3.0 Unported License.
     - https://github.com/MrMufflon/Leaflet.Coordinates/tree/master
   * - Leaflet Draw
     - 1.0.4
     - MIT License
     - https://github.com/Leaflet/Leaflet.draw
   * - Leaflet Easy Button
     - v1
     - MIT License
     - https://danielmontague.com/projects/easyButton.js/v1/examples/
   * - Leaflet FeatureGroup SubGroup
     -
     - BSD License
     - https://github.com/ghybs/Leaflet.FeatureGroup.SubGroup/tree/master
   * - Leaflet Fullscreen
     - 1.0.1
     - ISC License
     - https://github.com/Leaflet/Leaflet.fullscreen
   * - Leaflet Heatmap Overlay
     -
     - MIT License
     - https://www.patrick-wied.at/static/heatmapjs/plugin-leaflet-layer.html
   * - Leaflet Marker Cluster
     - 1.5.3
     - MIT License
     - https://github.com/Leaflet/Leaflet.markercluster
   * - Leaflet Measure
     -
     - MIT License
     - https://github.com/ljagis/leaflet-measure
   * - Leaflet Spin
     -
     - MIT License
     - https://github.com/makinacorpus/Leaflet.Spin
   * - Leaflet TileLayer Grayscale
     -
     - WTFPL license
     - https://github.com/Zverik/leaflet-grayscale
   * - Leaflet Messagebox
     - 1.1
     - BSD License
     - https://github.com/tinuzz/leaflet-messagebox
   * - LercDecode
     - 1.0.1
     - Apache Software License
     - https://unpkg.com/browse/lerc@1.0.1/
   * - Select2
     - 4.0.13
     - MIT License
     - https://github.com/select2/select2/tree/master

