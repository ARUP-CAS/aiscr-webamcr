.. _automaticke-testy:

Automatické testy
=================

Ke spuštění testů slouží vývojový server (.24). Před spuštěním testů je nutné nasadit aktuální nebo požadovanou verzi aplikace WebAMČR.
To se provede pomocí skriptu ``./scripts/test_deploy.sh``. Skript se při spuštění také zeptá, zda má stáhnout aktuální verzi WebAMČR origin/dev.
Po nasazení verze je potřeba cca 5 minut počkat než se WebAMČR rozběhne
Testy je možné spustit následujícím příkazem 

::

./scripts/start_selenium_tests.sh

skript má následující parametry:
 * `-f`          Provede neúspěšné testy v tabulce 
 * `-a`          Provede všechny testy (výchozí)
 * `-t cislo`    Provede test zadaneho čísla
 * `-b`          Spustí všechny testy na pozadí, výstup se uloží do /opt/selenium_test/test.log a run.log
 * `-h`          Zobrazí nápovědu
  
Výsledky testů se uloží do /opt/selenium_test/results.xlsx. 

V tabulce se ukládá:
 * `index` Pořadové číslo testu
 * `date` Datum a čas provedení testu
 * `test name` Jméno testu
 * `result` Výsledek testu (OK, Fail nebo Error)

V  adresáři ``/opt/selenium_test/`` se ukládají také screenshoty každého testu.

**Pozn.** Pokud uživatel přeruší probíhající test, je potřeba před spuštěním nového testu počkat několik minut, než se ukonči Selenium.


Vyhodnocení výsledků testu
--------------------------

K vyhodnocení běhu testu slouží aplikace Kibana. V ní je připraven
pohled ``Test logs query`` (zobrazuje logové zprávy z půběhu testu).

.. image:: images/automaticke_testy_test_log_view.png
   :alt: dashboard

Dále jsou k dispozici dashboardy ``Test Errors`` (zobrazuje chyby a
varování) a ``Test Overview`` (statistika chybových zpráv testu).

.. image:: images/automaticke_testy_dashboard.png
   :alt: dashboard

Požadované vlastnosti testovacího scénáře
-----------------------------------------

