Tmavý režim (Dark Theme)
========================

Přehled
-------

Aplikace AMČR podporuje přepínání mezi světlým a tmavým režimem.
Tmavý režim je implementován výhradně na straně klienta pomocí CSS
proměnných, SCSS přepisů a JavaScriptové třídy ``ThemeManager``.
Žádná serverová logika není zapojena.

Mechanismus aktivace
--------------------

Téma je řízeno dvěma DOM atributy nastavenými současně:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Selektor
     - Účel
   * - ``html[data-theme="dark"]``
     - Primární SCSS selektor pro všechny tmavé přepisy
   * - ``body.app-dark-theme``
     - Alternativní třída na ``<body>`` (pro page-specific scoping)

Přepínání zajišťuje třída **ThemeManager** v ``webclient/static/js/theme-toggle.js``:

1. Při načtení stránky čte ``localStorage('app-theme')``; pokud není nastaveno,
   použije preferenci operačního systému (``prefers-color-scheme: dark``).
2. Nastaví ``data-theme`` na ``<html>`` a přepne třídy
   ``app-dark-theme`` / ``app-light-theme`` na ``<body>``.
3. Sleduje změny ``prefers-color-scheme`` a automaticky přepíná,
   **pokud** uživatel ručně nezvolil téma.
4. Dispatchuje ``CustomEvent`` ``theme-changed``, na který reagují
   další komponenty (např. ikona tlačítka).

Tlačítko přepínání používá Material Icons ikonu (``dark_mode`` / ``light_mode``)
a nachází se v:

- **Přihlášené rozložení:** ``webclient/templates/base_logged_in.html``
  (navbar, ``#theme-toggle-btn``)
- **Přihlašovací / registrační stránky:** ``webclient/templates/registration/login.html``,
  ``password_reset_*.html``, ``django_registration/*.html``
- **Oznámení (veřejné stránky):** ``webclient/oznameni/templates/oznameni/header.html``,
  ``index.html``, ``index_2.html``, ``success.html``
- **Chybové stránky proxy (statické HTML):** ``proxy/custom_html/{cs,en}/*.html``
  — obsahují inline JS, který čte ``localStorage('app-theme')`` a nastaví
  ``data-theme`` přímo.

Struktura souborů
-----------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Soubor
     - Role
   * - ``webclient/static/scss/_app-variables.scss``
     - Proměnné světlého tématu (Bootstrap přepisy, barvy entit, layout)
   * - ``webclient/static/scss/_app-variables-dark.scss``
     - Definice tmavých proměnných (barevná paleta, tokeny komponent)
   * - ``webclient/static/scss/_app-theme-dark.scss``
     - SCSS pravidla tmavého režimu — importuje ``-dark`` proměnné
       a aplikuje přepisy uvnitř ``html[data-theme="dark"], body.app-dark-theme { … }``
   * - ``webclient/static/theme.scss``
     - Kořenový SCSS vstupní bod — importuje proměnné → Bootstrap →
       app styly → dark theme naposled
   * - ``webclient/static/bootstrap5/_variables-dark.scss``
     - Vlastní dark-mode proměnné Bootstrap 5 (využívané BS interně)
   * - ``webclient/static/js/theme-toggle.js``
     - JS třída ``ThemeManager`` + inicializace toggle tlačítka
   * - ``webclient/static/cookie-consent/css-components/dark-scheme.css``
     - Dark mode widgetu cookie-consent (``.cc--darkmode``)
   * - ``webclient/static/img/login-bg-dark.svg``
     - Tmavá varianta pozadí přihlašovací stránky

Pořadí importů v ``theme.scss``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: scss

   @import 'scss/app-variables';       // 1. Světlé výchozí hodnoty
   @import 'bootstrap5/bootstrap';      // 2. Bootstrap 5
   @import 'scss/app-mixins';           // 3. App mixiny
   @import 'scss/app-global';           // 4. Globální app styly
   @import 'scss/app-layout';           // 5. Layout
   @import 'scss/app-select2';          // 6. Select2 přepisy
   @import 'scss/app-theme-dark';       // 7. Tmavé téma (poslední — přepisuje vše výše)

Barevné škály
-------------

Světlý režim — odstíny šedé (``_app-variables.scss``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standardní Bootstrap škála šedé pro všechny světlé prvky UI:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Proměnná
     - Hex
     - Použití
   * - ``$white``
     - ``#fff``
     - Pozadí stránky, pozadí karet
   * - ``$gray-100``
     - ``#f8f9fa``
     - Světlá pozadí, jemné výplně
   * - ``$gray-200``
     - ``#e9ecef``
     - Ohraničení, hlavičky karet
   * - ``$gray-300``
     - ``#dee2e6``
     - Ohraničení, oddělovače, disabled stavy
   * - ``$gray-400``
     - ``#ced4da``
     - Ohraničení vstupních polí, muted UI
   * - ``$gray-500``
     - ``#adb5bd``
     - Placeholder text, disabled stav PIAN
   * - ``$gray-600``
     - ``#6c757d``
     - Sekundární text
   * - ``$gray-700``
     - ``#495057``
     - Text (tmavší)
   * - ``$gray-800``
     - ``#343a40``
     - Nadpisy, důraz
   * - ``$gray-900``
     - ``#212529``
     - Téměř černý text, potvrzený stav PIAN
   * - ``$black``
     - ``#000``
     - Čistě černá (výjimečně)

Tmavý režim — odstíny šedé (``_app-variables-dark.scss``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Invertovaná** škála — nízké hodnoty jsou tmavé, vysoké světlé:

.. list-table::
   :header-rows: 1
   :widths: 22 13 65

   * - Proměnná
     - Hex
     - Použití
   * - ``$white-dark``
     - ``#121212``
     - Nahrazuje ``$white`` — nejhlubší pozadí
   * - ``$gray-100-dark``
     - ``#1e1e1e``
     - Hover řádku tabulky, nejhlubší povrch
   * - ``$gray-200-dark``
     - ``#2a2a2a``
     - Hlavičky karet, hlavičky tabulek, sidebar, tělo tabulky
   * - ``$gray-300-dark``
     - ``#3a3a3a``
     - Pozadí navbaru, ``btn-light``, buňky tabulek oznámení
   * - ``$gray-400-dark``
     - ``#4a4a4a``
     - **Primární povrch** — pozadí body, karty, vstupy, sidebar,
       tabulky, posuvník
   * - ``$gray-500-dark``
     - ``#666666``
     - Ohraničení karet, vstupních polí, obecné ohraničení,
       hover posuvníku, disabled select2
   * - ``$gray-600-dark``
     - ``#888888``
     - Placeholder text, daterange hover/in-range, dropzone,
       select2 multi-choice, text accordion sidebaru
   * - ``$gray-700-dark``
     - ``#aaaaaa``
     - Sekundární text
   * - ``$gray-800-dark``
     - ``#d0d0d0``
     - Text s důrazem, pozadí tooltipů
   * - ``$gray-900-dark``
     - ``#e0e0e0``
     - **Primární text** (``$body-text-dark``), nadpisy, popisky
       formulářů
   * - ``$black-dark``
     - ``#ffffff``
     - Nahrazuje ``$black`` — čistě bílý text (invertováno)

Primární / akcentové barvy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Token
     - Světlý
     - Tmavý
     - Použití
   * - ``$primary``
     - ``#0d47a1``
     - —
     - Tlačítka, odkazy, brand accent
   * - ``$primary-dark``
     - —
     - ``#42a5f5``
     - Odkazy, focus border, patička, odznaky, aktivní položky sidebaru
   * - ``$secondary``
     - ``lighten(#303641, 30)``
     - ``lighten(#303641, 60)``
     - Sekundární tlačítka, muted akcenty

Barvy entit (neměnné v tmavém režimu)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Barvy specifické pro entity se v tmavém režimu **nepřepisují**:

.. list-table::
   :header-rows: 1
   :widths: 30 20

   * - Entita
     - Hex
   * - ``dokument``
     - ``#5882c4``
   * - ``projekt``
     - ``#F39225``
   * - ``akce``
     - ``#247e4b``
   * - ``lokalita``
     - ``#951E7A``
   * - ``samostatny_nalez``
     - ``#85140E``
   * - ``knihovna_3d``
     - ``#778e98``
   * - ``let``
     - ``#15968c``
   * - ``ext_zdroj``
     - ``#E7302A``
   * - ``soubor``
     - ``#6c697b``
   * - ``uzivatel``
     - ``#6c697b``

Mapování barev na komponenty (tmavý režim)
------------------------------------------

Layout a struktura
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 30

   * - Komponenta
     - Pozadí
     - Text
     - Ohraničení
   * - **Body / page wrapper**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - ``$gray-900-dark`` (``#e0e0e0``)
     - —
   * - **Navbar**
     - ``$gray-300-dark`` (``#3a3a3a``)
     - ``$gray-900-dark`` (``#e0e0e0``)
     - ``$gray-500-dark``
   * - **Sidebar**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - accordion: ``$gray-600-dark``, active: ``#e0e0e0``
     - ``rgba(#000, .3)``
   * - **Patička**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - ``$gray-900-dark``
     - —

Obsah
~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 26 26 26

   * - Komponenta
     - Pozadí
     - Text
     - Ohraničení
   * - **Karty**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - ``$gray-900-dark``
     - ``$gray-500-dark`` (``#666``)
   * - **Hlavičky karet**
     - ``$gray-200-dark`` (``#2a2a2a``)
     - zděděno
     - ``$gray-500-dark``
   * - **Tabulky (thead)**
     - ``$gray-200-dark`` (``#2a2a2a``)
     - ``$gray-900-dark``
     - ``$gray-500-dark``
   * - **Tabulky (tbody)**
     - ``$gray-200-dark`` (``#2a2a2a``)
     - ``$gray-900-dark``
     - ``$gray-500-dark``
   * - **Řádky tabulky (hover)**
     - ``$gray-100-dark`` (``#1e1e1e``)
     - —
     - —
   * - **Pruhované buňky**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - —
     - —
   * - **Dropdowny**
     - ``$gray-400-dark``
     - ``$gray-900-dark``
     - ``$gray-500-dark``
   * - **Dropdown hover**
     - ``$gray-200-dark`` (``#2a2a2a``)
     - —
     - —
   * - **Modály**
     - ``$gray-400-dark``
     - ``$gray-900-dark``
     - ``$gray-500-dark``
   * - **Hlavičky modálů**
     - ``$gray-200-dark``
     - —
     - ``$gray-500-dark``

Formuláře
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Komponenta
     - Pozadí
     - Text
     - Ohraničení
   * - **Vstupy / selecty**
     - ``$gray-400-dark`` (``#4a4a4a``)
     - ``$gray-900-dark`` (``#e0e0e0``)
     - ``$gray-500-dark`` (``#666``)
   * - **Focus vstupu**
     - ``$gray-400-dark``
     - ``$gray-900-dark``
     - ``$primary-dark`` (``#42a5f5``)
   * - **Placeholder**
     - —
     - ``$gray-600-dark`` (``#888``)
     - —
   * - **Select2 dropdown**
     - ``$gray-400-dark``
     - ``$gray-900-dark``
     - —
   * - **Select2 (vybraný)**
     - ``$primary``
     - ``$gray-900-dark``
     - —
   * - **Select2 (zvýrazněný)**
     - ``$gray-200-dark``
     - ``$gray-900-dark``
     - —
   * - **Select2 multi-choice tagy**
     - ``$gray-600-dark``
     - ``$gray-900-dark``
     - —

Ostatní
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Komponenta
     - Pozadí
     - Text / barva
   * - **Tlačítka** (``.btn-light``)
     - ``$gray-300-dark`` → hover ``$gray-400-dark``
     - ``$gray-900-dark``
   * - **Alerty**
     - ``rgba($gray-500-dark, 0.2)``
     - ``$gray-900-dark``
   * - **Odznaky (badges)**
     - ``$primary-dark`` (``#42a5f5``)
     - ``$white-dark`` (``#121212``)
   * - **Tooltipy**
     - ``$gray-800-dark`` (``#d0d0d0``)
     - ``$white-dark`` (``#121212``)
   * - **Text muted**
     - ``rgba(253,254,255, 0.8)``
     - —
   * - **Posuvník (track)**
     - ``$gray-200-dark``
     - —
   * - **Posuvník (thumb)**
     - ``$gray-400-dark`` → hover ``$gray-500-dark``
     - —
   * - **Daterangepicker**
     - ``$gray-400-dark``
     - ``#ebf4f0``
   * - **Daterange (aktivní)**
     - ``#357ebd``
     - ``#ebf4f8``
   * - **Daterange (in-range)**
     - ``$gray-600-dark``
     - ``#ebf4f8``

Přihlašovací / registrační stránky
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tmavé přihlašovací stránky používají stejné tokeny proměnných plus:

- Pozadí se přepíná na ``login-bg-dark.svg``
- Ohraničení ``input-group-text``: natvrdo ``#666666``
- Vnitřní sloupec popisu: pozadí ``#d2d2d20d`` s levým ohraničením ``$border-color-dark``

Widget cookie consent
~~~~~~~~~~~~~~~~~~~~~

Knihovna cookie-consent používá vlastní třídu ``.cc--darkmode`` s plně
nezávislou paletou definovanou v ``dark-scheme.css`` (základ ``#161a1c``,
tlačítka ``#c2d0e0`` / ``#242c31`` atd.). Tato paleta **není** napojena
na ``ThemeManager`` aplikace.

Interakce vrstev
----------------

::

   ┌──────────────────────────────────────────────┐
   │  _app-variables.scss  (světlé výchozí)       │
   ├──────────────────────────────────────────────┤
   │  Bootstrap 5  (využívá světlé výchozí)       │
   ├──────────────────────────────────────────────┤
   │  _app-global.scss / _app-layout.scss          │
   │  (app komponenty se světlými výchozími)       │
   ├──────────────────────────────────────────────┤
   │  _app-theme-dark.scss                         │
   │  └─ importuje _app-variables-dark.scss        │
   │  └─ scoped pod html[data-theme="dark"]        │
   │  └─ přepisuje CSS custom properties           │
   │  └─ per-component SCSS přepisy                │
   └──────────────────────────────────────────────┘

   JS ThemeManager  ──→  nastaví data-theme="dark" na <html>
                    ──→  přidá .app-dark-theme na <body>
                    ──→  SCSS pravidla se aktivují

Poznámky a postřehy
--------------------

- Tmavý režim používá **jednu střední šedou** (``#4a4a4a``) jako dominantní
  barvu povrchu pro body, karty, vstupy i sidebar. To vytváří uniformně
  „středně tmavý" vzhled místo hlubokého dark UI.
- Barvy entit **nejsou přizpůsobeny** pro tmavý režim — některé
  (např. ``#85140E`` pro ``samostatny_nalez``) mohou mít nízký kontrast
  vůči pozadí ``#4a4a4a``.
- V ``_app-theme-dark.scss`` existuje několik natvrdo zadaných barevných
  hodnot (``#357ebd``, ``#ebf4f0``, ``#d2d2d20d``, ``#666666``) mimo
  systém proměnných.
- Paleta cookie-consent dark je nezávislá a nerespektuje škálu šedé
  aplikace.
- Bootstrap 5 má vlastní ``_variables-dark.scss``, ale aplikace dark theme
  používá **separátní, paralelní** SCSS vrstvu (``_app-theme-dark.scss``)
  místo BS5 mechanismu ``[data-bs-theme="dark"]``.
