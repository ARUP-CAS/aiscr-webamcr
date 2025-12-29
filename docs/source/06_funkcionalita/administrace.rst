Administrace
============

Administrace se nachází na URL ``/admin``.

Obsahuje následující položky:

1. Autentizace a autorizace
2. Autentizační token
3. Asynchronní úlohy (``Celery``)
4. Aplikace ``Core``
5. Aplikace ``Dokument``
6. Aplikace ``Heslar``
7. Naplánované úlohy
8. Aplikace ``Uzivatel``
9. Správa repozitáře
10. Správa PID
11. Rosetta (překlady)

Autentizace a autorizace
-------------------------

Obsahují hlavní role, které mohou být přiřazeny uživatelům.

Autentizační token
------------------

Správa autentizačních tokenů pro API přístup.

Asynchronní úlohy (``Celery``)
------------------------------

Přehled a správa asynchronních úloh běžících v systému.

Aplikace ``Core``
-----------------

Odstavky systému
~~~~~~~~~~~~~~~~

Obsahují plánované a historické odstavky systému.

Záznam obsahuje:

* Od kdy se má zobrazovat informativní hláška na portálu
* Na kdy je odstavka plánována (hodinu před ní se zakáže přihlašování (text je nastavován v Translations) a začne uživatele automaticky odhlašovat)
* Status jestli je odstavka aktivní/neaktivní
* EN a CS texty pro zobrazení přihlášenému uživateli
* EN a CS texty v případě odstavky pro login page a pro oznámení samostatně

Aplikace Dokument
-----------------

Obsahuje správu záznamů modelu ``Lety``.

Aplikace Heslar
---------------

Umožňuje spravovat záznamy následujících modelů:

- ``Heslar``
- ``HeslarDatace``
- ``HeslarDokumentTypMaterial``
- ``HeslarHierarchie``
- ``HeslarNazev``
- ``HeslarOdkaz``
- ``RuianKatastr``
- ``RuianKraj``
- ``RuianOkres``

Naplánované úlohy
-----------------

Správa naplánovaných úloh a cronů v systému pomocí Celery.

Clocked
~~~~~~~

Definice jednorázvových úloh spuštěných v konkrétní čas.

* Možnost přidat nový záznam
* Možnost upravit existující záznam

Crontabs
~~~~~~~~

Definice opakujících se úloh podle cron syntaxe (minuta, hodina, den v měsíci, měsíc, den v týdnu).

* Možnost přidat nový záznam
* Možnost upravit existující záznam

Intervals
~~~~~~~~~

Definice úloh opakujících se v pravidelných intervalech (každých X sekund/minut/hodin/dní).

* Možnost přidat nový záznam
* Možnost upravit existující záznam

Periodic tasks
~~~~~~~~~~~~~~

Správa periodických úloh, které kombinují task (úlohu) s časovým plánem (Clocked, Crontabs, Intervals nebo Solar events).

* Možnost přidat nový záznam
* Možnost upravit existující záznam

Solar events
~~~~~~~~~~~~

Definice úloh spouštěných podle slunečních událostí (východ slunce, západ slunce, atd.).

Aplikace Uzivatel
-----------------

Umožňuje spravovat záznamy následujících modelů:

- ``AuthUser``
- ``Organizace``
- ``Osoba``

Users
~~~~~

* Obsahují data z DB tabulky ``auth_user``
* List se zobrazuje jako seznam tvořen sloupci ``email``, ``is_staff``, ``is_active``, ``organizace``, ``ident_cely``
* Na listu je možné filtrovat podle ``is_staff``, ``is_active``, ``organizace``
* Záznamy jsou seřazeny podle pole ``email``
* Je možné vyhledávání fulltext v poli ``email``
* Každý záznam je možné upravit/smazat. Nebo je možné přidat nový záznam
* Hodnota ``is_staff`` určuje, zda má uživatel přístup do administrátorského rozhraní
* Hodnota ``is_active`` se změní na ``True`` poté, co proběhne potvrzení e-mailové adresy


Správa repozitáře
-----------------

Obsahuje možnost hromadné aktualizace metadat.

Správa PID
----------

Obsahuje možnost hromadné změny DOI a IGSN.

Rosetta (Translations)
----------------------

* Obsahuje překlik do části aplikace kde je možné upravovat překlady aplikace
* Část aplikace obsahuje 1 soubor pro každý jazyk aplikace
* Po kliknutí na soubor jazyku se zobrazí editovací tabulka v které je možné editovat překlad
* Po uložení překladu se automaticky pregenerují soubory pro překlad, které používá aplikace
