Skript generate_module_docs
===========================

Dokumentace skriptu ``docs/generate_module_docs.py``.

Přehled modulu
--------------

Skript pro generování Sphinx dokumentace pro všechny Django moduly v webclient/
a jejich uložení do docs/source/04_django_aplikace/04_02_moduly/

Skript extrahuje docstringy z modulů a generuje podrobnou
reStructuredText dokumentaci pro každý adresář modulu.


**Použití:**

- autodoc: Používá direktivy Sphinx autodoc
- explicit: Zapisuje docstringy přímo do RST
  --module MODULE Konkrétní modul ke zpracování (např. 'adb', 'core')
  Pokud není zadáno, zpracuje všechny moduly

Třídy
------

.. py:class:: DockerImageScanner

   Prohledává soubory projektu a sbírá tagy Docker image.

   Prochází všechny soubory ``docker-compose*.yml`` v kořenovém adresáři projektu
   a soubor ``Dockerfile-DB``. Výsledkem je slovník mapující základní název image
   (bez tagu) na jeho plný tag.

   :param project_root: Kořenový adresář projektu.
   :type project_root: Path

   **Metody:**

   .. py:method:: __init__()

      Inicializuje scanner s kořenovým adresářem projektu.

      :param project_root: Kořenový adresář projektu.
      :type project_root: Path

   .. py:method:: collect_versions()

      Shromáždí verze image ze souborů docker-compose a Dockerfile-DB.

      Prochází nejprve compose soubory, poté ``Dockerfile-DB``. Pro každý
      základní název image je uložen první nalezený plný tag (produkční soubory
      mají přednost díky pořadí vrácenému metodou :meth:`_ordered_compose_files`).

      :return: Slovník ``{základní název image: plný tag}``.
      :rtype: Dict[str, str]

   .. py:method:: _compose_images()

      Extrahuje plné tagy image ze souborů docker-compose.

      Přeskočí proměnné (``${...}``) a testovací image
      (``docker.io/library/test_*``).

      :return: Seznam plných tagů image (např. ``redis:8.4.0``).
      :rtype: List[str]

   .. py:method:: _dockerfile_images()

      Extrahuje image z direktiv FROM v souboru Dockerfile-DB.

      Pokud soubor ``Dockerfile-DB`` neexistuje, vrátí prázdný seznam.

      :return: Seznam plných tagů image z direktiv FROM.
      :rtype: List[str]

   .. py:method:: _ordered_compose_files()

      Vrátí seznam souborů docker-compose seřazených podle priority.

      Produkční soubory (``docker-compose.yml``, ``docker-compose-proxy.yml``)
      jsou řazeny jako první, aby jejich verze image měly přednost při volání
      :meth:`collect_versions`.

      :return: Seřazený seznam cest k souborům docker-compose.
      :rtype: List[Path]

   .. py:method:: _base_image()

      Vrátí základní název image bez tagu.

      :param full_tag: Plný tag image (např. ``redis:8.4.0``).
      :type full_tag: str
      :return: Název image bez tagu (např. ``redis``).
      :rtype: str


.. py:class:: JsLibrary

   Datová třída reprezentující jednu Node.js knihovnu.

   :param name: Název balíčku (např. ``bootstrap``).
   :type name: str
   :param version: Verze balíčku (např. ``5.3.8``).
   :type version: str
   :param license: Identifikátor licence (např. ``MIT``).
   :type license: str
   :param homepage: URL domovské stránky nebo repozitáře knihovny.
   :type homepage: str


Funkce
------

.. py:function:: vprint()

   Vypíše zprávu pouze ve verbose režimu.

   :param args: Poziční argumenty předané do ``print()``.
   :param kwargs: Klíčové argumenty předané do ``print()``.

.. py:function:: check_content_changed(content, output_file)

   Zkontroluje, zda se obsah liší od existujícího souboru.

   :param content: Nový obsah k porovnání.
   :param output_file: Cesta k existujícímu souboru.
   :return: True, pokud se obsah změnil nebo soubor neexistuje

