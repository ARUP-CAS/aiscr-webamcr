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
11. Hromadný import
12. Rosetta (překlady)

Autentizace a autorizace
-------------------------

Obsahují hlavní a pomocné role, které mohou být přiřazeny uživatelům.

Autentizační token
------------------

Správa autentizačních tokenů pro API.

Asynchronní úlohy (``Celery``)
------------------------------

Přehled a správa asynchronních úloh běžících v systému.

Aplikace ``Core``
-----------------

Odstávky systému
~~~~~~~~~~~~~~~~

Obsahuje nastavení plánované odstávky systému.

Záznam obsahuje:

* Od kdy se má zobrazovat informativní hláška na portálu
* Na kdy je odstavka plánována (hodinu před ní se zakáže přihlašování (text je nastavován v Translations) a začne uživatele automaticky odhlašovat)
* Status jestli je odstavka aktivní/neaktivní
* CS a EN texty pro zobrazení přihlášenému uživateli
* CS a EN texty v případě odstavky pro login page a pro oznámení samostatně
* CS a EN texty pro zobrazení o blížící se odstávce

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
* Na listu je možné filtrovat podle ``is_staff``, ``is_active``, ``organizace`` a přiděleného oprávnění
* Hodnota ``is_staff`` společně s rolí ``Administrátor`` určuje, zda má uživatel přístup do administrátorského rozhraní
* Hodnota ``is_active`` značí, zda je uživatel aktivní (může se přihlásit)


Správa repozitáře
-----------------

Obsahuje možnost hromadné aktualizace metadat ukládaných v repozitáři Fedora. Jako vstup slouží CSV soubor s identifikátory záznamů.

Správa PID
----------

Obsahuje možnost hromadné změny DOI a IGSN. Jako vstup slouží CSV soubor s identifikátory záznamů.

Rosetta (Translations)
----------------------

* Přechod do části aplikace kde je možné upravovat překlady jednotlivých textových klíčů používaných v aplikaci
* Obsahuje samostatný soubor s definicí pro každý jazyk aplikace
* Po kliknutí na soubor jazyka se zobrazí editovací tabulka v které je možné editovat překlad
* Po uložení překladu se automaticky pregenerují soubory pro překlad, které používá aplikace
* Překlady je možné importovat a exportovat pomocí standardních PO souborů
