Skript generate_selenium_test_docs
==================================

Dokumentace skriptu ``docs/generate_selenium_test_docs.py``.

Přehled modulu
--------------

Generátor dokumentace Selenium testů z Google‑style docstringů.

Pravidla:
- Každá testovací metoda Selenium (funkce začínající na `test_`) musí mít docstring.
- Docstring musí obsahovat alespoň sekce `Steps:` a `Expected:` (neprázdné).
- Testy se grupují podle Django appky (adresář před `/tests/`) a řadí podle čísla testu.
- Výstup do RST:
(A) Přehledová tabulka s odkazy na jednotlivé testy (bez sloupce „popis“ – popis je v tooltipu),
(B) detailní textová dokumentace ke každému testu.

Přehledová tabulka:
- Test č.
- Modul
- Uživ. role (pokud je rolí více, každá se vypíše na vlastní řádek)
- Název (odkaz; krátký popis se zobrazí po najetí myší)

Doporučený formát docstringu (Google‑style):


**def test_001_neco(self):**

- Uživatel je přihlášen.
- Libovolná data, která pomůžou test reprodukovat.
1. Udělej toto
2. Udělej tamto
- Něco se stane

**Poznámky:**

- Volitelné poznámky
"""

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

   :return: Vrací hodnotu typu ``Path`` (vybranou hodnotu z kolekce).

.. py:function:: _is_ignored_path(p)

   Vrátí True, pokud cesta patří do adresářů, které při hledání ignorujeme.

   Typicky `.git`, virtuální prostředí, cache, node_modules apod.

   :param p: Parametr ``p`` předává se do volání ``set()``, pracuje se s atributy ``parts``.
   :return: Vrací hodnotu typu ``bool`` (výsledek volání ``any()``).

.. py:function:: _find_rst_file(root)

   Najde cílový RST soubor `selenium_testy.rst`.

   Nejdřív zkusí preferovanou cestu (docs/source/09_testovani/selenium_testy.rst),
   potom prohledá repozitář. Když soubor nenajde, vyhodí `FileNotFoundError`.

   :param root: Parametr ``root`` pracuje se s atributy ``rglob``.
   :return: Vrací hodnotu typu ``Path``; podle větve může jít o: proměnná ``path``, proměnná ``c``.
   :raises FileNotFoundError: Vyvolá se s textem "Nenalezen soubor selenium_testy.rst (zkontroluj umístění v repozitáři).".

.. py:function:: _iter_test_files(root)

   Vyhledá Python soubory se Selenium testy v repozitáři.

   Hledá `test_selenium.py` v adresářích obsahujících segment `tests` a ignoruje
   typické „šumové“ adresáře (venv, node_modules, …).

   :param root: Parametr ``root`` pracuje se s atributy ``rglob``.
   :return: Vrací hodnotu typu ``List[Path]`` (výsledek volání ``sorted()``).

.. py:function:: _get_app_name(file_path)

   Určí název Django appky podle cesty k souboru.

   Jako appku bere adresář bezprostředně před segmentem `tests`.

   :param file_path: Parametr ``file_path`` předává se do volání ``list()``, pracuje se s atributy ``parts``.
   :return: Vrací hodnotu typu ``str``; podle větve může jít o: str, vybranou hodnotu z kolekce.

.. py:function:: _module_dotted(root, file_path)

   Převede cestu k Python souboru na tečkovaný importní název modulu.

   Např. `webclient/ez/tests/test_selenium.py` -> `webclient.ez.tests.test_selenium`.

   :param root: Parametr ``root`` předává se do volání ``relative_to()``.
   :param file_path: Parametr ``file_path`` pracuje se s atributy ``relative_to``.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``join()``).

.. py:function:: _extract_test_no(name)

   Vytáhne číslo testu z názvu funkce `test_###_...`.

   Vrací int (např. 24) nebo None, pokud název neodpovídá vzoru.

   :param name: Parametr ``name`` předává se do volání ``match()``.
   :return: Vrací hodnotu typu ``Optional[int]`` (hodnotu podle větve zpracování).

.. py:function:: _split_summary_and_rest(doc)

   Rozdělí docstring na první řádek (summary) a zbytek.

   - Summary = první neprázdný řádek docstringu.
   - Rest = zbytek textu (bez počátečních/prázdných okrajů).

   :param doc: Parametr ``doc`` předává se do volání ``dedent()``.
   :return: Vrací hodnotu typu ``Tuple[str, str]`` (n-tici).

.. py:function:: _parse_description_and_sections(rest)

   Parsuje zbytek docstringu na „popis“ a sekce.

   Popis je volný text mezi summary a první hlavičkou sekce (např. `Role:`).
   Sekce jsou ve tvaru „NázevSekce:“ na samostatném řádku a obsah je odsazený.

   Vrací dvojici `(description, sections)` kde `sections` mapuje normalizovaný klíč
   (`steps`, `expected`, `role`, …) na text obsahu sekce.

   :param rest: Parametr ``rest`` pracuje se s atributy ``strip``, ``splitlines``, ovlivňuje větvení podmínek.
   :return: Vrací hodnotu typu ``Tuple[str, Dict[str, str]]`` (n-tici).

.. py:function:: _summary_title_or_error(summary, test_no, origin)

   Vrátí 'čistý' title bez 'Test XXX'.

   Současně validuje, že summary začíná 'Test XXX' a že XXX odpovídá
   test_no (pokud je známé).

   :param summary: Parametr ``summary`` předává se do volání ``match()``.
   :param test_no: Parametr ``test_no`` předává se do volání ``ValueError()``, ovlivňuje větvení podmínek.
   :param origin: Parametr ``origin`` předává se do volání ``ValueError()``.
   :return: Vrací hodnotu typu ``str`` (proměnná ``rest``).
   :raises ValueError: Vyvolá se při splnění podmínky ``not m``; nebo při splnění podmínky ``not rest``.

.. py:function:: _validate_unique_test_numbers(all_docs)

   Vrátí seznam chyb, pokud se stejné číslo testu vyskytuje vícekrát.

   Testy bez čísla (test_no is None) ignoruje.

   :param all_docs: Parametr ``all_docs`` slouží jako vstup pro logiku funkce ``_validate_unique_test_numbers``.
   :return: Vrací hodnotu typu ``List[str]`` (proměnná ``errs``).

.. py:function:: _validate(origin, summary, sections, has_docstring, test_no)

   Zkontroluje, že test splňuje povinná pravidla dokumentace.

   Kontroluje:
   - existenci docstringu,
   - existenci summary,
   - že summary začíná `Test XXX ...` a číslo sedí s názvem funkce,
   - povinné sekce `Steps:` a `Expected:`.

   Vrací seznam chybových hlášek.

   :param origin: Parametr ``origin`` předává se do volání ``append()``, ``_summary_title_or_error()``.
   :param summary: Parametr ``summary`` předává se do volání ``_summary_title_or_error()``, pracuje se s atributy ``strip``, ovlivňuje větvení podmínek.
   :param sections: Parametr ``sections`` ovlivňuje větvení podmínek.
   :param has_docstring: Parametr ``has_docstring`` ovlivňuje větvení podmínek.
   :param test_no: Parametr ``test_no`` předává se do volání ``_summary_title_or_error()``.
   :return: Vrací hodnotu typu ``List[str]`` (proměnná ``errs``).

.. py:function:: _rst_title(text, underline)

   Vytvoří reST nadpis (text + podtržení).

   Parametr `underline` je znak použítý jako podtržení (např. '-', '~', '^').

   :param text: Parametr ``text`` předává se do volání ``len()``, vstupuje do návratové hodnoty.
   :param underline: Parametr ``underline`` vstupuje do návratové hodnoty.
   :return: Vrací hodnotu typu ``str`` (hodnotu podle větve zpracování).

.. py:function:: _app_heading(app)

   Vytvoří nadpis pro sekci jedné Django appky v RST.

   :param app: Parametr ``app`` předává se do volání ``_rst_title()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``_rst_title()``).

.. py:function:: _test_anchor(app, test_no, fallback_name)

   Vytvoří stabilní RST kotvu (anchor) pro daný test.

   Kotva se skládá z appky, čísla testu a „bezpečné“ části názvu.

   :param app: Parametr ``app`` předává se do volání ``sub()``, pracuje se s atributy ``lower``.
   :param test_no: Parametr ``test_no`` slouží jako vstup pro logiku funkce ``_test_anchor``.
   :param fallback_name: Parametr ``fallback_name`` předává se do volání ``sub()``, pracuje se s atributy ``lower``.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``rstrip()``).

.. py:function:: _first_nonempty_line(s)

   Vrátí první neprázdný řádek ze zadaného textu (ořezaný).

   :param s: Parametr ``s`` slouží jako vstup pro logiku funkce ``_first_nonempty_line``.
   :return: Vrací hodnotu typu ``str``; podle větve může jít o: výsledek volání ``strip()``, str.

.. py:function:: _role_short(sections)

   Vrátí krátký text role (první neprázdný řádek ze sekce Role).

   :param sections: Parametr ``sections`` předává se do volání ``_first_nonempty_line()``, pracuje se s atributy ``get``, vstupuje do návratové hodnoty.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``_first_nonempty_line()``).

.. py:function:: _popis_short(description)

   Vrátí krátký popis (první neprázdný řádek) z description.

   Používá se pro tooltip v přehledové tabulce; delší text zkrátí.

   :param description: Parametr ``description`` předává se do volání ``_first_nonempty_line()``.
   :return: Vrací hodnotu typu ``str``; podle větve může jít o: hodnotu podle větve zpracování, proměnná ``line``.

.. py:function:: _render_detail_for_test(t)

   Vygeneruje detailní (textovou) dokumentaci pro jeden test do RST.

   Výstup obsahuje:
   - kotvu (anchor),
   - nadpis testu,
   - volitelný popis,
   - sekce (Role/Preconditions/TestData/Steps/Expected/Notes),
   - a nakonec „Stav testu“ s cestou na implementaci.

   :param t: Parametr ``t`` předává se do volání ``append()``, ``_rst_title()``, pracuje se s atributy ``anchor``, ``summary``, ovlivňuje větvení podmínek.
   :return: Vrací hodnotu typu ``str`` (výsledek volání ``join()``).

.. py:function:: _render_summary_table(all_docs)

   Vygeneruje přehledovou tabulku testů do RST.

   Tabulka je řazená podle čísla testu. Sloupec „Název“ je odkaz na detail testu
   a krátký popis se zobrazuje jako HTML tooltip při najetí myší.

   Pozn.: funkce používá `.. raw:: html`, protože cílíme pouze na HTML výstup.

   :param all_docs: Parametr ``all_docs`` předává se do volání ``sorted()``.
   :return: Vrací hodnotu typu ``str`` (hodnotu podle větve zpracování).

.. py:function:: _render(all_docs)

   Sestaví celé tělo autogenerované části: přehled + detailní sekce podle appky.

   :param all_docs: Parametr ``all_docs`` slouží jako vstup pro logiku funkce ``_render``.
   :return: Vrací hodnotu typu ``str`` (hodnotu podle větve zpracování).

.. py:function:: _replace_autoblock(original, generated)

   Nahradí autogenerovaný blok mezi START/END markerem v `selenium_testy.rst`.

   Pokud značky chybí, vyhodí `RuntimeError`.

   :param original: Parametr ``original`` pracuje se s atributy ``split``, ovlivňuje větvení podmínek.
   :param generated: Parametr ``generated`` pracuje se s atributy ``rstrip``.
   :return: Vrací hodnotu typu ``str`` (hodnotu podle větve zpracování).
   :raises RuntimeError: Vyvolá se při splnění podmínky ``START_MARKER not in original or END_MARKER not in original``.

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
