CORE permission_validation
==========================

Modul permission_validation.

Přehled modulu
--------------

Nedestruktivní kontrola zdrojové matice uživatelských oprávnění.

Třídy
------

.. py:class:: RouteException

   Přesná výjimka routy s uvedením existující ochrany a staré adresy.


.. py:class:: PolicyIssue

   Jedna chyba zdrojové matice nebo pokrytí routy.

   **Metody:**

   .. py:method:: __str__()

      Vrátí chybu s číslem řádku a názvem sloupce, pokud jsou známé.


.. py:class:: PermissionPolicyError

   Souhrn chyb zabraňujících importu matice oprávnění.

   **Metody:**

   .. py:method:: __init__()

      Uloží všechny chyby pro příkaz i administrační rozhraní.


.. py:class:: PermissionRecord

   Připravené oprávnění, které dosud nebylo zapsáno do databáze.


Funkce
------

.. py:function:: _text(value)

   Převede prázdnou buňku na prázdný řetězec a ostatní buňky ořízne.

.. py:function:: load_permission_sheet(docfile)

   Načte a normalizuje hlavičky CSV nebo listu XLSX bez změny databáze.

   :param docfile: Otevřený soubor s atributem ``name``.
   :return: Dvojice normalizovaného DataFrame a čísla prvního datového řádku.
   :raises PermissionPolicyError: Pokud soubor nebo jeho hlavička nejsou platné.

.. py:function:: route_patterns(resolver)

   Vrátí klíče rout ve stejném tvaru jako ``resolver_match.route``.

   :param resolver: Volitelný kořenový resolver pro izolované testy.
   :return: Množina všech vzorů včetně rout adminu a debug toolbaru.

.. py:function:: _address(row)

   Sestaví adresu stejně jako existující import, včetně kořenové cesty.

   :param row: Řádek matice obsahující sloupce aplikace a URL.
   :return: Adresa uložená v oprávnění.

.. py:function:: _parts(value)

   Rozdělí podmínku do alternativ při zachování prázdných položek.

   :param value: Hodnota buňky matice.
   :return: Seznam alternativ podmínky.

.. py:function:: _parse_role(row, row_number, role, address, action)

   Připraví všechny alternativy jedné role nebo vrátí jejich chyby.

   :param row: Řádek zdrojové matice.
   :param row_number: Číslo řádku ve zdrojovém souboru.
   :param role: Označení role B–E.
   :param address: Adresa uložená v oprávnění.
   :param action: Pojmenovaná akce nebo ``None``.
   :return: Připravené záznamy a chyby zpracování dané role.

.. py:function:: invalid_literal_actions(source_root, declared_actions)

   Najde neplatné literály v přímých voláních ``check_permissions``.

   :param source_root: Kořenový adresář kontrolovaných Python zdrojů.
   :param declared_actions: Množina povolených pojmenovaných akcí.
   :return: Chyby obsahující neznámé literály a jejich umístění.

.. py:function:: validate_permission_sheet(sheet, first_row, routes, declared_actions, exceptions, source_root)

   Zkontroluje zdrojovou matici a připraví záznamy bez zápisu do databáze.

   :param sheet: DataFrame s normalizovanými sloupci ``POLICY_COLUMNS``.
   :param first_row: Číslo prvního datového řádku ve zdrojovém souboru.
   :param routes: Volitelná množina rout pro izolované testy.
   :param declared_actions: Volitelná množina deklarovaných akcí.
   :param exceptions: Volitelné přesné výjimky rout.
   :param source_root: Kořen Python zdrojů pro kontrolu literálů volání.
   :return: Dvojice připravených záznamů a všech nalezených chyb.

.. py:function:: validate_permission_file(docfile)

   Načte a zkontroluje soubor vůči skutečným routám a deklarovaným akcím.

   :param docfile: Otevřený CSV nebo XLSX soubor matice.
   :return: Normalizovaná tabulka a připravené záznamy oprávnění.
   :raises PermissionPolicyError: Pokud soubor nebo jeho pravidla nejsou platné.