.. py:function:: extract_url_patterns(urls_file)

   Extrahujte vzory URL ze souboru urls.py.

   :param urls_file: Cesta k souboru urls.py.
   :return: Každý url_pattern je slovník s klíči: ``pattern``, ``view``, ```name```

.. py:function:: parse_path_call(node)

   Analyzuje volání path() nebo re_path() a extrahuje informace o vzoru URL.

   :param node: uzel AST představující volání path().
   :return: ```dict: {'pattern': str, 'view': str, 'name': str} or None```

.. py:function:: generate_url_routing_rst()

   Vygeneruje dokumentaci k směrování URL pro všechny moduly.

   Vytvoří docs/source/04_django_aplikace/04_01_core/url_routing.rst
   s tabulkami všech vzorů URL z urls.py každého modulu.

   :return: True, pokud úspěšné, jinak false

.. py:function:: extract_signals(signals_file)

   Extrahuje přijímače signálu ze souboru signals.py.

   :param signals_file: Cesta k souboru signals.py.
   :return: Seznam slovníků informací o signálech s klíči: ``function``, ``signal_type``, ``sender``, ```weak```

.. py:function:: parse_receiver_decorator(decorator, function_name)

   Analyzuje dekorátor @receiver() pro extrakci informací o signálu.

   :param decorator: AST Volací uzel představující @receiver()
   :param function_name: Název dekorované funkce
   :return: ```dict: {'function': str, 'signal_type': str, 'sender': str, 'weak': str} or None```

.. py:function:: generate_signals_rst()

   Vygeneruje dokumentaci signálů pro všechny moduly.

   Vytvoří docs/source/04_django_aplikace/04_01_core/signals.rst
   s tabulkami všech přijímačů signálů z každého modulu signals.py

   :return: True v případě úspěchu, False v opačném případě.

.. py:function:: extract_permissions(models_file)

   Extrahuje možnosti akcí z třídy Permissions v models.py.

   :param models_file: Cesta k souboru models.py.
   :return: Seznam názvů akcí (např. ``adb_smazat``, ```vb_smazat```)

.. py:function:: generate_permissions_rst()

   Vygeneruje dokumentaci oprávnění.

   Aktualizuje docs/source/04_django_aplikace/04_01_core/permissions.rst
   připojením seznamu všech definovaných akcí z Permissions.actionChoices
   za nadpis „Uživatelské akce řízené pomocí oprávnění”.

   :return: True, pokud úspěšné, jinak False.

.. py:function:: clean_comment_value(value)

   Odstraní obalové uvozovky/závorky z hodnoty komentáře.

   :param value: Parametr ``value`` pracuje se s atributy ``strip``.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: parse_comment_values(comment_text)

   Vrátí mapované hodnoty získané z inline komentáře XSD.

   :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: get_following_comment(parent, element)

   Najde první uzel komentáře bezprostředně za daným elementem.

   :param parent: Parametr ``parent`` se předává do volání ``list()``.
   :param element: Parametr ``element`` ovlivňuje větvení podmínek.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: collect_choice_element_names(choice_element)

   Shromáždí názvy všech uzlů xs:element uvnitř bloku choice.

   :param choice_element: Parametr ``choice_element`` slouží jako vstup pro logiku funkce ``collect_choice_element_names``.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: format_choice_note(names)

   Naformátuje poznámku popisující možnosti uvnitř elementu choice.

   :param names: Kolekce ``names`` zpracovávaná touto funkcí.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: extract_elements_from_parent(parent, choice_context)

   Rekurzivně extrahuje definice elementů a zaznamená kontext choice, pokud existuje.

   :param parent: Parametr ``parent`` se předává do volání ``get_following_comment()``.
   :param choice_context: Kolekce ``choice_context`` zpracovávaná touto funkcí.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: extract_elements_from_complex_type(complex_type)

   Extrahuje řádky elementů z definice complexType.

   :param complex_type: Parametr ``complex_type`` slouží jako vstup pro logiku funkce ``extract_elements_from_complex_type``.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: extract_model_mappings(schema_root)

   Načte mapování z volby elementu amcr do řádků Model -> ComplexType.

   :param schema_root: Parametr ``schema_root`` pracuje se s atributy ``find``.
   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: extract_xsd_version(schema_root)

   Extrahuje atribut verze z kořenového prvku schématu XSD.

   :param schema_root: Kořenový prvek schématu XSD.
   :return: Verze (např. „2.2“) nebo „neznámá“, pokud nebyla nalezena

.. py:function:: extract_django_command_info(command_file)

   Extrahuje informace o dokumentaci ze souboru příkazů pro správu Django.

   :param command_file: Cesta k příkazovému souboru.
   :return: ```dict: {'name': str, 'help': str, 'docstring': str, 'arguments': list}```

.. py:function:: extract_command_arguments(add_arguments_node)

   Extrahuje definice argumentů z metody add_arguments.

   :param add_arguments_node: AST uzel metody add_arguments.
   :return: Seznam slovníků s informacemi o argumentech s klíči: ``name``, ``type``, ``help``, ```default```

.. py:function:: generate_management_commands_rst()

   Vygeneruje dokumentaci k příkazům pro správu.

   Vytvoří docs/source/04_django_aplikace/04_01_core/management_commands.rst
   s dokumentací ke všem příkazům pro správu Django v core/management/commands.

   :return: True, pokud úspěšné, jinak False.

.. py:function:: generate_export_structure_rst()

   Vygeneruje docs/source/05_integrace/export_structure.rst ze souboru amcr.xsd.

   :return: Hodnota vrácená funkcí podle aktuální logiky implementace.

.. py:function:: has_meaningful_code(source_file)

   Zkontroluje, zda soubor Python obsahuje smysluplný kód (nejen komentáře).

   :param source_file: Cesta k souboru.
   :return: rue, pokud soubor obsahuje smysluplný kód, False v opačném případě.

.. py:function:: extract_docstrings(source_file)

   Extrahuje docstrings z modulu Python pomocí AST parsování.

   :param source_file: Cesta ke zdrojovému souboru.
   :return: tuple: (docstring modulu nebo None, třídy, funkce); třídy a funkce jsou seznamy slovníků.

.. py:function:: _looks_like_sphinx_fieldlist(docstring)

   Vrátí True, pokud text vypadá jako Sphinx info pole (:param:, :return: atd.).

.. py:function:: _indent_docstring_lines(docstring, indent)

   Přidá ``indent`` k neprázdným řádkům; prázdné řádky ponechá prázdné.

.. py:function:: format_docstring_for_rst(docstring, indent)

   Formátuje docstring pro výstup RST v režimu explicit.

   Docstringy se Sphinx poli (:param:, :return:, …) se předají beze změny obsahu (jen odsazení).
   Google sekce (Args:, Returns:, …) se převedou na stejná Sphinx info pole.

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

.. py:function:: get_script_language(script_name)

   Vrátí jazyk pro zvýraznění syntaxe podle přípony souboru.

   :param script_name: Parametr ``script_name`` předává se do volání ``Path()``.
   :return: Vrací hodnotu typu ``str`` (str).

.. py:function:: get_script_doc_name(script_name)

   Vrátí bezpečný název RST souboru pro skript.

   :param script_name: Parametr ``script_name`` předává se do volání ``sub()``, vstupuje do návratové hodnoty.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``lower()``).

.. py:function:: generate_rst_for_project_script(source_file, output_dir)

   Vygeneruje RST dokumentaci pro jeden soubor v adresáři scripts/.

   :param source_file: Parametr ``source_file`` předává se do volání ``get_script_doc_name()``, ``get_script_language()``, pracuje se s atributy ``name``.
   :param output_dir: Parametr ``output_dir`` slouží jako vstup pro logiku funkce ``generate_rst_for_project_script``.
   :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.

.. py:function:: generate_project_scripts_index_rst(toctree_entries, output_dir)

   Vygeneruje index.rst pro skripty v adresáři scripts/.

   :param toctree_entries: Parametr ``toctree_entries`` předává se do volání ``sorted()``.
   :param output_dir: Parametr ``output_dir`` slouží jako vstup pro logiku funkce ``generate_project_scripts_index_rst``.
   :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.