Požadované vlastnosti testovacího scénáře jsou následující (vychází z
článku `How to Write Test Cases in Software Testing with
Examples <https://www.guru99.com/test-case.html>`__:

-  testovací scénář by měl být jednoduchý a měl by testovat max. jednu
   stránku či jednu sadu funkcí,
-  testovací scénář musí být napsán a vytvořen z pohledu uživatele, tj.
   musí přesně simulovat kroky, které by prováděl uživatel, pokud by
   chtěl dosáhnout daného výsledku,
-  testy by se neměly překrývat,
-  u každého testu musí být specifikována alespoň jedna metrika
   úspěšnosti průběhu.

Postup vytvoření kódu testu
---------------------------

Pro scénář je třeba připravit sadu vstupních dat a kontrolní výstup.

Struktura popisu scénáře
------------------------

Popis scénáře by měl obsahovat následující:

-  ID scénáře,
-  stručný popis scénáře,
-  uživatelská role,
-  předpoklady pro průběh testu (pokud jsou),
-  uživatelské kroky, které scénář simuluje,
-  testovací data,
-  očekávané výsledky (tj. metriky, které oveřují úspěšný průběh testu).

Scénáře jsou seskupeny podle jednotlivých aplikací.

Core
----

Test 001 Přihlášení do AMČR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Testuje přihlášení uživatele.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Uživatelské kroky
^^^^^^^^^^^^^^^^^

1. Vyplnění formuláře na titulní stránce

Testovací data
^^^^^^^^^^^^^^

uživatelské jméno a heslo

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

1. Uživatel je přesměrován na stránku s titulkem AMČR Homepage

Stav testu
^^^^^^^^^^

Implementován v
``core.tests.test_selenium.CoreSeleniumTest.test_001_core_001``.

Projekt
-------

Test 002 Otevření tabulky projekty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Testuje tabulku s projekty. Ověřuje, zda funguje řazení podle
jednotlivých sloupců a zobrazení/skrývání sloupců.

Využívá metodu ``_check_column_hiding``.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

1. Uživatel klikne na menu Projekty -> Vybrat projekty
2. Uživatel kliká na záhlaví jednotlivých sloupců
3. Uživatel skyje a znovu zobrazí jednotlivé sloupce pomocí výsuvného
   menu

Testovací data
^^^^^^^^^^^^^^

*Žádná*

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

1. Po kliknutí na název sloupce je do adresy stránky přidán řetězec
   ``sort=sloupec``
2. Po skytí sloupce zmizí název sloupce ze záhlaví
3. Po zobrazení sloupce je sloupec v záhlaví tabulky

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektSeleniumTest.test_002_projekt_001``.

Test 003 Zapsání projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání projektu na stránce ``/projekt/zapsat``. Test simuluje
zadání validních data měl by končit zapsáním projektu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Jsou vložena kompletní data o katastrech, okresech a krajích.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

1. Uživatel klikne na menu Projekty -> Zapsat
2. Uživatel vyplní data do formuláře a kliknutím na mapu vybere hlavní
   katastr
3. Uživatel klikne na tlačítko Uložit

Testovací data
^^^^^^^^^^^^^^

+-----------------------+---------------------------------------------+
| Field                 | Value                                       |
+=======================+=============================================+
| typ_projektu          | záchranný                                   |
+-----------------------+---------------------------------------------+
| id_podnet             | test                                        |
+-----------------------+---------------------------------------------+
| id_lokalizace         | test                                        |
+-----------------------+---------------------------------------------+
| id_parcelni_cislo     | test                                        |
+-----------------------+---------------------------------------------+
| id_planovane_zahajeni | dynamicky vložené datum (dnes + dva dny až  |
|                       | dnes + pět dní)                             |
+-----------------------+---------------------------------------------+
| id_oznamovatel        | test                                        |
+-----------------------+---------------------------------------------+
| id_odpovedna_osoba    | test                                        |
+-----------------------+---------------------------------------------+
| id_adresa             | test                                        |
+-----------------------+---------------------------------------------+
| id_telefon            | +420123456789                               |
+-----------------------+---------------------------------------------+
| id_email              | test@example.com                            |
+-----------------------+---------------------------------------------+

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Pole ``id_oznamovatel`` je povoleno.
-  Pole ``id_odpovedna_osoba`` je povoleno.
-  Pole ``id_adresa`` je povoleno.
-  Pole ``id_telefon`` je povoleno.
-  Pole ``id_email`` je povoleno.
-  Po kliknutí na tlačítko Uložit je v databázi o 1 projekt více

Stav testu
''''''''''

Implementován v
``projekt.tests.test_selenium.ProjektZapsatSeleniumTest.test_003_projekt_zapsat_p_001``.

Test 006 Schválení projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test schválení projektu

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Archivář je přihlášen.
- Projekt ve stavu Px0 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Archivář schválí projekt.

Testovací data
^^^^^^^^^^^^^^

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Změní se označení projektu.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektZapsatSeleniumTest.test_006_schvaleni_projektu_p_001``.

Test 007 Zahájení výzkumu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zahájení výzkumu u projektu ve stavu P2 s pozitivním výsledkem. Měl by končit posunem projektu do stavu P3

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A2.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A2.

Testovací data
^^^^^^^^^^^^^^

================= =====================================
Field ID          Value
================= =====================================
id_datum_zahajeni (date calculated: -5 days from today)
================= =====================================

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A3
-  Datum zahájení projektu odpovídá testovacím datům.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektZahajitVyzkumSeleniumTest.test_007_projekt_zahajit_vyzkum_p_001``.

Test 008 Ukončení výzkumu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test ukončení výzkumu u projektu ve stavu P3 s pozitivním výsledkem. Měl by končit posunem projektu do stavu P4.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A3.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A3.

Testovací data
^^^^^^^^^^^^^^

================= =====================================
Field ID          Value
================= =====================================
id_datum_ukonceni (date calculated: -1 days from today)
================= =====================================

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A4.
-  Datum zahájení projektu odpovídá testovacím datům.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektUkoncitVyzkumSeleniumTest.test_008_projekt_ukoncit_vyzkum_p_001``.

Test 009 Ukončení výzkumu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test ukončení výzkumu u projektu ve stavu P3 s negativním výsledkem. Měl by končit neposunutím projektu do stavu P4.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A3.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A3.

Testovací data
^^^^^^^^^^^^^^

================= =====================================
Field ID          Value
================= =====================================
id_datum_ukonceni (date calculated: 90 days from today)
================= =====================================

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt zůstal ve stavu A3.
-  Zobrazena chyba ``Datum nesmí být dále než měsíc v budoucnosti``.

Stav testu
''''''''''

Implementován v
``projekt.tests.test_selenium.ProjektUkoncitVyzkumSeleniumTest.test_009_projekt_ukoncit_vyzkum_n_001``.

Test 010 Uzavření projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test uzavření projektu ve stavu P4 s pozitivním výsledkem. Měl by končin posunem projektu do stavu P5.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A4, který má projektovou akci.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A4.

Testovací data
^^^^^^^^^^^^^^

Žádná.

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přestunut do stavu A5.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektUzavritSeleniumTest.test_010_projekt_uzavrit_p_001``.

Test 011 Uzavření projektu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test uzavření projektu ve stavu P4 s negativním výsledkem. Měl by končin neposunutím projektu do stavu P5.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A4, který nemá projektovou akci.


Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A4.

Testovací data
^^^^^^^^^^^^^^

Žádná.

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt zůstal ve stavu A4.
-  Zobrazena chyba ``Projekt musí mít alespoň jednu projektovou akci``.

Stav testu
''''''''''

Implementován v
``projekt.tests.test_selenium.ProjektUzavritSeleniumTest.test_011_projekt_uzavrit_n_001``.

Test 012 Archivace projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace projektu ve stavu P5 s pozitivním výsledkem. Scénář končí pousnem projektu do stavu P6,

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A5, který má archivovanou projektovou akci.


Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A5.


Testovací data
^^^^^^^^^^^^^^

Žádná.


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt je přesunut do stavu A6.


Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektArchivovatSeleniumTest.test_012_projekt_archivovat_p_001``.


Test 013 Archivace projektu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace projektu ve stavu P5 s negativním výsledkem. Scénář končí nepousnutím projektu do stavu P6,

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A5, který má nearchivovanou projektovou
   akci.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A5.

Testovací data
^^^^^^^^^^^^^^

Stejná jako u ``test_projekt_zapsat_p_001``.

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt zůstal ve stavu A5.
-  Zobrazena chyba ``Akce musí být archivovaná``.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektArchivovatSeleniumTest.test_013_projekt_uzavrit_n_001``.

Test 014 Vrácení stavu u archivovaného projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení projektu do stavu P5 s pozitivním výsledkem. Scénář končí posunem do stavu P5.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A6.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A6.

Testovací data
^^^^^^^^^^^^^^

========= =====
Field ID  Value
========= =====
id_reason test
========= =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A5.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVratitSeleniumTest.test_014_projekt_vratit_p_001``.

Test 015 Vrácení stavu u uzavřeného projektu (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení projektu do stavu P4 s pozitivním výsledkem. Scénář končí posunem do stavu P4.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A5.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A5.

Testovací data
^^^^^^^^^^^^^^

========= =====
Field ID  Value
========= =====
id_reason test
========= =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A4.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVratitSeleniumTest.test_015_projekt_vratit_p_002``.

Test 016  Vrácení stavu u ukončeného projektu (pozitivní scénář 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení projektu do stavu P3 s pozitivním výsledkem. Scénář končí posunem do stavu P3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A4.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A4.

Testovací data
^^^^^^^^^^^^^^

========= =====
Field ID  Value
========= =====
id_reason test
========= =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A3.

Stav testu
^^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVratitSeleniumTest.test_016_projekt_vratit_p_003``.

Test 017 Vrácení stavu u zahájeného projektu (pozitivní scénář 4)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení projektu do stavu P2 s pozitivním výsledkem. Scénář končí posunem do stavu P2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A3.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A3.

Testovací data
^^^^^^^^^^^^^^

========= =====
Field ID  Value
========= =====
id_reason test
========= =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A2.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVratitSeleniumTest.test_017_projekt_vratit_p_004``.

Test 018 Vrácení stavu u přihlášeného projektu (pozitivní scénář 5)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení projektu do stavu P2 s pozitivním výsledkem. Scénář končí posunem do stavu A1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A2.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt ve stavu A2.

Testovací data
^^^^^^^^^^^^^^

========= =====
Field ID  Value
========= =====
id_reason test
========= =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A1.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVratitSeleniumTest.test_018_projekt_vratit_p_005``.

Test 19 Navržení zrušení projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test navržení zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A7.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt.


Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt.

Testovací data
^^^^^^^^^^^^^^

======== ==========
Field ID Value
======== ==========
reason   item no. 2
======== ==========

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A7.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektNavrhnoutZrusitSeleniumTest.test_019_projekt_zrusit_p_001``.

Test 020 Navržení zrušení projektu (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test navržení zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A7.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt.

Testovací data
^^^^^^^^^^^^^^

============= ==========
Field ID      Value
============= ==========
reason        item no. 1
id_projekt_id test
============= ==========

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt přesunut do stavu A7.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektNavrhnoutZrusitSeleniumTest.test_020_projekt_zrusit_p_002``.

Test 021 Navržení zrušení projektu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test navržení zrušení projektu s negativním výsledkem. Scénář končí neposunutím projektu do stavu A7.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt s projektovými akcemi.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt s projektovými akcemi.

Testovací data
^^^^^^^^^^^^^^

======== ==========
Field ID Value
======== ==========
reason   item no. 2
======== ==========

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt zůstal ve výchozím stavu.
-  Zobrazena chyba ``Projekt před zrušením nesmí mít projektové akce``.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektNavrhnoutZrusitSeleniumTest.test_021_projekt_zrusit_n_001``.

Test 022 Zrušení projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A8

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

-  Uživatel je přihlášen.
-  Existuje projekt ve stavu A7.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel otevře projekt s projektovými akcemi.

Testovací data
^^^^^^^^^^^^^^

============== =====
Field ID       Value
============== =====
id_reason_text test
============== =====

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Projekt je přesunut do stavu A8.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektZrusitSeleniumTest.test_022_projekt_zrusit_p_001``.

Test 023 Vytvoření projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření projektové akce. Scénář končí vytvořením projektové akce ve stavu A1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^
- Uživatel je přihlášen.
- Projekt je ve stavu P3


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (viz předpoklady)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202111043“ → Vybrat → otevřít projekt
- Kliknout na Vložit další akci (v sekci Archeologické akce)
- Vytvoření akci


Testovací data
^^^^^^^^^^^^^^
Projekt C-202401502

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Vytvoření akce u projektu - v databázi bude o jednu akci více.

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektVytvoreniProjektoveAkce.test_023_projekt_vytvori_akci_p_001``.

Test 145 Test Fedory pro projekty (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dat do Fedory v projektech

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření - projekt zachrany
- Update - projekt
- Update oznamovatel
- Smazat soubor v projektu
- Vytvoření soubor
- Vytvoření projektová akce
- Změna přístupnosti Akce
- Smazání projektové Akce 
- Smazání projektu
- Znovu vytvoření projektové Akce

Testovací data
^^^^^^^^^^^^^^
Projekt C-201121404, X-M-202393246, C-202111043

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory 

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektSeleniumTest.test_145_test_Fedora_projekt_001``.

Test 146 Test Fedory pro projekty (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

test zapsání dat do Fedory v projektech

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář, Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^
- Vytvoření oznámení
- Smazání dokumentu u projektu
- Schválení projektu - změna ident-cely projektu
- Vytvoření průzkumného projektu
- Vytvoření části dokumentu projektu
- Vytvoření PAS
- Změna přístupnosti PAS
- Smazání části dokumentu
- Smazání PAS
- Smazání projektu
- Znovu vytvoření PAS
- Vytvoření části dokumentu - existující dokument


Testovací data
^^^^^^^^^^^^^^

Projekt  C-202209999, C-202210662, M-202302810, C-202114070
Dokument M-TX-194300151



Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory 

Stav testu
^^^^^^^^^^

Implementován v
``projekt.tests.test_selenium.ProjektSeleniumTest.test_146_test_Fedora_projekt_002``.

Akce
----

Test 024 Přidání dokumentační jednotky celek akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D01 typu celek akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která nemá žádnou dokumentační jednotku.


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (viz předpoklady)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202110946“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (C-202110946A).
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ DJ “celek akce”
- Zvolit typ Negativní jednotka “ano”
- Kliknout na “uložit” 

Testovací data
^^^^^^^^^^^^^^
- typ: celek akce
- negativni_jednotka : Ano

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U akce bude vytvořena DJ typu “celek akce” (v databázi je o jednu DJ více).

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_024_pridani_dokumentacni_jednotky_p_001``.

Test 033 Vytvoření projektové akce (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

test ztratil smysl


Test 034 Přidání dokumentační jednotky celek akce (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí nevytvořením dokumentační jednotky D01 typu celek akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která nemá žádnou dokumentační jednotku.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (číslo projektu)
- Projekty → Vybrat → Filtr → ID obsahuje „číslo projektu“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (číslo akce).
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ DJ - ponechat nevyplněno
- Zvolit typ Negativní jednotka “ano”
- Kliknout na “uložit změny” 

Testovací data
^^^^^^^^^^^^^^

Akce C-202401502A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U akce nebude vytvořena DJ typu “celek akce” (v databázi není o jednu DJ více).

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_034_pridani_dokumentacni_jednotky_n_001``.

Test 035 Přidání dokumentační jednotky část akce (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu část akce u projektové akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D02 typu část akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (M-202400005)
- Projekty → Vybrat → Filtr → ID obsahuje „M-202400005“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (M-202400005A).
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ DJ “část akce”
- Zvolit typ Negativní jednotka “ano”
- Kliknout na “uložit změny” 

Testovací data
^^^^^^^^^^^^^^

C-202309552A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U akce bude vytvořena DJ D02 typu “část akce” (v databázi je o jednu DJ více).

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_035_pridani_dokumentacni_jednotky_p_002``.

Test 036 Přidání dokumentační jednotky část akce (negativní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu část akce u projektové akce ve stavu A1. Scénář končí nevytvořením dokumentační jednotky D02 typu část akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202309552)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202309552“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (C-202309552A).
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ DJ “nevyplněno”
- Zvolit typ Negativní jednotka “ano”
- Kliknout na “uložit změny” 

Testovací data
^^^^^^^^^^^^^^

C-202309552

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U akce nebude vytvořena DJ D02 typu “část akce” (v databázi není o jednu DJ více).

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_036_pridani_dokumentacni_jednotky_n_002``.

Test 037 Přidání komponenty k dokumentační jednotce celek akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření komponenty u dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí vytvořením komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (M-202400004)
- Projekty → Vybrat → Filtr → ID obsahuje „M-202400004“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (M-202400004A).
- Kliknout na dokumentační jednotku D01 
- Kliknout na “Další volby” a zvolit ”Přidat komponentu”.
- Zvolit Období “únětická k.”
- Zvolit Areál “sídliště nesp.”.
- Kliknout na “uložit změny” 


Testovací data
^^^^^^^^^^^^^^

C-202309027

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U DJ D01 bude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_037_pridani_komponenty_dokumentacni_jednotky_p_001``.

Test 040 Přidání komponenty k dokumentační jednotce celek akce (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření komponenty u dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí nevytvořením komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202309027)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202309027“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (C-202309027A).
- Kliknout na dokumentační jednotku D01 
- Kliknout na “Další volby” a zvolit ”Přidat komponentu”.
- Zvolit Období “únětická k.”
- Zvolit Areál “zůstane nevyplněno”.
- Kliknout na “uložit změny” 

Testovací data
^^^^^^^^^^^^^^

C-202309027

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U DJ D01 nebude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_040_pridani_komponenty_dokumentacni_jednotky_n_001``.

Test 041  Přidání objektu k pozitivní komponentě (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření objektu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí vytvořením objektu u komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní a obsahuje komponentu K001.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202004814)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202004814“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (C-202004814A).
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Objekty zvolit Druh “(polo)zemnice”.
- V sekci Nálezy a Objekty vyplnit Počet “1”.
- Kliknout na “Uložit změny” 

Testovací data
^^^^^^^^^^^^^^

C-202004814

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_041_pridani_objektu_komponente_p_001``.

Test 042 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření předmětu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí vytvořením předmětu u komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní a obsahuje komponentu K001.


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202004814)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202004814“ → Vybrat → otevřít projekt
- Uživatel otevře akci ve stavu A1 (C-202004814A).
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Předměty zvolit Druh “džbán”.
- V sekci Nálezy a Předměty zvolit Specifikace “keramika nesp.”.
- V sekci Nálezy a Předměty vyplnit Počet “1”.
- Kliknout na “Uložit změny” 

Testovací data
^^^^^^^^^^^^^^

C-202004814

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_042_pridani_predmetu_komponente_p_001``.

Test 043 Smazání objektu u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání objektu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí smazáním objektu.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001
- Objekt “jáma kůlová/sloupová” připojený ke komponentě K001


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projektovou akci ve stavu A1 (X-C-91277520A)
- Projekty → Vybrat → Filtr → ID obsahuje „X-C-91277520“ → Vybrat → otevřít projektovou akci X-C-91277520A
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Objekty u položky “jáma kůlová/sloupová” kliknout na možnost “odstranit”
- Volbu potvrdit

Testovací data
^^^^^^^^^^^^^^

X-C-91277520A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U komponenty K001 bude odebrána položka typu objekt. V databázi bude o jeden objekt méně. Oznámení “Záznam byl úspěšně smazán”

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_043_smazani_objektu_komponente_p_001``.


Test 044 Smazání předmětu u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání předmětu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí smazáním předmětu.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001
- Předmět “doklad umění/kultu” připojený ke komponentě K001

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projektovou akci ve stavu A1 (M-202400926A)
- Projekty → Vybrat → Filtr → ID obsahuje „M-202400926“ → Vybrat → otevřít projektovou akci M-202400926A
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Předměty u položky “doklad umění/kultu” kliknout na možnost “odstranit”
- Volbu potvrdit

Testovací data
^^^^^^^^^^^^^^

X-C-91277520A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U komponenty K001 bude odebrána položka typu předmět. V databázi bude o jeden předmět méně. Oznámení “Záznam byl úspěšně smazán”

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_044_smazani_predmetu_komponente_p_001``.

Test 079 Přidání dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání dokumentu k projektové akci. Scénář končí vytvořením záznamu dokumentu a jeho připojením k projektové akci.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202207641A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202207641A“ → Vybrat → otevřít projekt
- Uživatel otevře akci (C-202207641A).
- V tabulce Dokumenty kliknout na tlačítko “Přidat dokument”
- Uživatel vyplní povinné údaje ve formuláři Dokument
- Klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^

C-202207641A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Bude vytvořen nový záznam typu dokument (v databázi je o jeden dokument více). Tento dokument je připojený k projektové akci C-202207641A 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_079_pridani_dokumentu_projektove_akci_p_001``.

Test 080 Připojení existujícího dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení existujícího dokumentu k projektové akci. Scénář končí vytvořením vazby mezi dokumentem a projektovou akcí.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (C-202207641)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202207641“ → Vybrat → otevřít projekt
- Uživatel otevře akci (C-202207641A).
- V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument”
- Uživatel vyhledá dokument “M-TX-194300114”
- Klikne na tlačítko Připojit

Testovací data
^^^^^^^^^^^^^^

C-202207641
M-TX-194300151

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Je vytvořena vazba mezi dokumentem a projektovou akcí C-202207641A

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001``.

Test 081 Připojení existujícího dokumentu z projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení existujícího dokumentu z projektu k projektové akci. Scénář končí vytvořením vazby mezi dokumentem a projektovou akcí.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt je ve stavu P3
- Projekt obsahuje projektovou akci s připojeným dokumentem
- Projekt obsahuje další projektovou akci ve stavu A1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt ve stavu P3 (M-202400928)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401979“ → Vybrat → otevřít projekt
- Uživatel otevře akci (C-202401979B).
- V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument z projektu”
- Uživatel vyhledá dokument “...”
- Zaškrtne políčko Vybrat a klikne na tlačítko Připojit

Testovací data
^^^^^^^^^^^^^^

C-202401979B

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Je vytvořena vazba mezi dokumentem a projektovou akcí C-202401979B

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001``.

Test 084 Připojení externího zdroje k projektové akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení externího zdroje k projektové akci. Scénář končí vytvořením vazby mezi samostatnou akcí a externím zdrojem.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202301164)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202301164“ → Vybrat → otevřít projekt → otevřít akci „C-202301164A“ 
- V části “Externí zdroje” kliknout na “připojit externí zdroj”
- Uživatel vyhledá identifikátor “X-BIB-1295324”
- Klikne na tlačítko Připojit

Testovací data
^^^^^^^^^^^^^^

C-202301164
X-BIB-1295324

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Je vytvořena vazba mezi projektovou akcí externím zdrojem  „X-BIB-1295324“

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_084_pripojeni_externiho_zdroje_projektove_akci_p_001``.


Test 086 Vytvoření PIAN u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření PIAN k projektové akci.Scénář končí vytvořením nového PIAN připojeného k DJ 01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202401980-D01” kliknout na Další volby → PIAN - vytvořit → vytvořit geometrii PIAN (jak vyřešit v testu?)
- V části nový PIAN nastavit přesnost na hodnotu “odchylka jednotky metrů”

Testovací data
^^^^^^^^^^^^^^

C-202401980

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202401980-D01” je připojen nový PIAN.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_086_vytvoreni_PIAN_projektove_akce_p_001``.

Test 087 Editace PIAN u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test editace PIAN u projektové akci. Scénář končí novu geometrií PIAN u dokumentační jednotky DJ 01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401981A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401981A“ → Vybrat → otevřít projekt → otevřít akci „C-202401981A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202401981A-D01” kliknout na Další volby → PIAN - upravit → upravit geometrii PIAN 

Testovací data
^^^^^^^^^^^^^^

N-1212-000000002
C-202401981A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202401981A-D01” je upravena geometrie připojeného PIAN.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_087_editace_PIAN_projektove_akce_p_001``.

Test 088 Smazání PIAN u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání PIAN u projektové akci. Scénář končí smazáním nepotvrzeného PIAN u dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401981A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401981“ → Vybrat → otevřít projekt → otevřít akci „C-202401981A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202401981A-D01” kliknout na Další volby → PIAN - odpojit → v dialogovém okně “Odpojení PIAN” kliknout na tlačítko “Odpojit”

Testovací data
^^^^^^^^^^^^^^
C-202401981A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202401981A-D01” je smazán nepotvrzený PIAN, v databázi je o 1 PIAN méně. 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_088_smazani_PIAN_projektove_akce_p_001``.

Test 089 Připojení PIAN z mapy u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení PIAN z mapy u projektové akci. Scénář končí připojením existujícího PIAN k dokumentační jednotce D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202401980A-D01” kliknout na Další volby → PIAN - připojit z mapy→ kliknout na PIAN XXX  → kliknout na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

C-202401980

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202401980A-D01” bude vytvořena vazba s PIAN „XXX”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_089_pripojeni_PIAN_projektove_akce_p_001``.

Test 090 Odpojení potvrzeného PIAN u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odpojení potvrzeného PIAN projektové akci. Scénář končí odpojením existujícího PIAN od dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202007232A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202007232“ → Vybrat → otevřít projekt → otevřít akci „C-202007232A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202007232A-D01” kliknout na Další volby → PIAN - odpojit → V dialogovém okně “Odpojení PIAN” kliknout na “Odpojit”

Testovací data
^^^^^^^^^^^^^^

C-202007232A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202007232A-D01” zanikne vazba s PIAN „XXX”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_090_odpojeni_PIAN_projektove_akce_p_001``.

Test 091 Import PIAN k projektové akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test importu PIAN k projektové akci. Scénář končí vytvořením PIAN u dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202309724A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202309724“ → Vybrat → otevřít projekt → otevřít akci „C-202309724A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202309724A-D01” kliknout na Další volby → PIAN - importovat → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
- V části “Nový PIAN” vybrat přesnost “odchylka jednotky metrů” a kliknout “uložit změny”

Testovací data
^^^^^^^^^^^^^^
geom.csv
C-202309724

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202309724A-D01” bude připojen nový PIAN „XXX”. V databázi bude o jeden PIAN více (vznikne vazba s D01). 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_091_import_PIAN_projektove_akce_p_001``.

Test 092 Editace PIAN k projektové akci importem (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test editace PIAN k projektové akci importem. Scénář končí upraveným PIAN u dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202005190)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202005190“ → Vybrat → otevřít projekt → otevřít akci „C-202005190A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202005190A-D01” kliknout na Další volby → PIAN - upravit importem → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
- V části ““Dokumentační jednotka C-202005190A-D01” kliknout na “uložit změny”

Testovací data
^^^^^^^^^^^^^^
C-202005190A
geom.csv

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202005190A-D01” bude upravena geometrie PIAN „XXX”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_092_editace_PIAN_projektove_akce_importem_p_001``.

Test 093 Připojení PIAN k projektové akci podle ID (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení PIAN k projektové akci podel ID. Scénář končí připojením PIAN podle ID u dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka C-202401980A-D01” kliknout na Další volby → PIAN - připojit podle ID
- V části ““Dokumentační jednotka C-202401980A-D01” v poli “PIAN” zadat ID PIAN “P-0134-00000” a kliknout na “uložit změny”

Testovací data
^^^^^^^^^^^^^^
C-202401980
P-0134-00000

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-202401980A-D01” bude připojen PIAN „P-0134-00000”. V databázi bude vytvořena vazba mezi PIAN a dokumentační jednotkou “C-202401980A-D01”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_093_pripojeni_PIAN_projektove_akce_p_001``.

Test 094 Smazání komponenty u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání komponenty u projektové akce. Scénář končí smazáním komponenty K001 u dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojenou komponentu K001.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-201015104A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-201015104“ → Vybrat → otevřít projekt → otevřít akci „C-201015104A“ 
- V části “Dokumentační jednotky” kliknout na komponentu “K001” u dokumentační jednotky “D01”
- V části “Komponenta C-201015104A-K001 ” kliknout na Další nabídka → Smazat komponentu  → v dialogovém okne “SMazat komponetnu” kliknout na “Smazat”

Testovací data
^^^^^^^^^^^^^^

C-201015104A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “C-201015104A-D01” bude smazána komponenta K001 „XXX”. V databázi bude o jeden záznam méně.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_094_smazani_komponenty_projektove_akce_p_001``.

Test 095 Smazání dokumentační jednotky u projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání dokumentační jednotky u projektové akce. Scénář končí smazáním dokumentační jednotky D01 u projektové akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A1 s dokumentační jednotkou D01.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
- Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku“D01”  →  v části “Dokumentační jednotka “Dokumentační jednotka C-202401980A-D01“ kliknout na “Další volby”  → DJ - smazat
- V části “Dokumentační jednotka “Dokumentační jednotka C-202401980A-D01“ kliknout na “Další volby”  → DJ - smazat → v dialogovém okně “Smazat dokumentační jednotku” kliknout na “Smazat”

Testovací data
^^^^^^^^^^^^^^
C-202401980A


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U projektové akce  “C-202401980A” bude smazána dokumentační jednotka D01. V databázi bude o jeden záznam méně.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_095_smazani_DJ_projektove_akce_p_001``.

Test 102 Archivace projektové akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace projektové akce. Scénář končí posunem projektové akce ze stavu A2 do stavu A3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projektová akce ve stavu A2 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.
- Nahrazuje NZ - Ano

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-201443939A)
- Projekty → Vybrat → Filtr → ID obsahuje C-201443939A → Vybrat → otevřít projekt →  otevřít akci „C-201443939A“ 
- V panelu pro akce kliknout na “Archivovat” → v dialogovém okně “Archivovat záznam” kliknout na “Archivovat”
- V dalším dialogovém okně “Archivace projektu” kliknout na “Archivovat”

Testovací data
^^^^^^^^^^^^^^

C-201443939A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Projektová akce “C-201443939A” se posune ze stavu A2 do stavu A3. Projekt “C-201443939A” se posune ze stavu P5 do stavu P6. 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceProjektoveAkce.test_102_archivace_projektove_akce_p_001``.


Samostatné nálezy
-----------------

Test 025 Zapsání samostatného nálezu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání samostatného nálezu na stránce /pas/zapsat. Končí zapsáním samostatného nálezu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt typu “průzkum” je ve stavu P3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Samostatné nálezy -> Zapsat nález
- Uživatel vyplní data do formuláře a kliknutím na mapu vybere lokalizaci nálezu
- Uživatel klikne na tlačítko Uložit

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Po kliknutí na tlačítko Uložit je v databázi o jeden samostatný nález více.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_025_zapsani_samostatneho_nalezu_p_001``.

Test 026 Zapsání samostatného nálezu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání samostatného nálezu na stránce /pas/zapsat. Test simuluje zadání nevalidních dat a měl by končit nezapsáním projektu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Projekt typu “průzkum” je ve stavu P3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Samostatné nálezy -> Zapsat nález
- Uživatel vyplní data do formuláře a kliknutím na mapu vybere lokalizaci nálezu
- Uživatel klikne na tlačítko Uložit

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Neuspěšné zapsání projektu, počet projektů v databázi se nezměnil.
- Zobrazena chyba “Chybí Projekt”


Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_026_zapsani_samostatneho_nalezu_n_001``.

Test 028 Odeslání samostatného nálezu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání samostatného nálezu ve stavu SN1 na stránce /pas/detail. Měl by končit odesláním samostatného nálezu a změnou jeho stavu na SN2.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN1
- Uživatel nahraje k nálezu fotografii
- Uživatel klikne na tlačítko Odeslat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

test_foto_1.jpg

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Odeslání samostatného nálezu a změna jeho stavu na SN2.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_028_odeslani_samostatneho_nalezu_p_001``.

Test 029 Odeslání samostatného nálezu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání samostatného nálezu ve stavu SN1 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit neodesláním samostatného nálezu a jeho ponecháním ve stavu SN1.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN1 (číslo SN)
- Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
- Uživatel klikne na tlačítko Odeslat

Testovací data
^^^^^^^^^^^^^^

M-202105907-N00091

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Neodeslání samostatného nálezu a jeho ponechání ve stavu SN1.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_029_odeslani_samostatneho_nalezu_n_001``.

Test 030 Potvrzení samostatného nálezu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání samostatného nálezu ve stavu SN2 na stránce /pas/detail. Měl by končit potvrzením samostatného nálezu a změnou jeho stavu na SN3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN2 (číslo SN) → Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
- Uživatel vyplní testovací data do formuláře
- Uživatel klikne na tlačítko Odeslat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^
C-202211308-N00213

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Odeslání samostatného nálezu a změna jeho stavu na SN3.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_030_potvrzeni_samostatneho_nalezu_p_001``.


Test 031 Potvrzení samostatného nálezu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test potvrzení samostatného nálezu ve stavu SN2 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN2 (čílso SN)
- Samostatné nálezy → Vybrat → Filtr → ID obsahuje „čílso SN“ → Vybrat → otevřít SN
- Uživatel vyplní testovací data do formuláře
- Uživatel klikne na tlačítko Odeslat a volbu potvrdí



Testovací data
^^^^^^^^^^^^^^
PAS C-202211308-N00213

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
- Zobrazena chyba “Před potvrzením musí být nález předán”


Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_031_potvrzeni_samostatneho_nalezu_n_001``.


Test 032 Potvrzení samostatného nálezu (negativní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test potvrzení samostatného nálezu ve stavu SN2 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN2 (číslo SN)
- Samostatný nález → Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
- Uživatel vyplní tetovací data do formuláře
- Uživatel klikne na tlačítko Odeslat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^
PAS C-202211308-N00213

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
- Zobrazena chyba “Vyplňte prosím toto pole”

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_032_potvrzeni_samostatneho_nalezu_n_002``.


Test 038 Archivace samostatného nálezu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace samostatného nálezu ve stavu SN3 na stránce /pas/detail. Měl by končit potvrzením samostatného nálezu a změnou jeho stavu na SN4.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN3
- Samostatné nálezy → Vybrat → Filtr → ID obsahuje „C-202010474-N00002“ → Vybrat → otevřít samostatný nález
- Uživatel klikne na tlačítko Archivovat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-202010474-N00002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Archivace samostatného nálezu a jeho posunutí do stavu SN4.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_038_archivace_samostatneho_nalezu_p_001``.


Test 039 Archivace samostatného nálezu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace samostatného nálezu ve stavu SN3 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN3
- Uživatel smaže přiloženou fotografii

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN3
- Samostatné nálezy → Vybrat → Filtr → ID obsahuje „samostatný nález v SN3“ → Vybrat → otevřít samostatný nález
- Uživatel klikne na tlačítko Archivovat

Testovací data
^^^^^^^^^^^^^^

C-202010474-N00002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
- Zobrazena chyba “Chybí fotografie”

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_039_archivace_samostatneho_nalezu_n_001``.

Test 045 Vrácení samostatného nálezu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení samostatného nálezu ve stavu SN3 na stránce /pas/detail. Měl by končit vrácením samostatného nálezu a změnou jeho stavu na SN2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatný nález je ve stavu SN3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatný nález ve stavu SN3
- Samostatné nálezy → Vybrat → Filtr → ID obsahuje „M-202301371-N00015“ → Vybrat → otevřít samostatný nález
- Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

M-202301371-N00015

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vrácení samostatného nálezu do stavu SN2.

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_045_vraceni_samostatneho_nalezu_p_001``.

Test 147 Test Fedory PAS (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel, Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^
- Vytvoření PAS
- Editace PAS
- Vytvoření souboru
- Reload soubor
- Smazání souboru
- Editace Uložení
- Smazání PAS

Testovací data
^^^^^^^^^^^^^^

M-202105907
test.jpg
test1.jpg

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_147_test_Fedora_PAS_001``.

Test 154 Zobrazební spolupráce Badatel - Archeolog (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test  "Badatel" vidí jen své spolupráce a "Archeolog" vidí jen spolupráce své organizace

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel, Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

Uživatel se přihlásí jako Badatel
Uživatel klikne na menu PAS -> Spolupráce
Uživatel Badatel vidí jen své spolupráce
Uživatel se přihlásí jako Archeolog
Uživatel klikne na menu PAS -> Spolupráce
Uživatel Archeolog vidí jen spolupráce své organizace

Testovací data
^^^^^^^^^^^^^^
žádné.

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Badatel a Archeolog vidí správný počet záznamů

Stav testu
^^^^^^^^^^

Implementován v
``pas.tests.test_selenium.AkceSamostatneNalezy.test_154_zobrazeni_spoluprace_p_001``.

Oznameni
--------

Test 027 Proces oznámení projektu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Oznámení projektu stavebníkem

Uživatelská role
^^^^^^^^^^^^^^^^
-

Předpoklady
^^^^^^^^^^^
žádné

Uživatelské kroky
^^^^^^^^^^^^^^^^^
Uživatel na stránce /oznameni vyplní formulář a odešle ho.


Testovací data
^^^^^^^^^^^^^^

test_foto_1.jpg

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  V databázi je o jedn projekt více.

Stav testu
^^^^^^^^^^

Implementován v
``oznameni.tests.test_selenium.OznameniSeleniumTest.test_027_oznameni_projektu_001``.


Samostatná akce
---------------

Test 046 Vytvoření samostané akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření samostatné akce. Scénář končí vytvořením samostatné akce akce ve stavu A1.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.   

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel vstoupí do modulu Samostatné akce pro zápis nové akce
- Samostatné akce → Zapsat
- Uživatel vyplní povinné položky
- Uživatel klikne na tlačítko “Zapsat”


Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Vytvoření samostatné akce - v databázi bude o jednu akci více

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_046_vytvoreni_samostatne_akce_p_001``.

Test 047 Vytvoření samostatné akce (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření samostatné akce. Scénář nekončí vytvořením samostatné akce ve stavu A1.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel vstoupí do modulu Samostatné akce pro zápis nové akce
- Samostatné akce → Zapsat
- Uživatel vyplní povinné položky, nevyplní Hlavní katastr
- Uživatel klikne na tlačítko “Zapsat”



Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Nedojde k vytvoření samostatné akce - v databázi bude stejný počet akcí

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_047_vytvoreni_samostatne_akce_n_001``.

Test 048 Přidání dokumentační jednotky celek akce (pozitivní scénář 1) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu celek akce u samostané akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.   
- Samostatná akce ve stavu A1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1
- Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
- Uživatel přidá dokumentační jednotku “Celek akce” (v sekci dokumentační jednotky)
- Dokumentační jednotky  → Přidat dokumentační jednotku 	
- Uživatel vyplní povinná pole
- Uživatel klikne na tlačítko “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000001A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U akce bude vytvořena DJ D01 typu “Celek akce” (v databázi je o jednu DJ více)

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001``.

Test 049  Přidání dokumentační jednotky “Celek akce” (negativní scénář 1) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu celek akce u samostatné akce ve stavu A1. Scénář nekončí vytvořením dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.   
- Samostatná akce ve stavu A1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1
- Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
- Uživatel přidá dokumentační jednotku “Celek akce” (v sekci dokumentační jednotky)
- Dokumentační jednotky  → Přidat dokumentační jednotku 	
- Uživatel vyplní povinná pole, nevyplní Typ 
- Uživatel klikne na tlačítko “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000001A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U akce NEbude vytvořena DJ typu “Celek akce” (v databázi je stejný počet DJ)

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001``.

Test 050 Přidání komponenty k DJ u samostatné akce (pozitivní scénář 1) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření komponenty k DJ u samostatné akce ve stavu A1. Scénář 	končí vytvořením komponenty K01.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.   
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1
- Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
- Uživatel vybere dokumentační jednotku D01 (v sekci “Dokumentační jednotky”)
- Uživatel k DJ přidá komponentu K01 - X-C-9000000060A-D01  → Další volby (+) → Komponenta vytvořit
- Uživatel vyplní povinná pole 
- Uživatel klikne na tlačítko “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000002A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U DJ bude vytvořena komponenta K01. V databázi bude o jednu komponentu více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_050_pridani_komponenty_DJ_samostatne_akce_p_001``.

Test 074 Přidání komponenty k DJ u samostatné akce (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření komponenty k DJ u samostatné akce ve stavu A1. Scénář nekončí vytvořením komponenty.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.   
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01


Uživatelské kroky
^^^^^^^^^^^^^^^^^

-  Uživatel se přihlásí
-  Uživatel otevře samostatnou akci ve stavu A1
-  Samostatné akce  → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít SA
-  Uživatel vybere dokumentační jednotku D01 (v sekci “Dokumentační jednotky”)
-  Uživatel k DJ přidá komponentu K01  X-C-9000000002AD01  → Další volby (+) → Komponenta vytvořit
-  Uživatel vyplní povinná pole, nevyplní Areál 
-  Uživatel klikne na tlačítko “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000002A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky D01 NEbude vytvořena komponenta (v databázi je stejný počet DJ). U pole Areál se objeví nápověda “Vyberte prosím v seznamu některou položku”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_074_pridani_komponenty_DJ_samostatne_akce_n_001``.

Test 075 Přidání objektu k pozitivní komponentě (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření objektu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí vytvořením objektu u komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Objekty zvolit Druh “(polo)zemnice”.
- V sekci Nálezy a Objekty vyplnit Počet “1”.
- Kliknout na “Uložit změny” 

Testovací data
^^^^^^^^^^^^^^

X-C-9000000003A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001``.

Test 076 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření předmětu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí vytvořením předmětu u komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Předměty zvolit Druh “džbán”.
- V sekci Nálezy a Předměty zvolit Specifikace “keramika”.
- V sekci Nálezy a Předměty vyplnit Počet “1”.
- Kliknout na “Uložit změny” 

Testovací data
^^^^^^^^^^^^^^

X-C-9000000003A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U komponenty K001 bude vytvořen nový předmět. V databázi bude o jeden předmět více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001``.

Test 077 Smazání objektu u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání objektu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí smazáním objektu.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001
- Objekt “jáma kůlová/sloupová” připojený ke komponentě K001

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít samostatnou akci
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Objekty u položky “jáma kůlová/sloupová” kliknout na možnost “odstranit”
- Volbu potvrdit

Testovací data
^^^^^^^^^^^^^^

X-C-9000000004A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  U komponenty K001 bude odebrána položka typu objekt. V databázi bude o jeden objekt méně. Oznámení “Záznam byl úspěšně smazán”

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001``.

Test 078 Smazání předmětu u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání předmětu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí smazáním předmětu.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1
- Dokumentační jednotka D01
- Komponenta K001
- Předmět “doklad umění/kultu” připojený ke komponentě K001

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít samostatnou akci
- Kliknout na komponentu K001 u dokumentační jednotky D01 
- V sekci Nálezy a Předměty u položky “doklad umění/kultu” kliknout na možnost “odstranit”
- Volbu potvrdit


Testovací data
^^^^^^^^^^^^^^

X-C-9000000004A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U komponenty K001 bude odebrána položka typu předmět. V databázi bude o jeden předmět méně. Oznámení “Záznam byl úspěšně smazán”

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001``.

Test 082 Přidání dokumentu k samostatné akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání dokumentu k samostatné akci. Scénář končí vytvořením záznamu dokumentu a jeho připojením k samostatné akci.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce je ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
- V tabulce Dokumenty kliknout na tlačítko “Přidat dokument”
- Uživatel vyplní povinné údaje ve formuláři Dokument
- Klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^

X-C-9000000003A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Bude vytvořen nový záznam typu dokument (v databázi je o jeden dokument více). Tento dokument je připojený k samostatné akci X-C-9000000003A

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_082_pridani_dokumentu_samostatne_akci_p_001``.

Test 083 Připojení existujícího dokumentu k samostatné akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení existujícího dokumentu k samostatné akci.Scénář končí vytvořením vazby mezi dokumentem a samostatnou akcí.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce je ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít projekt
- V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument”
- Uživatel vyhledá dokument “M-TX-194300126”
- Klikne na tlačítko Připojit

Testovací data
^^^^^^^^^^^^^^

X-C-9000000004A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Je vytvořena vazba mezi dokumentem a projektovou akcí X-C-9000000004A 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001``.

Test 085 Připojení externího zdroje k samostatné akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení externího zdroje k samostatné akci..Scénář končí vytvořením vazby mezi samostatnou akcí a externím zdrojem.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít akci „X-C-9000000003A“ 
- V části “Externí zdroje” kliknout na “připojit externí zdroj”
- Uživatel vyhledá identifikátor “X-BIB-1295325”
- Klikne na tlačítko Připojit

Testovací data
^^^^^^^^^^^^^^

X-C-9000000003A
X-BIB-1295324

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Je vytvořena vazba mezi samostatnou akcí externím zdrojem  „X-BIB-1295325“

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001``.

Test 096 Vytvoření PIAN u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření PIAN k samostatné akci.Scénář končí vytvořením nového PIAN připojeného k DJ D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000002A)
- Samostatné acke → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít akci „X-C-9000000002A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000002A-D01” kliknout na Další volby → PIAN - vytvořit → vytvořit geometrii PIAN 
- V části nový PIAN nastavit přesnost na hodnotu “odchylka jednotky metrů”

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000002A-D01” samostatné akce je připojen nový PIAN. V databázi je o jeden záznam více.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_096_vytvoreni_PIAN_samostatne_akce_p_001``.

Test 097 Editace PIAN u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test editace PIAN u samostatné akce. Scénář končí novou geometrií PIAN u dokumentační jednotky D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A-)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A-“ → Vybrat → otevřít akci „X-C-9000000006A-“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000006A--D01” kliknout na Další volby → PIAN - upravit → upravit geometrii PIAN (jak vyřešit v testu?)

Testovací data
^^^^^^^^^^^^^^

X-C-9000000006A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000006A--D01” je upravena geometrie připojeného PIAN (jak poznáme v testu?).

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_097_editace_PIAN_samostatne_akce_p_001``.

Test 098 Editace PIAN k samostatné akci importem (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test editace PIAN k samostatné akci importem. Scénář končí upraveným PIAN u dokumentační jednotky D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A“ → Vybrat → otevřít akci „X-C-9000000006A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000006A-D01” kliknout na Další volby → PIAN - upravit importem → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
- V části ““Dokumentační jednotka X-C-9000000006A-D01” kliknout na “uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000006A
geom.csv

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000006A-D01” bude upravena geometrie PIAN „XXX”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_098_editace_PIAN_samostatne_akce_importem_p_001``.

Test 099 Import PIAN k samostatné akci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test importu PIAN k samostatné akci. Scénář končí vytvořením PIAN u dokumentační jednotky D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000002A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít akci „X-C-9000000002A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000002A-D01” kliknout na Další volby → PIAN - importovat → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
- V části “Nový PIAN” vybrat přesnost “odchylka jednotky metrů” a kliknout “uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000002A
geom.csv

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000002A-D01” bude připojen nový PIAN „XXX”. V databázi bude o jeden PIAN více (vznikne vazba s D01).  

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_099_import_PIAN_samostatne_akce_p_001``.

Test 100 Odpojení potvrzeného PIAN u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odpojení potvrzeného PIAN u samostatné akce. Scénář končí odpojením existujícího PIAN od dokumentační jednotky D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- amostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000012A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000012A“ → Vybrat → otevřít akci „X-C-9000000012A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000012A-D01” kliknout na Další volby → PIAN - odpojit → V dialogovém okně “Odpojení PIAN” kliknout na “Odpojit”

Testovací data
^^^^^^^^^^^^^^
X-C-9000000012A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000012A-D01” zanikne vazba s PIAN „XXX”.

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_100_odpojeni_potvrzeneho_PIAN_samostatne_akce_p_001``.

Test 101 Smazání PIAN u samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test smazání PIAN u samostatné akce. Scénář končí smazáním nepotvrzeného PIAN u dokumentační jednotky D01 u samostatné akce.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A“ → Vybrat → otevřít akci „X-C-9000000006A“ 
- V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
- V části “Dokumentační jednotka X-C-9000000006A-D01” kliknout na Další volby → PIAN - odpojit → v dialogovém okně “Odpojení PIAN” kliknout na tlačítko “Odpojit”

Testovací data
^^^^^^^^^^^^^^

X-C-9000000006A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U dokumentační jednotky “X-C-9000000006A-D01” je smazán nepotvrzený PIAN, v databázi je o 1 PIAN méně. 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_101_smazani_PIAN_samostatne_akce_p_001``.

Test 103 Archivace samostatné akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace samostatné akce. Scénář končí posunem projektové akce ze stavu A2 do stavu A3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Samostatná akce ve stavu A2 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.
- Nahrazuje NZ - Ano

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-9157766A)
- Samostatné akce → Vybrat → Filtr → ID obsahuje „C-9157766A“ → Vybrat →  otevřít akci „C-9157766A“ 
- V panelu pro akce kliknout na “Archivovat” → v dialogovém okně “Archivovat záznam” kliknout na “Archivovat”

Testovací data
^^^^^^^^^^^^^^

C-9157766A

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Samostatná akce “C-9157766A” se posune ze stavu A2 do stavu A3. 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_103_archivace_samostatne_akce_p_001``.

Test 138 Test Fedory pro Samostatne akce (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Fedory pro Samostatne akce

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel, Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^
- Vytvoření Samostatné Akce
- Editace Akce
- Vytvoření vedoucího Akce
- Editace vedoudího Akce
- Smazání vedoucího Akce
- Vytvoření DJ
- Editace DJ
- Smazání DJ
- Vytvoření komponenty
- Editace komponenty
- Vytvoření nálezu
- Editace nálezu
- Smazání nálezu
- Smazání komponenty
- Připojení nového Dokumentu
- Odpojení Dokumentu
- Připojení EZ
- Editace EZ
- Odpojení EZ
- Odeslání Akce
- Samzání Akce
- Připojení existujícího dokumentu

Testovací data
^^^^^^^^^^^^^^

X-M-9922437A
X-C-9000000002A
BIB-0000001
X-C-91468414A
X-C-TX-000000008
ADB-BLAT60-000001
N-2214-000000004
C-9003982A
X-M-91558334A
M-TX-194300151

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_138_test_Fedory_samostatne_akce_p_001``.

Test 139 Test Fedory pro PIAN, ADB, vyskovy bod (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření PIAN
- Vytvoření ADB
- Vytvoření Výškového bodu
- Editace PIAN
- Editace ADB
- Změna přístupnosti Akce
- Editace Výškového bodu
- Smazání Výškového bodu
- Smazání ADB
- Odpojení a smazání PIAN
- Pripojení existujícího PIAN
- Odpojení PIAN bez smazání
- Potvrzení PIAN
- Vytvoření DJ typu katastr
- Editace DJ typu katastr
- Smazání DJ typu katastr
- Smazání DJ

Testovací data
^^^^^^^^^^^^^^

X-C-9000000011A
P-1121-100070
ruian-693154
ruian-600016
X-C-91601363A
P-2212-010011

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory 

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_139_test_Fedory_PIAN_p_001``.

Test 140 Test Fedory pro ADB (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Arcivovat Akci s ADB

Testovací data
^^^^^^^^^^^^^^

M-9002352A
N-1541-000000005
ADB-OPAV13-000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``arch_z.tests.test_selenium.AkceSamostatneAkce.test_140_test_Fedory_ADB_p_001``.

Lokality
--------

Test 051 Zapsání lokality (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání lokality na stránce /arch-z/lokalita/zapsat. Končí zapsáním lokality do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Lokality -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jednu lokalitu více.

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_051_zapsani_lokality_p_001``.

Test 052 Zapsání lokality (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání lokality na stránce /arch-z/lokalita/zapsat. Nekončí zapsáním lokality do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^
- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Lokality -> Zapsat
- Uživatel vyplní data do formuláře, nevyplní pole Název
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Neuspěšné zapsání lokality, počet lokalit v databázi se nezměnil.
- Zobrazena nápověda “Vyplňte prosím toto pole” u pole Název.


Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_052_zapsani_lokality_n_001``.

Test 053 Přidání dokumentační jednotky lokalita (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu lokalita u lokalita ve stavu L1. Scénář končí vytvořením dokumentační jednotky D01 typu lokalita.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L1 a nemá žádnou dokumentační jednotku

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L1 (viz předpoklady)
- Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000001“ → Vybrat → otevřít lokalitu
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ DJ “lokalita”
- Zvolit typ Negativní jednotka “ne”
- Kliknout na “uložit” 

Testovací data
^^^^^^^^^^^^^^

X-C-L000000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U akce bude vytvořena DJ typu “lokalita” (v databázi je o jednu DJ více).

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_053_pridani_DJ_lokality_p_001``.


Test 054 Přidání dokumentační jednotky lokalita (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření dokumentační jednotky typu lokalita u lokalita ve stavu L1. Scénář nekončí vytvořením dokumentační jednotky D01 typu lokalita.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L1 a nemá žádnou dokumentační jednotku

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L1 (viz předpoklady)
- Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000001“ → Vybrat → otevřít lokalitu
- Kliknout na tlačítko “Přidat dokumentační jednotku”
- Zvolit typ Negativní jednotka “ne”, nevybere pole Typ
- Kliknout na “uložit” 

Testovací data
^^^^^^^^^^^^^^

X-C-L000000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Neuspěšné vytvoření DJ typu “lokalita”, počet DJ v databázi se nezměnil.
- Zobrazena nápověda “Vyberte prosím v seznamu některou položku” u pole Typ.


Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_054_pridani_DJ_lokality_n_001``.

Test 055 Přidání komponenty k dokumentační jednotce lokalita (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vytvoření komponenty u dokumentační jednotky typu lokalita u lokality ve stavu L1. Scénář končí vytvořením komponenty K001 u dokumentační jednotky D01.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L1 a má dokumentační jednotku D01 typu lokalita, která je pozitivní.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L1 (X-C-L000000002)
- Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000002“ → Vybrat → otevřít lokalitu
- Kliknout na dokumentační jednotku D01 
- Kliknout na “Další volby” a zvolit ”Komponenta - vytvořit”.
- Zvolit Období “únětická k.”
- Zvolit Areál “sídliště nesp.”.
- Kliknout na “uložit změny” 

Testovací data
^^^^^^^^^^^^^^

X-C-L000000002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U DJ D01 bude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001``.

Test 056 Odeslání lokality (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání lokality ve stavu L1 na stránce /arch-z/lokalita/detail. Měl by končit odesláním lokality a změnou jeho stavu na L2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L1, má připojenu dokumentační jednotku D01, ta má připojenu komponentu K001. Dokumentační jednotka má připojený PIAN.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L1
- Lokalita → Vybrat → Filtr → ID obsahuje „C-N9000579“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Odeslat a volbu potvrdí


Testovací data
^^^^^^^^^^^^^^

C-N9000579

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Odeslání lokality a změna jejího stavu na L2.

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_056_odeslani_lokality_p_001``.

Test 057 Odeslání lokality (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání lokality ve stavu L1 na stránce /arch-z/lokalita/detail. Měl by končit neodesláním lokality a ponecháním lokality ve stavu L1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L1, má připojenu dokumentační jednotku D01, ta má připojenu komponentu K001. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L1
- Lokalita → Vybrat → Filtr → ID obsahuje „C-N9000145“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Odeslat

Testovací data
^^^^^^^^^^^^^^

C-N9000145

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Neodeslání lokality a její ponechání ve stavu L1. Chybová hláška “Dokumentační jednotce C-N9000145-D01 chybí PIAN”,

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_057_odeslani_lokality_n_001``.

Test 058 Archivace lokality (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit archivací lokality a změnou jeho stavu na L3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L2.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L2
- Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
- Uživatel vybere dokumentační jednotku D01 a potvrdí nepotvrzený PIAN
- Dokumentační jednotky → D01 → Další volby → PIAN - potvrdit
- Uživatel klikne na tlačítko Archivovat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-N1000003

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Archivace lokality a její posunutí do stavu L3.

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_058_archivace_lokality_p_001``.

Test 059 Archivace lokality (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit ponecháním lokality ve stavu L2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L2.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L2
- Lokality → Vybrat → Filtr → ID obsahuje „C-N1000109“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Archivovat

Testovací data
^^^^^^^^^^^^^^

C-N1000109

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- K archivaci lokality nedojde, ta zůstane ve stavu L2.
- Zobrazena chyba “Lokalitu nelze odeslat. Zkontrolujte, zda má všechny náležitosti.” a nápověda “Dokumentační jednotce X-M-K000000034-D01 chybí PIAN.”


Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_059_archivace_lokality_n_001``.

Test 060 Vrácení odeslané lokality (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit vrácením lokality a změnou jejího stavu na L1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L2
- Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-N1000003

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vrácení lokality do stavu L1.

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_060_vraceni_odeslane_lokality_p_001``.

Test 061 Vrácení odeslané lokality (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit neúspěšným vrácením a ponecháním lokality ve stavu L2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L2
- Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Vrátit a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-N1000003

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- K vrácení lokality nedojde, ta zůstane ve stavu L2.
- Zobrazena nápověda “Vyplňte prosím toto pole”

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_061_vraceni_odeslane_lokality_n_001``.

Test 062 Vrácení archivované lokality (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení lokality ve stavu L3 na stránce /arch-z/lokalita/detail. Měl by končit vrácením lokality a změnou jejího stavu na L2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L3


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L3
- Lokality → Vybrat → Filtr → ID obsahuje „C-N9000593“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-N9000593

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vrácení lokality do stavu L2. 

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_062_vraceni_archivovane_lokality_p_001``.

Test 063 Vrácení archivované lokality (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení lokality ve stavu L3 na stránce /arch-z/lokalita/detail. Měl by končit neúspěšným vrácením a ponecháním lokality ve stavu L3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Lokalita je ve stavu L3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře lokalitu ve stavu L3
- Lokality → Vybrat → Filtr → ID obsahuje „C-N9000593“ → Vybrat → otevřít lokalitu
- Uživatel klikne na tlačítko Vrátit a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-N9000593

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- K vrácení lokality nedojde, ta zůstane ve stavu L3.
- Zobrazena nápověda “Vyplňte prosím toto pole”

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_063_vraceni_archivovane_lokality_n_001``.

Test 143 Test Fedory pro lokalitu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření Lokality
- Editace Lokality
- Vytvoření DJ
- Editace DJ
- Vytvoření PIAN
- Editace PIAN
- Vytvoření komponenty
- Editace komponenty
- Vytvoření nálezu
- Editace nálezu
- Připojení a vytvoření nového Části dokumentu
- Připojení EZ
- Editace EZ
- Odeslání Lokality
- Smazaní EZ
- Smazání Části dokumentu
- Smazání nálezu
- Smazání komponenty
- Smazání DJ
- Smazání Lokality
- Potvrzení PIAN
- Připojení existujícího dokumentu

Testovací data
^^^^^^^^^^^^^^

ruian-679038
BIB-0000001
X-C-K0751147
N-1412-000000007
M-L9000181
M-TX-194300151

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``lokalita.tests.test_selenium.AkceLokality.test_143_test_Fedory_lokalita_p_001``.

Dokumenty
---------

Test 064 Zapsání dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dokumentu na stránce /dokument/zapsat. Končí zapsáním dokumentu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Dokumenty -> Zapsat
- Uživatel vyplní územní příslušnost
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden dokument více. Dokument změní svůj stav na D1

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_064_zapsani_dokumentu_p_001``.

Test 065 Zapsání dokumentu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dokumentu na stránce /dokument/zapsat. Končí neúspěšným zapsáním dokumentu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Dokumenty -> Zapsat
- Uživatel vyplní územní příslušnost
- Uživatel vyplní data do formuláře, nevyplní pole Autoři
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat se objeví nápověda u pole autoři “Vyberte prosím v seznamu některou položku”

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_065_zapsani_dokumentu_n_001``.

Test 066 Odeslání dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit úspěšným odesláním dokumentu a jeho posunutím do stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D1. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D1
- Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000003“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Odeslat


Testovací data
^^^^^^^^^^^^^^

X-C-TX-000000003

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Odeslání dokumentu a změna jeho procesního stavu na D2.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_066_odeslani_dokumentu_p_001``.

Test 057 Odeslání dokumentu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit neúspěšným odesláním dokumentu a jeho ponecháním ve stavu D1.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D1. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu L1
- Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000003“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Odeslat

Testovací data
^^^^^^^^^^^^^^

X-C-TX-000000003

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  Neúspěšné odeslání dokumentu a jeho ponechání ve stavu D1. Chybová hláška “Dokument nelze odeslat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”,

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_067_odeslani_dokumentu_n_001``.

Test 068 Archivace dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace dokumentu ve stavu D2 na stránce /dokument/detail/. Měl by končit archivací dokumentu a změnou jeho stavu na D3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D2.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D2
- Dokumenty → Vybrat → Filtr → ID obsahuje „X-C-TX-202413020“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Archivovat a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

X-C-TX-202413020

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Archivace dokumentu a jeho posunutí do stavu D3.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_068_archivace_dokumentu_p_001``.

Test 069 Archivace dokumentu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace dokumentu ve stavu D2 na stránce /dokument/detail/. Měl by končit neúspěšnou archivací dokumentu a jeho ponecháním ve stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D1. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D2
- Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-202413013“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Archivovat

Testovací data
^^^^^^^^^^^^^^

X-C-TX-202413013

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Neúspěšná archivace dokumentu a jeho ponechání ve stavu D2. Chybová hláška “Dokument nelze archivovat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_069_archivace_dokumentu_n_001``.

Test 070 Vrácení odeslaného dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení dokumentu ve stavu D2 na stránce /dokument/detail. Měl by končit vrácením dokumentu a změnou jeho stavu na D1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D2
- Dokumenty → Vybrat → Filtr → ID obsahuje „M-TX-201604272“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

M-TX-201604272

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vrácení dokumentu do stavu D1.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001``.

Test 071 Vrácení odeslaného dokumentu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení dokumentu ve stavu D2 na stránce /dokument/detail. Měl by končit neúspěšným vrácením a ponecháním dokumentu ve stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D2

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D2
- Dokumenty → Vybrat → Filtr → ID obsahuje „M-TX-201604272“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Vrátit a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

M-TX-201604272

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- K vrácení dokumentu nedojde, ten zůstane ve stavu D2.
- Zobrazena nápověda “Vyplňte prosím toto pole”
 

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001``.

Test 072 Vrácení archivovaného dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení dokumentu ve stavu D3 na stránce /dokument/detail. Měl by končit vrácením dokumentu a změnou jeho stavu na D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D3


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D3
- Dokumenty → Vybrat → Filtr → ID obsahuje „C-TX-202400071“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-TX-202400071

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vrácení dokumentu do stavu D2.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001``.

Test 073 Vrácení archivovaného dokumentu (negativní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test vrácení dokumentu ve stavu D3 na stránce /dokument/detail. Měl by končit neúspěšným vrácením a ponecháním dokumentu ve stavu D3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D3

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu D3
- Lokality → Vybrat → Filtr → ID obsahuje „C-TX-202400071“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Vrátit a volbu potvrdí

Testovací data
^^^^^^^^^^^^^^

C-TX-202400071

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- K vrácení dokumentu nedojde, ten zůstane ve stavu D3.
- Zobrazena nápověda “Vyplňte prosím toto pole”
 

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001``.

Test 132 Zapsání dokumentu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dokumentu na stránce /dokument/zapsat. Končí zapsáním dokumentu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Dokumenty -> Zapsat
- Uživatel vyplní územní příslušnost
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden dokument více. Dokument změní svůj stav na D1

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_132_zapsani_dokumentu_p_002``.

Test 133 Zapsání dokumentu (negativní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dokumentu na stránce /dokument/zapsat. Končí neúspěšným zapsáním dokumentu do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Dokumenty -> Zapsat
- Uživatel vyplní územní příslušnost
- Uživatel vyplní data do formuláře, nevyplní pole Autoři
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat se objeví nápověda u pole autoři “Vyberte prosím v seznamu některou položku”

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_133_zapsani_dokumentu_n_002``.

Test 134 Odeslání dokumentu (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit úspěšným odesláním dokumentu a jeho posunutím do stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D1. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu L1
- Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000002“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Odeslat

Testovací data
^^^^^^^^^^^^^^

X-C-TX-000000002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Odeslání dokumentu a změna jeho procesního stavu na D2.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_134_odeslani_dokumentu_p_002``.

Test 135 Odeslání dokumentu (negativní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit neúspěšným odesláním dokumentu a jeho ponecháním ve stavu D1.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Dokument je ve stavu D1. 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře dokument ve stavu L1
- Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000002“ → Vybrat → otevřít dokument
- Uživatel klikne na tlačítko Odeslat

Testovací data
^^^^^^^^^^^^^^

X-C-TX-000000002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Neúspěšné odeslání dokumentu a jeho ponechání ve stavu D1. Chybová hláška “Dokument nelze odeslat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”,

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_135_odeslani_dokumentu_n_002``.

Test 141 Test Fedory pro Dokument (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření Dokumentu
- Editace Dokumentu
- Editace Letu v Dokumentu
- Vytvoření Části Dokumentu typ Akce
- Vytvoření Části Dokumentu typ Lokalita
- Vytvoření Části Dokumentu typ Projekt
- Vytvoření komponenty
- Vytvoření nálezu objektu a předmětu
- Vytvoření Tvaru
- Přidání souboru
- Odeslání Dokumentu
- Editace Části Dokumentu
- Editace komponenty
- Editace nálezu
- Smazání nálezu
- Smazání komponenty
- Smazání Části Dokumentu
- Smazání Části Dokumentu typ projekt
- Smazání Části Dokumentu typ lokalita
- Editace Tvaru
- Smazání Tvaru
- Upgrade souboru
- Smazání souboru
- Editace Neidentifikované Akce
- Smazání Neidentifikované Akce
- Smazání Dokumentu
- Odpojení Akce
- Odpojení Lokality
- Odpojení Projektu


Testovací data
^^^^^^^^^^^^^^

C-LET-00001
C-200810821A
C-K9000001
C-201911202
C-TX-197602290
X-C-TX-201801164
C-201125635A
C-202010506
C-K9000010
C-LET-00010
X-C-TX-201801166
C-201226860A
C-K9000024
C-202104117

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_141_test_Fedory_dokument_p_001``.

Test 142 Test Fedory pro LET (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření Letu
- Editace Letu
- Připojení Letu v Dokumentu
- Odpojení Letu v Dokumentu
- Smazání Letu

Testovací data
^^^^^^^^^^^^^^

M-TX-202000166

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceDokumenty.test_142_test_Fedory_LET_p_001``.

Knihovna 3D
-----------

Test 104 Zápis záznamu do knihovny 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zápisu nového záznamu do Knihovny 3D. Scénář končí vytvořením nového záznamu v Knihovně 3D.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Hodnoty pro povinná pole 

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Zapsat  → uživatel vyplní povinná pole  → uživatel klikne na tlačítko “Zapsat”

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vznikne nový záznam v Knihovně 3D - v databázi bude o jeden záznam více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_104_zapis_do_knihovny_D3_p_001``.

Test 105 Odeslání záznamu do knihovny 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání záznamu do Knihovny 3D. Scénář končí posunem záznamu ze stavu D1 do stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Hodnoty pro povinná pole
- Soubor s náhledem 3D modelu

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“ 
- Uživatel vyplní povinná pole
- V sekci “Náhledy 3D modelu/soubory s texturou” klikne uživatel na možnost “Nahrát soubory” → vloží soubor “del.zip” a klikne na “Dokončit”
- V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

Testovací data
^^^^^^^^^^^^^^
X-C-3D-000000005
del.zip

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam v Knihovně 3D se posune ze stavu D1 do stavu D2.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_105_odeslani_zaznamu_knihovny_D3_p_001``.

Test 106 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidání objektu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“ 
- V části “Specifikace obsahu” v části “Objekty” vybere uživatel v poli “Druh” hodnotu “hradba” a klikne na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000005

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořen nový objekt. V databázi bude o jeden objekt více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_106_pridani_objektu_knihovny_D3_p_001``.

Test 107 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidáním předmětu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“ 
- V části “Specifikace obsahu” v části “Předměty” vybere uživatel v poli “Druh” hodnotu “dýka”, v poli “Specifikace” hodnotu “kámen štípaný” a klikne na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000005

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořen nový předmět. V databázi bude o jeden předmět více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_107_pridani_predmetu_knihovny_D3_p_001``.

Test 108 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání prostorového vymezení k záznamu v Knihovně 3D. 

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“ 
- V části “Detail” klikne uživatel na “upravit”  → v mapě se přiblíží na místo XXX a klikne do mapy (jak vyřešit v testu?) → kliknout na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000005

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořeno nové prostorové vymezení - bude vytvořena vazba mezi záznamem a prostorovým vymezením.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_108_pridani_souradnic_knihovny_D3_p_001``.

Test 109 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání souboru k záznamu v Knihovně 3D.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1, který nemá připojený soubor.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“ 
- V části “Náhledy 3D modelu/soubory s texturou” klikne uživatel na “nahrát soubory” → v dialogové obrazovce vybere uživatel soubor del.zip → kliknout na “Dokončit”

Testovací data
^^^^^^^^^^^^^^
del.zip
X-C-3D-000000005

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude připojen nový soubor.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_109_pridani_souboru_zaznamu_knihovny_D3_p_001``.

Test 110 Archivace záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test archivace záznamu v Knihovně 3D. Test končí posunem záznamu ze stavu D2 do D3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D2, který má vyplněny všechny náležitosti.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „XXX“ → Vybrat → otevřít záznam „XXX“ 
- V panelu pro akce klikne uživatel na tlačítko “Archivovat” → v dialogovém okně “Archivovat dokument” klikne uživatel na tlačítko “Archivovat”

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam v Knihovně 3D se posune ze stavu D2 do stavu D3.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_110_archivace_zaznamu_knihovny_D3_p_001``.

Test 111 Zápis záznamu do knihovny 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zápisu nového záznamu do Knihovny 3D. Scénář končí vytvořením nového záznamu v Knihovně 3D.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Hodnoty pro povinná pole

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Zapsat  → uživatel vyplní povinná pole  → uživatel klikne na tlačítko “Zapsat”

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Vznikne nový záznam v Knihovně 3D - v databázi bude o jeden záznam více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_111_zapis_do_knihovny_D3_p_002``.

Test 112 Odeslání záznamu do knihovny 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání záznamu do Knihovny 3D. Scénář končí posunem záznamu ze stavu D1 do stavu D2.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- Hodnoty pro povinná pole
- Soubor s náhledem 3D modelu

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“ 
- Uživatel vyplní povinná pole 
- V sekci “Náhledy 3D modelu/soubory s texturou” klikne uživatel na možnost “Nahrát soubory” → vloží soubor “del.zip” a klikne na “Dokončit”
- V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

Testovací data
^^^^^^^^^^^^^^

del.zip
X-C-3D-000000006

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam v Knihovně 3D se posune ze stavu D1 do stavu D2.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_112_odeslani_zaznamu_knihovny_D3_p_002``.

Test 113 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidání objektu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“ 
- V části “Specifikace obsahu” v části “Objekty” vybere uživatel v poli “Druh” hodnotu “kašna” a klikne na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000006

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořen nový objekt. V databázi bude o jeden objekt více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_113_pridani_objektu_knihovny_D3_p_002``.

Test 114 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidáním předmětu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“ 
- V části “Specifikace obsahu” v části “Předměty” vybere uživatel v poli “Druh” hodnotu “zub”, v poli “Specifikace” hodnotu “zub lidský” a klikne na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000006

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořen nový předmět. V databázi bude o jeden předmět více.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_114_pridani_predmetu_knihovny_D3_p_002``.

Test 115 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání prostorového vymezení k záznamu v Knihovně 3D. 

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“ 
- V části “Detail” klikne uživatel na “upravit”  → v mapě se přiblíží na místo XXX a klikne do mapy → kliknout na “Uložit změny”

Testovací data
^^^^^^^^^^^^^^

X-C-3D-000000006

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude vytvořeno nové prostorové vymezení - bude vytvořena vazba mezi záznamem a prostorovým vymezením.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_115_pridani_souradnic_knihovny_D3_p_002``.

Test 116 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test přidání souboru k záznamu v Knihovně 3D. 

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v Knihovně 3D ve stavu D1, který nemá připojený soubor.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“ 
- V části “Náhledy 3D modelu/soubory s texturou” klikne uživatel na “nahrát soubory” → v dialogové obrazovce vybere uživatel soubor del.zip  → kliknout na “Dokončit”

Testovací data
^^^^^^^^^^^^^^

del.zip
X-C-3D-000000006

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- U záznamu v Knihovně 3D bude připojen nový soubor.

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_116_pridani_souboru_zaznamu_knihovny_D3_p_002``.

Test 144 Test Fedory pro 3D dokumenty (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření 3D dokumentu
- Editace 3D dokumentu
- Editace komponenty
- Vytvoření nálezu
- Editace nálezu
- Nahrání souboru
- Upgrade souboru
- Odeslání 3D dokumentu
- Smazáí nálezu
- Smazání souboru
- Smazání 3D dokumentu

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

-  zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``dokument.tests.test_selenium.AkceKnihovna3D.test_144_test_Fedory_3D_p_001``.


Externí zdroje
--------------

Test 117 Zápsání nového externího zdroje typu kniha (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001``.

Test 118 Odeslání záznamu Externí zdroj (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání záznamu Externí zdroj. Scénář končí posunem záznamu ze stavu EZ1 do stavu EZ2.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- záznam Externí zdroj ve stavu EZ1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“ 
- V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

Testovací data
^^^^^^^^^^^^^^

X-BIB-000000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam Externí zdroj se posune ze stavu EZ1 do stavu EZ2.

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_118_odeslani_externího_zdroje_p_001``.

Test 119 Připojení akce k externímu zdroji (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení záznamu Akce k záznamu Externí zdroj. Scénář končí vytvořením vazby mezi záznamy.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- záznam Externí zdroj ve stavu EZ1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“ 
- V tabulce Připojené akce kliknout na “Připojit akci” → v dialogovém okně v poli “Připojovaný záznam” vyhledat záznam akce X-M-9000000007A, po vyhledání potvrdit kliknutím na “Připojit”

Testovací data
^^^^^^^^^^^^^^

X-BIB-000000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- V tabulce připojených akcí je o jednu připojenou akci více

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_119_pripojeni_akce_externího_zdroje_p_001``.

Test 120 Připojení lokality k externímu zdroji (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test připojení záznamu Akce k záznamu Externí zdroj. Scénář končí vytvořením vazby mezi záznamy.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- záznam Externí zdroj ve stavu EZ1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“ 
- V tabulce Připojené lokality kliknout na “Připojit lokalitu” → v dialogovém okně v poli “Připojovaný záznam” vyhledat záznam lokality C-K9000001, po vyhledání potvrdit kliknutím na “Připojit”

Testovací data
^^^^^^^^^^^^^^

C-K9000001
X-BIB-000000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- V tabulce připojených lokalit je o jednu připojenou lokalitu více

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_120_pripojeni_lokality_externího_zdroje_p_001``.

Test 121 Potvrzení externího zdroje (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test potvrzení záznamu v modulu Externí zdroje. Test končí posunem záznamu ze stavu EZ2 do EZ3.

Uživatelská role
^^^^^^^^^^^^^^^^
Archivář

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen
- Záznam v modulu Externí zdroje ve stavu EZ2, který má vyplněny všechny náležitosti.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-1408662“ → Vybrat → otevřít záznam „X-BIB-1408662“ 
- V panelu pro akce klikne uživatel na tlačítko “Potvrdit” → v dialogovém okně “Potvrdit externí zdroj” klikne uživatel na tlačítko “Potvrdit”

Testovací data
^^^^^^^^^^^^^^

X-BIB-1408662

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam Externí zdroj se posune ze stavu EZ2 do stavu EZ3.

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_121_potvrzení_externího_zdroje_p_001``.

Test 122 Zapsání nového externího zdroje (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_122_zapsani_externího_zdroje_p_002``.

Test 123 Odeslání záznamu Externí zdroj (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test odeslání záznamu Externí zdroj. Scénář končí posunem záznamu ze stavu EZ1 do stavu EZ2.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.
- záznam Externí zdroj ve stavu EZ1

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000002“ → Vybrat → otevřít záznam „X-BIB-000000002“ 
- V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

Testovací data
^^^^^^^^^^^^^^

X-BIB-000000002

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Záznam Externí zdroj se posune ze stavu EZ1 do stavu EZ2.

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_123_odeslani_externího_zdroje_p_001``.

Test 124 Zápsání nového externího zdroje typu část knihy (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_124_zapsani_externího_zdroje_p_003``.

Test 125 Zapsání nového externího zdroje typu článek v časopise (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_125_zapsani_externího_zdroje_p_004``.

Test 126 Zapsání nového externího zdroje typu článek v novinách (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_126_zapsani_externího_zdroje_p_005``.

Test 127 Zapsání nového externího zdroje typu jiný zdroj (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_127_zapsani_externího_zdroje_p_006``.

Test 128 Zápsání nového externího zdroje typu část knihy (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_128_zapsani_externího_zdroje_p_007``.

Test 129 Zapsání nového externího zdroje typu článek v časopise (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_129_zapsani_externího_zdroje_p_008``.

Test 130 Zapsání nového externího zdroje typu článek v novinách (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_130_zapsani_externího_zdroje_p_009``.

Test 131 Zapsání nového externího zdroje typu jiný zdroj (pozitivní scénář 10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel

Předpoklady
^^^^^^^^^^^

- Uživatel je přihlášen.

Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Uživatel se přihlásí
- Uživatel klikne na menu Externí zdroje -> Zapsat
- Uživatel vyplní data do formuláře
- Uživatel klikne na tlačítko Zapsat

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_131_zapsani_externího_zdroje_p_010``.

Test 136 Test Fedory pro EZ (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dat do Fedory v EZ

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog, Archivář

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření EZ
- Potvrzení EZ
- Editace EZ
- Smazání EZ

Testovací data
^^^^^^^^^^^^^^
X-BIB-1408662
X-BIB-0926116
X-BIB-0700016

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_136_test_Fedory_externi_zdroj_p_001``.

Test 137 Test Fedory pro EZ (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test zapsání dat do Fedory v EZ

Uživatelská role
^^^^^^^^^^^^^^^^
Archeolog

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

Připojení AZ
Připojení Lokalita
Editace paginace AZ
Editace paginace Lokalita
Odpojení AZ
Odpojení Lokalita


Testovací data
^^^^^^^^^^^^^^

X-BIB-000000001
X-C-9000000001A
C-K9000001

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``ez.tests.test_selenium.AkceExterniZdroj.test_137_test_Fedory_externi_zdroj_p_002``.

Heslář
------

Test 151 Test Fedory pro hesláře (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření záznamu Heslář
- Editace záznamu Heslář
- Vytvoření záznamu Heslář datace 
- Editace záznamu Heslář datace
- Smazání záznamu Heslář datace
- Vytvoření záznamu Heslář hierarchie
- Editace záznamu Heslář hierarchie
- Smazání záznamu Heslář hierarchie
- Vytvoření záznamu Heslář odkaz
- Editace záznamu Heslář odkaz
- Smazání záznamu Heslář odkaz
- Smazání záznamu Heslář

Testovací data
^^^^^^^^^^^^^^

HES-000886
HES-001066
HES-001065

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``heslar.tests.test_selenium.AkceHeslar.test_151_test_Fedora_heslar_001``.

Uživatel
--------

Test 148 Test Fedory pro uživatele (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Registrace uživatele
- Validace mailu
- Aktivace uživatele
- Vytvoření uživatele administrátorem
- Editace uživatele administrátorem
- Změna hesla administrátorem
- Smazání notifikace admin
- Editace notifikace admin
- Vytvoření notifikace admin
- Vytvoření hlídacího psa admin
- Editace hlídacího psa admin
- Smazání hlídacího psa admin
- Smazání uživatele admin

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``uzivatel.tests.test_selenium.AkceUzivatel.test_148_test_Fedora_uzivatel_001``.

Test 149 Test Fedory pro uživatele (pozitivní scénář 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel, Archeolog

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Editace uživatele Badatel
- Změna hesla Badatel
- Smazání notifikace Archeolog
- Editace notifikace Archeolog
- Vytvoření notifikace Archeolog
- Vytvoření hlídacího psa Archeolog
- Editace hlídacího psa Archeolog
- Smazaní hlídacího psa Archeolog


Testovací data
^^^^^^^^^^^^^^

U-005362
U-005357

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``uzivatel.tests.test_selenium.AkceUzivatel.test_149_test_Fedora_uzivatel_002``.

Test 150 Test Fedory pro spolupráci PAS (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Badatel, Archeolog

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^
- Vytvoření žádosti o spolupráci v PAS - Badatel
- Potvrzení spolupráce z mailu - Archeolog
- Editace spolupráce - Archeolog
- Smazání spolupráce  - Administrator

Testovací data
^^^^^^^^^^^^^^
U-000393
U-003726
U-005357
U-000408
U-000127

Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``uzivatel.tests.test_selenium.AkceUzivatel.test_150_test_Fedora_spoluprace_001``.

Test 152 Test Fedory pro organizaci (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vytvoření organizace 
- Editace organizace
- Smazání organizace

Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``uzivatel.tests.test_selenium.AkceOrganizace.test_152_test_Fedora_organizace_001``.

Test 153 Test Fedory pro osobu (pozitivní scénář 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uživatelská role
^^^^^^^^^^^^^^^^
Administrator

Předpoklady
^^^^^^^^^^^


Uživatelské kroky
^^^^^^^^^^^^^^^^^

- Vztvoření osoby
- Editace osoby
- Smazání osoby


Testovací data
^^^^^^^^^^^^^^


Očekávané výsledky
^^^^^^^^^^^^^^^^^^

- zápis dat do Fedory

Stav testu
^^^^^^^^^^

Implementován v
``uzivatel.tests.test_selenium.AkceOsoba.test_153_test_Fedora_osoba_001``.