Skript generate_module_docs
===========================

Dokumentace skriptu ``docs/generate_module_docs.py``.

Funkce
------

.. py:function:: check_content_changed(content, output_file)

   Zkontroluje, zda se obsah liší od existujícího souboru.

   :param content: Nový obsah k porovnání.
   :param output_file: Cesta k existujícímu souboru.
   :return: True, pokud se obsah změnil nebo soubor neexistuje

.. py:function:: extract_url_patterns(urls_file)

   Extrahujte vzory URL ze souboru urls.py.

   :param urls_file: Cesta k souboru urls.py.
   :return: Každý url_pattern je slovník s klíči: ``pattern``, ``view``, ``name``

.. py:function:: parse_path_call(node)

   Analyzuje volání path() nebo re_path() a extrahuje informace o vzoru URL.

   :param node: uzel AST představující volání path().
   :return: ``dict: {'pattern': str, 'view': str, 'name': str} or None``

.. py:function:: generate_url_routing_rst()

   Vygeneruje dokumentaci k směrování URL pro všechny moduly.

   Vytvoří docs/source/04_django_aplikace/04_01_core/url_routing.rst
   s tabulkami všech vzorů URL z urls.py každého modulu.

   :return: True, pokud úspěšné, jinak false

.. py:function:: extract_signals(signals_file)

   Extrahuje přijímače signálu ze souboru signals.py.

   :param signals_file: Cesta k souboru signals.py.
   :return: Seznam slovníků informací o signálech s klíči: ``function``, ``signal_type``, ``sender``, ``weak``

.. py:function:: parse_receiver_decorator(decorator, function_name)

   Analyzujte dekorátor @receiver(), abyste extrahovali informace o signálu.

   :param decorator: AST Volací uzel představující @receiver()
   :param function_name: Název dekorované funkce
   :return: ``dict: {'function': str, 'signal_type': str, 'sender': str, 'weak': str} or None``

.. py:function:: generate_signals_rst()

   Vygeneruje dokumentaci signálů pro všechny moduly.

   Vytvoří docs/source/04_django_aplikace/04_01_core/signals.rst
   s tabulkami všech přijímačů signálů z každého modulu signals.py

   :return: True v případě úspěchu, False v opačném případě.

.. py:function:: extract_permissions(models_file)

   Extrahuje možnosti akcí z třídy Permissions v models.py.

   :param models_file: Cesta k souboru models.py.
   :return: Seznam názvů akcí (např. ``adb_smazat``, ``vb_smazat``)

.. py:function:: generate_permissions_rst()

   Vygeneruje dokumentaci oprávnění.

   Aktualizuje docs/source/04_django_aplikace/04_01_core/permissions.rst
   připojením seznamu všech definovaných akcí z Permissions.actionChoices
   za nadpis „Uživatelské akce řízené pomocí oprávnění”.

   :return: True, pokud úspěšné, jinak False.

.. py:function:: clean_comment_value(value)

   Odstraní obalové uvozovky/závorky z hodnoty komentáře.

   :param value: Hodnota parametru ``value``.
   :return: Návratová hodnota funkce.

.. py:function:: parse_comment_values(comment_text)

   Vrátí mapované hodnoty získané z inline komentáře XSD.

   :param comment_text: Hodnota parametru ``comment_text``.
   :return: Návratová hodnota funkce.

.. py:function:: get_following_comment(parent, element)

   Najde první uzel komentáře bezprostředně za daným elementem.

   :param parent: Hodnota parametru ``parent``.
   :param element: Hodnota parametru ``element``.
   :return: Návratová hodnota funkce.

.. py:function:: collect_choice_element_names(choice_element)

   Shromáždí názvy všech uzlů xs:element uvnitř bloku choice.

   :param choice_element: Hodnota parametru ``choice_element``.
   :return: Návratová hodnota funkce.

.. py:function:: format_choice_note(names)

   Naformátuje poznámku popisující možnosti uvnitř elementu choice.

   :param names: Hodnota parametru ``names``.
   :return: Návratová hodnota funkce.

.. py:function:: extract_elements_from_parent(parent, choice_context)

   Rekurzivně extrahuje definice elementů a zaznamená kontext choice, pokud existuje.

   :param parent: Hodnota parametru ``parent``.
   :param choice_context: Hodnota parametru ``choice_context``.
   :return: Návratová hodnota funkce.

.. py:function:: extract_elements_from_complex_type(complex_type)

   Extrahuje řádky elementů z definice complexType.

   :param complex_type: Hodnota parametru ``complex_type``.
   :return: Návratová hodnota funkce.

.. py:function:: extract_model_mappings(schema_root)

   Načte mapování z volby elementu amcr do řádků Model -> ComplexType.

   :param schema_root: Hodnota parametru ``schema_root``.
   :return: Návratová hodnota funkce.

.. py:function:: extract_xsd_version(schema_root)

   Extrahuje atribut verze z kořenového prvku schématu XSD.

   :param schema_root: Kořenový prvek schématu XSD.
   :return: Verze (např. „2.2“) nebo „neznámá“, pokud nebyla nalezena

.. py:function:: extract_django_command_info(command_file)

   Extrahuje informace o dokumentaci ze souboru příkazů pro správu Django.

   :param command_file: Cesta k příkazovému souboru.
   :return: ``dict: {'name': str, 'help': str, 'docstring': str, 'arguments': list}``

.. py:function:: extract_command_arguments(add_arguments_node)

   Extrahuje definice argumentů z metody add_arguments.

   :param add_arguments_node: AST uzel metody add_arguments.
   :return: Seznam slovníků s informacemi o argumentech s klíči: ``name``, ``type``, ``help``, ``default``

.. py:function:: generate_management_commands_rst()

   Vygeneruje dokumentaci k příkazům pro správu.

   Vytvoří docs/source/04_django_aplikace/04_01_core/management_commands.rst
   s dokumentací ke všem příkazům pro správu Django v core/management/commands.

   :return: True, pokud úspěšné, jinak False.

.. py:function:: generate_export_structure_rst()

   Vygeneruje docs/source/05_integrace/export_structure.rst ze souboru amcr.xsd.

   :return: Návratová hodnota funkce.

.. py:function:: has_meaningful_code(source_file)

   Zkontroluje, zda soubor Python obsahuje smysluplný kód (nejen komentáře).

   :param source_file: Cesta k souboru.
   :return: rue, pokud soubor obsahuje smysluplný kód, False v opačném případě.

.. py:function:: extract_docstrings(source_file)

   Extrahuje docstrings z modulu Python pomocí AST parsování.

   :param source_file: Cesta ke zdrojovému souboru.
   :return: tuple: (třídy, funkce), kde každá je seznamem slovníků.

.. py:function:: format_docstring_for_rst(docstring, indent)

   Formátuje docstring ve stylu Google pro výstup RST.

   Převádí sekce Args:, Returns: atd. do správného formátu RST
   s názvy argumentů uzavřenými v zpětných lomítkách. Názvy sekcí jsou přeloženy
   do češtiny.

   :param docstring: Docstring, který se má formátovat
   :param indent: Prefix odsazení pro každý řádek.
   :return: Seznam formátovaných řádků RST.

.. py:function:: generate_rst_explicit(source_file, module_name, module_title, module_description)

   Vygeneruje soubor RST s explicitním obsahem docstringu.

   :param source_file: Cesta k zdrojovému souboru.
   :param module_name: Plně kvalifikovaný název modulu.
   :param module_title: Název souboru RST.
   :param module_description: Popis modulu.
   :return: Vygenerovaný obsah RST.

.. py:function:: generate_rst_autodoc(module_name, module_title, module_description)

   Vygeneruje soubor RST pomocí direktiv Sphinx autodoc.

   :param module_name: Plně kvalifikovaný název modulu.
   :param module_title: Název souboru RST`.
   :param module_description: HPopis modulu.
   :return: Vygenerovaný obsah RST.

.. py:function:: get_module_title_and_description(module_dir_name, filename)

   Předá příslušný název a popis souboru modulu.

   :param module_dir_name: Název adresáře modulu (např. ``adb``, ``core``).
   :param filename: Název souboru Python (např. ``models.py``).
   :return: tuple: (title, description)

.. py:function:: generate_rst_for_file(source_file, module_dir_name, output_dir, mode)

   Vygeneruje dokumentaci RST pro jeden soubor Python.

   :param source_file: Cesta ke zdrojovému souboru Python.
   :param module_dir_name: Název adresáře modulu.
   :param output_dir: Výstupní adresář pro soubory RST.
   :param mode: Režim generování (``autodoc`` nebo ``explicit``).
   :return: True v případě úspěchu, False v opačném případě.

.. py:function:: generate_index_rst(module_dir_name, generated_files, output_dir)

   Vygeneruje soubor index.rst s toctree všech vygenerovaných modulů.

   :param module_dir_name: Název adresáře modulu.
   :param generated_files: Seznam vygenerovaných názvů souborů Python.
   :param output_dir: Výstupní adresář.
   :return: True v případě úspěchu, False v opačném případě

.. py:function:: process_module(module_dir_name, mode)

   Zpracuje jeden adresář modulu.

   :param module_dir_name: Název adresáře modulu.
   :param mode: Režim generování (``autodoc`` nebo ``explicit``).
   :return: True, pokud byly vygenerovány nějaké soubory.

.. py:function:: get_all_modules()

   Získá všechny adresáře modulů Django z webového klienta.

   :return: Seznam názvů adresářů modulů.

.. py:function:: generate_all_modules(mode, specific_module)

   Vygeneruje soubory RST pro všechny moduly nebo konkrétní modul.

   :param mode: Režim generování (``autodoc`` nebo ``explicit``).
   :param specific_module: Konkrétní modul, který se má zpracovat, nebo None pro všechny.
   :return: True, pokud byla vygenerována nějaká dokumentace.

.. py:function:: generate_rst_for_docs_script(source_file, output_dir, mode)

   Vygeneruje dokumentaci RST pro jeden Python skript v adresáři docs/.

   :param source_file: Cesta ke zdrojovému souboru Python v docs/.
   :param output_dir: Výstupní adresář pro soubory RST.
   :param mode: Režim generování (``autodoc`` nebo ``explicit``).
   :return: True v případě úspěchu, False v opačném případě.

.. py:function:: generate_docs_scripts_index_rst(generated_files, output_dir)

   Vygeneruje index.rst pro dokumentační skripty v docs/.

   :param generated_files: Seznam vygenerovaných názvů souborů Python.
   :param output_dir: Výstupní adresář.
   :return: True v případě úspěchu, False v opačném případě.

.. py:function:: generate_docs_scripts_docs(mode)

   Vygeneruje RST dokumentaci pro všechny ``*.py`` skripty v ``docs/``.

   :param mode: Režim generování (``autodoc`` nebo ``explicit``).
   :return: True, pokud byl vygenerován alespoň jeden soubor.

.. py:function:: build_docs()

   Vytvoří HTML dokumentaci pomocí Sphinx.

   :return: True, pokud se sestavení podařilo, False v opačném případě.

.. py:function:: main()

   Hlavní funkce pro spuštění generátoru dokumentace.