.. py:function:: generate_project_scripts_docs()

   Vygeneruje RST dokumentaci pro soubory v ``scripts/``.

   :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.

.. py:function:: build_docs()

   Vytvoří HTML dokumentaci pomocí Sphinx.

   :return: True, pokud se sestavení podařilo, False v opačném případě.

.. py:function:: _fetch_dockerhub_odkaz(image)

   Načte zdrojovou URL pro Docker Hub image (best-effort, bez autentizace).

   :param image: Základní název image, např. ``grafana/grafana-enterprise``.
   :type image: str
   :return: Řetězec zdrojové URL, nebo prázdný řetězec při chybě nebo nepodporovaném registru.
   :rtype: str

.. py:function:: _is_git_ignored(path)

   Zjistí, zda je soubor ignorovaný gitem (``.gitignore`` apod.).

   Využívá ``git check-ignore``. Pokud git není dostupný nebo příkaz selže,
   soubor se považuje za sledovaný (vrací ``False``), aby kontrola zůstala
   konzervativní mimo git repozitář.

   :param path: Cesta k souboru ke kontrole.
   :type path: Path
   :return: True, pokud je soubor ignorovaný gitem, jinak False.
   :rtype: bool

.. py:function:: _parse_compose_versions(project_root)

   Parsuje všechny soubory docker-compose*.yml a Dockerfile-DB v project_root
   a hledá direktivy image:. Vrátí slovník mapující základní název image na plný tag.

   Priorita: docker-compose.yml / docker-compose-proxy.yml (produkce) jako první,
   poté ostatní soubory.

   :param project_root: Kořenový adresář projektu.
   :type project_root: Path
   :return: Slovník ``{základní název image: plný tag}``.
   :rtype: Dict[str, str]

.. py:function:: _check_missing_meta_images(versions, images_meta)

   Vrátí seznam základních názvů image nalezených v docker-compose / Dockerfile-DB,
   které nejsou pokryty žádným záznamem v docker_images_meta.yaml.

   Proměnné reference na image (``${...}``) v compose souborech jsou již filtrovány
   třídou DockerImageScanner, takže jsou kontrolovány pouze konkrétní názvy image.

   :param versions: Slovník ``{základní název image: plný tag}`` z docker-compose souborů.
   :type versions: Dict[str, str]
   :param images_meta: Seznam metadatových záznamů z docker_images_meta.yaml.
   :type images_meta: List[Dict[str, str]]
   :return: Seřazený seznam základních názvů image chybějících v metadatech.
   :rtype: List[str]

.. py:function:: _load_odkaz_cache()

   Načte mezipaměť odkazů DockerHub ze souboru ``docker_images_odkaz_cache.yaml``.

   Pokud soubor neexistuje, vrátí prázdný slovník.

   :return: Slovník ``{název image: URL}`` s dříve uloženými odkazy.
   :rtype: Dict[str, str]

.. py:function:: _save_odkaz_cache(cache)

   Uloží mezipaměť odkazů DockerHub do souboru ``docker_images_odkaz_cache.yaml``.

   :param cache: Slovník ``{název image: URL}`` k uložení.
   :type cache: Dict[str, str]

.. py:function:: _fetch_missing_links(image_keys, cache)

   Načte DockerHub odkazy pouze pro image, které ještě nejsou v mezipaměti, paralelně.

   :param image_keys: Seznam základních názvů image, pro které se mají načíst odkazy.
   :type image_keys: List[str]
   :param cache: Existující mezipaměť odkazů ``{název image: URL}``.
   :type cache: Dict[str, str]
   :return: Aktualizovaná mezipaměť včetně nově načtených odkazů.
   :rtype: Dict[str, str]

.. py:function:: generate_docker_images_rst()

   Vygeneruje dokumentaci Docker image.

   :return: True v případě úspěchu, False v opačném případě.
   :rtype: bool

.. py:function:: _build_section_header(title, description)

   Vytvoří záhlaví sekce RST.

   :param title: Název sekce.
   :type title: str
   :param description: Popis sekce.
   :type description: str
   :return: Seznam řádků RST záhlaví sekce.
   :rtype: List[str]

.. py:function:: _build_image_block(entry, versions, hub_cache)

   Sestaví RST blok pro jeden Docker image.

   :param entry: Metadatový záznam image z docker_images_meta.yaml.
   :type entry: Dict[str, str]
   :param versions: Slovník ``{základní název image: plný tag}`` z docker-compose souborů.
   :type versions: Dict[str, str]
   :param hub_cache: Mezipaměť odkazů DockerHub ``{název image: URL}``.
   :type hub_cache: Dict[str, str]
   :return: Seznam řádků RST bloku pro daný image.
   :rtype: List[str]

.. py:function:: _extract_version(full_tag)

   Extrahuje verzi tagu z plného tagu Docker image.

   :param full_tag: Plný tag image (např. ``redis:8.4.0``).
   :type full_tag: str
   :return: Verze tagu (např. ``8.4.0``), nebo ``latest`` pokud tag není přítomen.
   :rtype: str

.. py:function:: load_json(path)

   Načte a vrátí obsah JSON souboru.

   :param path: Cesta k JSON souboru.
   :type path: Path
   :return: Deserializovaný obsah JSON souboru.
   :rtype: dict

.. py:function:: normalize_repo_url(url)

   Normalizuje URL repozitáře pro zobrazení v dokumentaci.

   Odstraní prefix ``git+``, převede ``git://host/…`` na ``https://host/…``
   (prohlížeče ``git://`` nepodporují spolehlivě) a ořízne příponu ``.git``.

   :param url: Surová URL repozitáře (např. ``git+https://github.com/foo/bar.git``).
   :type url: str
   :return: Normalizovaná URL (např. ``https://github.com/foo/bar``).
   :rtype: str

.. py:function:: npm_package_page_url(package_name)

   Vrátí kanonickou URL stránky balíčku na https://www.npmjs.com/.

   Používá se jako záložní odkaz, když v ``node_modules`` není k dispozici
   ``homepage`` ani ``repository`` (např. při běhu generátoru bez ``npm install``).
   Scoped balíčky (``@scope/name``) se kódují s ``%2F`` místo lomítka v cestě.

   :param package_name: Název balíčku z ``package.json`` (např. ``leaflet`` nebo ``@types/node``).
   :type package_name: str
   :return: URL ve tvaru ``https://www.npmjs.com/package/...``.
   :rtype: str

.. py:function:: parse_preserved_js_library_links(rst_content)

   Z existujícího RST vytáhne mapu ``název balíčku → odkaz`` z generovaného bloku.

   Parsuje řádky ``list-table`` mezi značkami ``.. BEGIN GENERATED NODEJS LIBRARIES``
   a ``.. END GENERATED NODEJS LIBRARIES``. Řádek záhlaví tabulky
   (``Název knihovny``) se přeskočí. Slouží k zachování odkazů při běhu bez
   ``node_modules`` (např. CI), aby se nepřepisovaly platné URL hodnotami
   z :func:`npm_package_page_url`.

   Očekává stejný čtyřřádkový tvar řádků tabulky jako :func:`build_rst_table`;
   ruční zalamování buněk může parsování rozhodit.

   :param rst_content: Obsah souboru ``javascript_knihovny.rst`` (nebo ekvivalent).
   :type rst_content: str
   :return: Slovník ``{název balíčku: URL}`` pro neprázdné odkazy.
   :rtype: Dict[str, str]

.. py:function:: load_dependencies(package_json)

   Načte produkční závislosti ze slovníku ``package.json``.

   :param package_json: Deserializovaný obsah souboru ``package.json``.
   :type package_json: dict
   :return: Slovník ``{název balíčku: verze}`` z pole ``dependencies``.
   :rtype: Dict[str, str]

.. py:function:: load_lock_licenses(lock_file)

   Načte licence balíčků ze souboru ``package-lock.json``.

   Prochází sekci ``packages`` lock souboru a extrahuje pole ``license``
   pro každý záznam pod klíčem ``node_modules/<název>``.

   :param lock_file: Cesta k souboru ``package-lock.json``.
   :type lock_file: Path
   :return: Slovník ``{název balíčku: licence}``.
   :rtype: Dict[str, str]

.. py:function:: read_node_module_metadata(project_root, name)

   Načte licenci a URL domovské stránky balíčku z adresáře ``node_modules``.

   Pokud soubor ``package.json`` daného balíčku neexistuje, vrátí dvojici
   prázdných řetězců. Pole ``license`` může být řetězec nebo objekt s klíčem
   ``type`` (starší formát npm). URL repozitáře je normalizována pomocí
   :func:`normalize_repo_url`.

   :param project_root: Kořenový adresář projektu obsahující ``node_modules``.
   :type project_root: Path
   :param name: Název balíčku (např. ``bootstrap``).
   :type name: str
   :return: Dvojice ``(licence, homepage_url)``.
   :rtype: tuple[str, str]

.. py:function:: collect_libraries(project_root, dependencies, lock_licenses, preserved_links)

   Sestaví seznam Node.js knihoven obohacený o licence a URL.

   Pro každou závislost z ``dependencies`` nejprve hledá licenci v ``lock_licenses``
   (ze souboru ``package-lock.json``), a pokud ji nenajde, čte ji přímo
   ze souboru ``package.json`` v ``node_modules``. Homepage se čte z
   ``node_modules``; chybí-li, použije se dříve uložený odkaz z ``preserved_links``
   (poslední generovaný blok v RST — stabilizuje CI bez ``npm ci``), jinak URL
   stránky balíčku na npm (:func:`npm_package_page_url`). Nový balíček bez
   uloženého odkazu tedy dostane vždy npm URL. Záznamy jsou seřazeny abecedně
   podle názvu balíčku.

   :param project_root: Kořenový adresář projektu obsahující ``node_modules``.
   :type project_root: Path
   :param dependencies: Slovník ``{název balíčku: verze}`` z ``package.json``.
   :type dependencies: Dict[str, str]
   :param lock_licenses: Slovník ``{název balíčku: licence}`` z ``package-lock.json``.
   :type lock_licenses: Dict[str, str]
   :param preserved_links: Volitelně odkazy z existujícího generovaného bloku RST.
   :type preserved_links: Optional[Dict[str, str]]
   :return: Seřazený seznam objektů :class:`JsLibrary`.
   :rtype: List[JsLibrary]

.. py:function:: build_rst_table(rows)

   Sestaví RST blok s tabulkou Node.js knihoven.

   Vygeneruje sekci dokumentace ve formátu ``list-table`` ohraničenou
   značkami ``BEGIN_MARKER`` a ``END_MARKER``, která obsahuje sloupce
   Název knihovny, Verze, Licence a Odkaz.

   :param rows: Seznam záznamů Node.js knihoven k zobrazení v tabulce.
   :type rows: List[JsLibrary]
   :return: Řetězec s RST obsahem tabulky včetně ohraničujících značek.
   :rtype: str

.. py:function:: insert_generated_block(content, block)

   Vloží nebo nahradí generovaný blok mezi značkami v RST obsahu.

   :param content: Původní text souboru (např. ``.rst``).
   :param block: Nový generovaný úsek včetně značek začátku a konce.
   :return: Obsah po vložení bloku, jinak ``block`` předřazený před ``content``.

.. py:function:: generate_js_libraries_rst()

   Vygeneruje tabulku Node.js JavaScript knihoven pro javascript_knihovny.rst.

   Licences berou z ``package-lock.json``; odkazy nejprve z ``node_modules``,
   při jejich absenci z existujícího generovaného bloku v souboru, jinak z
   :func:`npm_package_page_url`. Pro aktualizaci odkazů z metadat balíčků
   (homepage, repository) je potřeba mít nainstalované závislosti (``npm ci``).

   :return: True v případě úspěchu, False v opačném případě.
   :rtype: bool

.. py:function:: main()

   Hlavní funkce pro spuštění generátoru dokumentace.
