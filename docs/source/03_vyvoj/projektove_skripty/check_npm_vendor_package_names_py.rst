Skript check_npm_vendor_package_names.py
========================================

Automaticky generovaná dokumentace skriptu ``scripts/check_npm_vendor_package_names.py``.

Přehled modulu
--------------

Kontrola souladu záložní n-tice ``_NPM_VENDOR_PACKAGE_NAMES`` v Django ``base.py`` s klíči
``dependencies`` v kořenovém ``package.json``.

Při ``--fix`` přepíše n-tici tak, aby přesně odpovídala (abecedně seřazené) klíčům z ``dependencies``.

Výstup pro uživatele a CI: řádky na stderr s prefixem ``[npm-vendor-names]`` (grep v GitHub Actions).

Funkce
------

.. py:function:: log_msg(message)

   Vypíše jeden řádek na stderr s prefixem pro přehled v CI a PR komentářích.

   :param message: Text bez prefixu (typicky ``ERROR:``, ``FIX:`` nebo ``INFO:``).

.. py:function:: repo_root()

   Vrátí kořen repozitáře (nadřazený adresář ``scripts/``).

   :return: Cesta ke kořeni.

.. py:function:: load_dependency_keys(root)

   Načte množinu jmen přímých závislostí z kořenového ``package.json``.

   :param root: Kořen repozitáře.
   :return: Klíče sekce ``dependencies``.
   :raises FileNotFoundError: Vyvolá se, pokud v kořeni chybí soubor ``package.json``.
   :raises json.JSONDecodeError: Vyvolá se při neplatném JSON v souboru.
   :raises ValueError: Vyvolá se, pokud kořen JSON není objekt, pole ``dependencies`` není objekt,
       nebo ne všechny klíče v ``dependencies`` jsou řetězce.

.. py:function:: _tuple_inner_span(text, open_paren_index)

   Najde indexy obsahu n-tice: ``text[inner_start:inner_end]`` je tělo mezi závorkami (bez ``(`` a ``)``).

   Respektuje řetězce a escape sekvence; mimo řetězec ignoruje obsah po ``#`` do konce řádku.

   :param text: Celý obsah souboru.
   :param open_paren_index: Index otevírací závorky ``(`` přiřazení n-tice.
   :return: ``(inner_start, inner_end)`` nebo ``None`` při neuzavřené závorce.

.. py:function:: locate_vendor_tuple_assignment(text)

   Najde v ``base.py`` span přiřazení ``_NPM_VENDOR_PACKAGE_NAMES = (...)``.

   :param text: Obsah ``base.py``.
   :return: ``(assign_start, assign_end, inner_start, inner_end)`` — celý blok k nahrazení
       je ``text[assign_start:assign_end]``; ``inner_*`` je tělo n-tice pro ``ast``.

.. py:function:: parse_tuple_string_literals(inner)

   Parsuje tělo n-tice a vrátí seznam řetězcových literálů v pořadí výskytu.

   :param inner: Obsah mezi ``(`` a ``)`` včetně komentářů a řádkových zalomení.
   :return: Seznam hodnot řetězců.
   :raises ValueError: při neplatné syntaxi nebo nečistě řetězcových prvcích.

.. py:function:: _elts_as_str_list(value)

   Vrátí řetězce z ``ast.Tuple`` nebo jednoprvkové n-tice.

.. py:function:: build_tuple_assignment(sorted_names)

   Sestaví text přiřazení ``_NPM_VENDOR_PACKAGE_NAMES = (...)`` ve stylu Black (odsazení 4 mezery).

   :param sorted_names: Již seřazené názvy balíčků.
   :return: Text včetně koncového ``\n\n`` před následující definici.

.. py:function:: read_tuple_names(base_path)

   Načte ``base.py`` a extrahuje množinu jmen z ``_NPM_VENDOR_PACKAGE_NAMES``.

   :param base_path: Cesta k ``base.py``.
   :return: ``(celý_text, množina_jmen)``.

.. py:function:: main(argv)

   Vstupní bod CLI.

   :param argv: Argumenty bez ``sys.argv[0]``; ``None`` = ``sys.argv[1:]``.
   :return: ``0`` při OK; ``1`` při chybě nebo po úspěšném ``--fix`` se změnou souboru (pre-commit).

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/check_npm_vendor_package_names.py
   :language: python
   :linenos:
