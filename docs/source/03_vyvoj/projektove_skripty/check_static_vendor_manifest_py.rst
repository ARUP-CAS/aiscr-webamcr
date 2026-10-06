Skript check_static_vendor_manifest.py
======================================

Automaticky generovaná dokumentace skriptu ``scripts/check_static_vendor_manifest.py``.

Přehled modulu
--------------

Kontrola souladu manifestu ``webclient/static_vendor.json`` s knihovnami třetích stran vloženými
do ``webclient/static/``.

Ověřuje, že:

* každá položka manifestu má vyplněný název, verzi, licenci, zdroj a seznam cest,
* každá cesta z manifestu existuje a patří jen jedné položce,
* každý soubor pod ``webclient/static/vendor/`` je v manifestu,
* žádný adresář pod ``webclient/static/vendor/`` se nejmenuje jako balíček z ``dependencies``
v ``package.json`` (knihovna nesmí být zároveň z npm i vendorovaná),
* relativní ``url(...)`` v CSS souborech z manifestu míří na existující soubor,
* každý odkaz ``{% static 'vendor/...' %}`` v šablonách míří na soubor z manifestu.

Výstup pro uživatele a CI: řádky na stderr s prefixem ``[static-vendor]`` (grep v GitHub Actions).

Funkce
------

.. py:function:: log_msg(message)

   Vypíše jeden řádek na stderr s prefixem pro přehled v CI a PR komentářích.

   :param message: Text bez prefixu (typicky ``ERROR:`` nebo ``INFO:``).

.. py:function:: repo_root()

   Vrátí kořen repozitáře (nadřazený adresář ``scripts/``).

   :return: Cesta ke kořeni.

.. py:function:: load_manifest(root)

   Načte seznam knihoven z manifestu ``webclient/static_vendor.json``.

   :param root: Kořen repozitáře.
   :return: Položky pole ``libraries``.
   :raises FileNotFoundError: Vyvolá se, pokud manifest neexistuje.
   :raises json.JSONDecodeError: Vyvolá se při neplatném JSON.
   :raises ValueError: Vyvolá se, pokud kořen není objekt nebo ``libraries`` není pole objektů.

.. py:function:: load_npm_dependencies(root)

   Načte jména přímých závislostí z kořenového ``package.json``.

   :param root: Kořen repozitáře.
   :return: Klíče sekce ``dependencies``; prázdná množina, pokud soubor chybí.

.. py:function:: is_static_relative(rel)

   Ověří, že cesta z manifestu je POSIX cesta relativní k ``webclient/static/`` a nevede mimo něj.

   :param rel: Cesta z pole ``paths`` (např. ``vendor/leaflet-search/leaflet-search.js``).
   :return: ``False`` pro prázdnou cestu (``.``), absolutní cestu, cestu s diskem, zpětným lomítkem
       nebo komponentou ``..``.

.. py:function:: is_inside(static_dir, path)

   Ověří, že cesta po vyřešení symlinků leží uvnitř ``webclient/static/``.

   Doplňuje lexikální :func:`is_static_relative`: symlink ve ``static/`` mířící ven neprojde.

   :param static_dir: Adresář ``webclient/static``.
   :param path: Kontrolovaná cesta (nemusí existovat).
   :return: ``True``, pokud ``path.resolve()`` je pod ``static_dir.resolve()``.

.. py:function:: check_entries(libraries, static_dir)

   Zkontroluje povinná pole položek a existenci jejich cest.

   :param libraries: Položky manifestu.
   :param static_dir: Adresář ``webclient/static``.
   :return: ``(chyby, mapa cesta → název knihovny)`` pro všechny cesty z manifestu.

.. py:function:: check_vendor_dir(static_dir, owners, npm_deps)

   Zkontroluje, že každý soubor pod ``static/vendor/`` je v manifestu a že žádný podadresář
   nenese jméno npm závislosti.

   :param static_dir: Adresář ``webclient/static``.
   :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
   :param npm_deps: Jména závislostí z ``package.json``.
   :return: Seznam chyb.

.. py:function:: check_css_urls(static_dir, owners)

   Zkontroluje, že relativní ``url(...)`` v CSS souborech z manifestu míří na existující soubor.

   Absolutní URL (``http:``, ``//``, ``/``), ``data:`` URI a odkazy na fragment se přeskakují.

   :param static_dir: Adresář ``webclient/static``.
   :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
   :return: Seznam chyb.

.. py:function:: check_template_references(templates_root, owners)

   Zkontroluje, že odkazy ``{% static 'vendor/...' %}`` v šablonách míří na soubory z manifestu.

   :param templates_root: Adresář, pod kterým se hledají šablony ``*.html``.
   :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
   :return: Seznam chyb.

.. py:function:: collect_errors(root)

   Provede všechny kontroly nad repozitářem.

   :param root: Kořen repozitáře.
   :return: Seznam chyb; prázdný seznam znamená soulad.
   :raises FileNotFoundError: Vyvolá se, pokud manifest neexistuje.
   :raises json.JSONDecodeError: Vyvolá se při neplatném JSON manifestu nebo ``package.json``.
   :raises ValueError: Vyvolá se při neplatné struktuře manifestu.

.. py:function:: main(argv)

   Vstupní bod CLI.

   :param argv: Argumenty bez ``sys.argv[0]``; ``None`` = ``sys.argv[1:]``.
   :return: ``0`` při souladu, ``1`` při chybě.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/check_static_vendor_manifest.py
   :language: python
   :linenos:
