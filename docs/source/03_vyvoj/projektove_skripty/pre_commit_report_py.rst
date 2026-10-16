Skript pre_commit_report.py
===========================

Automaticky generovaná dokumentace skriptu ``scripts/pre_commit_report.py``.

Přehled modulu
--------------

Zachytí staged změny CI a vykreslí stejné údaje ve všech reportech.

Reporty žijí v RUNNER_TEMP mimo stageované soubory. Změny se zachytí po hookách;
vykreslení po publikaci doplní její výsledek bez opakovaného čtení diffu.
Metadata workflow a diagnostický text se předávají pouze přes proměnné prostředí.

Funkce
------

.. py:function:: git_output()

   Načte údaje indexu bez shellové interpolace a závislosti na locale.

   :param args: Další argumenty příkazu ``git diff --cached --find-renames``.
   :return: Výstup diffu dekódovaný jako UTF-8 se zachováním neplatných bajtů pomocí surrogateescape.
   :raises subprocess.CalledProcessError: Pokud Git nedokáže přečíst staged diff.

.. py:function:: parse_changes(names, numstat)

   Spojí NUL záznamy názvů, stavů a počtů řádků včetně přejmenování.

   :param names: Výstup ``git diff --name-status -z`` pro zachycený index.
   :param numstat: Výstup ``git diff --numstat -z`` pro tentýž index.
   :return: Seznam změn s cestami, stavy a počty řádků; binární soubory mají počty ``None``.

.. py:function:: write_json(path, record)

   Uloží čitelný snapshot beze ztráty neobvyklých znaků v cestách Gitu.

   :param path: Cílový soubor JSON mimo stageované soubory.
   :param record: Zachycené změny, výsledky kroků a metadata reportu.

.. py:function:: capture(path)

   Zachytí staged změny a provedené operace před commitem oprav.

   :param path: Soubor JSON ve kterém se snapshot uchová pro reporty po publikaci.
   :return: Snapshot výsledků workflow a změn indexu; při neúspěšném stage je seznam změn prázdný.

.. py:function:: inline(value)

   Uzavře cestu nebo větev tak, aby její znaky nezměnily Markdown.

   :param value: Doslovný název souboru, větve nebo režimu pro report.
   :return: Inline blok kódu s bezpečným oddělovačem a escapovanými řídicími znaky.

.. py:function:: fenced(value)

   Zachová doslovný diagnostický text včetně vložených značek bloku kódu.

   :param value: Víceřádkový diagnostický výstup hooku.
   :return: Blok kódu s oddělovačem delším než značky obsažené v diagnostice.

.. py:function:: diagnostic_section(title, value, limit)

   Omezí velikost diagnostiky a konec logu zobrazí ve sbalitelné sekci.

   :param title: Název diagnostiky; konec logu zachovává poslední znaky místo prvních.
   :param value: Doslovný text hooku, který se vloží do bezpečně ohraničeného bloku kódu.
   :param limit: Zbývající rozpočet sekce v bajtech UTF-8 včetně značek a zprávy o zkrácení.
   :return: Sekce Markdown v rámci rozpočtu nebo prázdný řetězec při nedostatku místa.

.. py:function:: processing_failures(record)

   Najde selhané či zrušené kroky zpracování odděleně od výsledku hooků.

   :param record: Snapshot obsahující výsledky kroků workflow v položce ``outcomes``.
   :return: Názvy kroků se stavem ``failure`` nebo ``cancelled``.

.. py:function:: result_description(record)

   Popíše výsledek bez příslibu, že staged opravy vyřešily všechna selhání.

   :param record: Snapshot změn, výsledků zpracování, hooků a publikace.
   :return: Stavová zpráva rozlišující selhání, navržené opravy a dokončení bez změn.

.. py:function:: staged_section(record)

   Popíše pouze soubory v zachyceném snapshotu indexu.

   :param record: Snapshot se seznamem změn a příznakem dokončeného zachycení indexu.
   :return: Sekce Markdown se soubory, typy změn a počty řádků nebo vysvětlením chybějících změn.

.. py:function:: common_report(record)

   Vykreslí společné údaje pro popis PR, komentář a summary.

   :param record: Snapshot s metadaty běhu, výsledky operací, změnami a diagnostikou.
   :return: Společný report v Markdown včetně dostupného odkazu na opravné PR.

.. py:function:: render(record, output_dir)

   Použije jeden report bez samostatných kopií jeho údajů pro jednotlivé výstupy.

   :param record: Snapshot použitý pro všechny tři reporty bez opětovného čtení diffu.
   :param output_dir: Adresář pro soubory popisu PR, sticky komentáře a Actions summary.

.. py:function:: update_publication(record)

   Doplní výsledky publikace bez změny snapshotu diffu.

   :param record: Snapshot upravený na místě podle výsledku publikace a URL opravného PR z prostředí.

.. py:function:: main()

   Zachytí změny jednou, vykreslí report před i po publikaci a vrátí stav checku.

   :return: Kód 0 při dokončeném příkazu nebo 1, pokud příkaz ``check`` zjistí selhání běhu.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/pre_commit_report.py
   :language: python
   :linenos:
