Skript generate_selenium_test_docs
==================================

Dokumentace skriptu ``docs/generate_selenium_test_docs.py``.

Třídy
------

.. py:class:: TestDoc

   Třída `TestDoc` v modulu `docs.generate_selenium_test_docs`.

   Zapouzdřuje související data a chování v rámci dané části aplikace.


Funkce
------

.. py:function:: _repo_root_from_script()

   Vrátí kořen repozitáře odvozený z umístění tohoto skriptu.

   Předpoklad: skript leží v `<repo>/docs/...`, takže kořen je o dvě úrovně výš.

.. py:function:: _is_ignored_path(p)

   Vrátí True, pokud cesta patří do adresářů, které při hledání ignorujeme.

   Typicky `.git`, virtuální prostředí, cache, node_modules apod.

.. py:function:: _find_rst_file(root)

   Najde cílový RST soubor `selenium_testy.rst`.

   Nejdřív zkusí preferovanou cestu (docs/source/09_testovani/selenium_testy.rst),
   potom prohledá repozitář. Když soubor nenajde, vyhodí `FileNotFoundError`.

.. py:function:: _iter_test_files(root)

   Vyhledá Python soubory se Selenium testy v repozitáři.

   Hledá `test_selenium.py` v adresářích obsahujících segment `tests` a ignoruje
   typické „šumové“ adresáře (venv, node_modules, …).

.. py:function:: _get_app_name(file_path)

   Určí název Django appky podle cesty k souboru.

   Jako appku bere adresář bezprostředně před segmentem `tests`.

.. py:function:: _module_dotted(root, file_path)

   Převede cestu k Python souboru na tečkovaný importní název modulu.

   Např. `webclient/ez/tests/test_selenium.py` -> `webclient.ez.tests.test_selenium`.

.. py:function:: _extract_test_no(name)

   Vytáhne číslo testu z názvu funkce `test_###_...`.

   Vrací int (např. 24) nebo None, pokud název neodpovídá vzoru.

.. py:function:: _split_summary_and_rest(doc)

   Rozdělí docstring na první řádek (summary) a zbytek.

   - Summary = první neprázdný řádek docstringu.
   - Rest = zbytek textu (bez počátečních/prázdných okrajů).

.. py:function:: _parse_description_and_sections(rest)

   Parsuje zbytek docstringu na „popis“ a sekce.

   Popis je volný text mezi summary a první hlavičkou sekce (např. `Role:`).
   Sekce jsou ve tvaru „NázevSekce:“ na samostatném řádku a obsah je odsazený.

   Vrací dvojici `(description, sections)` kde `sections` mapuje normalizovaný klíč
   (`steps`, `expected`, `role`, …) na text obsahu sekce.

.. py:function:: _summary_title_or_error(summary, test_no, origin)

   Vrátí 'čistý' title bez 'Test XXX'.

   Současně validuje, že summary začíná 'Test XXX' a že XXX odpovídá
   test_no (pokud je známé).

.. py:function:: _validate_unique_test_numbers(all_docs)

   Vrátí seznam chyb, pokud se stejné číslo testu vyskytuje vícekrát.

   Testy bez čísla (test_no is None) ignoruje.

.. py:function:: _validate(origin, summary, sections, has_docstring, test_no)

   Zkontroluje, že test splňuje povinná pravidla dokumentace.

   Kontroluje:
   - existenci docstringu,
   - existenci summary,
   - že summary začíná `Test XXX ...` a číslo sedí s názvem funkce,
   - povinné sekce `Steps:` a `Expected:`.

   Vrací seznam chybových hlášek.

.. py:function:: _rst_title(text, underline)

   Vytvoří reST nadpis (text + podtržení).

   Parametr `underline` je znak použítý jako podtržení (např. '-', '~', '^').

.. py:function:: _app_heading(app)

   Vytvoří nadpis pro sekci jedné Django appky v RST.

.. py:function:: _test_anchor(app, test_no, fallback_name)

   Vytvoří stabilní RST kotvu (anchor) pro daný test.

   Kotva se skládá z appky, čísla testu a „bezpečné“ části názvu.

.. py:function:: _first_nonempty_line(s)

   Vrátí první neprázdný řádek ze zadaného textu (ořezaný).

.. py:function:: _role_short(sections)

   Vrátí krátký text role (první neprázdný řádek ze sekce Role).

.. py:function:: _popis_short(description)

   Vrátí krátký popis (první neprázdný řádek) z description.

   Používá se pro tooltip v přehledové tabulce; delší text zkrátí.

.. py:function:: _render_detail_for_test(t)

   Vygeneruje detailní (textovou) dokumentaci pro jeden test do RST.

   Výstup obsahuje:
   - kotvu (anchor),
   - nadpis testu,
   - volitelný popis,
   - sekce (Role/Preconditions/TestData/Steps/Expected/Notes),
   - a nakonec „Stav testu“ s cestou na implementaci.

.. py:function:: _render_summary_table(all_docs)

   Vygeneruje přehledovou tabulku testů do RST.

   Tabulka je řazená podle čísla testu. Sloupec „Název“ je odkaz na detail testu
   a krátký popis se zobrazuje jako HTML tooltip při najetí myší.

   Pozn.: funkce používá `.. raw:: html`, protože cílíme pouze na HTML výstup.

.. py:function:: _render(all_docs)

   Sestaví celé tělo autogenerované části: přehled + detailní sekce podle appky.

.. py:function:: _replace_autoblock(original, generated)

   Nahradí autogenerovaný blok mezi START/END markerem v `selenium_testy.rst`.

   Pokud značky chybí, vyhodí `RuntimeError`.

.. py:function:: main()

   Hlavní vstup skriptu.

   - najde test soubory,
   - vyparsuje docstringy,
   - provede validace (včetně jedinečnosti čísel testů),
   - vygeneruje RST a případně přepíše autogenerovanou část.

   Návratové kódy:
   - 0: vše OK a bez změn,
   - 1: chyba validace nebo došlo k přegenerování souboru (je třeba `git add`),
   - 2: zásadní problém (nenalezeny soubory).

   :return: Návratový kód procesu generování dokumentace selenium testů.
