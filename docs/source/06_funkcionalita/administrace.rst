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

Organizace a jejich hierarchie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organizace tvoří hierarchii prostřednictvím pole ``soucast``. Při přidání, změně nebo
smazání organizace v administraci jsou tyto operace zakázány, pokud Redis potvrzuje fázi
``importing`` hromadného importu. Ve fázích validace a čekání na schválení se toto omezení
neuplatňuje. Pokud stav importu nelze v Redis ověřit, změny se z bezpečnostních důvodů také
zakážou a do logu se zapíše chyba.

Vlastnická oprávnění archeologů zahrnují jejich organizaci a její potomky. Výsledek
vyhledání podstromu se cacheuje v instanci uživatele; po uložení změny organizace přes
model se při dalším přístupu obnoví.
Pokud podstrom obsahuje cyklus, systém jej zaloguje a při procházení přeskočí vazby tvořící
cyklus. Oprávnění tak zahrne bezpečné větve dostupné mimo cyklus, ale nepovolí přístup přes
cyklické vazby.

Před importem se kontrolují dopředné reference a cykly vznikající na změněných vztazích
organizací a jejich dosažitelných předcích; nesouvisející historické cykly import
neblokují. Prázdná hodnota ``soucast`` umožňuje vztah odstranit a cyklus opravit.
Pokud dávka obsahuje organizační záznamy, při závěrečném úklidu po importní fázi se navíc
provede diagnostická kontrola celé hierarchie, a to i po chybě nebo rollbacku. Nalezené
cykly se pouze zapíší do logu s ID úlohy a nemění výsledek importu; případná chyba této
kontroly rovněž nezastaví závěrečný úklid.


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
* Překlady je možné importovat a exportovat pomocí standardních PO souborů; import nejdřív připraví
  zálohu původního souboru, nový ``.po`` i ``.mo`` a teprve pak je jednotlivě nahradí. Chyba při
  přípravě ponechá oba katalogy i seznam záloh beze změny. Každý soubor se nahradí v jednom kroku,
  takže aplikace nenačte rozepsaný soubor z tohoto importu
* Náhrada katalogů netvoří společnou transakci. Při chybě během přejmenování může zůstat zveřejněná
  záloha nebo nové ``.po`` s původním ``.mo``; aplikace pak překládá podle původního ``.mo``.
  Import zobrazí chybu a odstraní zbývající dočasné soubory. Automatická obnova při ukončení procesu
  není zaručena
* Uložený, importovaný nebo ze zálohy obnovený překlad v katalozích aplikace (``LOCALE_PATHS``, runtime
  volume ``/vol/web/locale``) se přebírá bez restartu. Každý webový proces kontroluje změny na začátku
  požadavku a worker Celery na začátku úlohy, nejvýše jednou za výchozích 60 sekund. Platná změna se
  převezme při další způsobilé kontrole; nečinný proces čeká na další požadavek či úlohu. E-mailová část
  platí, jakmile služby Celery běží s verzí obsahující tuto kontrolu (nasazení, které aktualizuje jen
  web a proxy, Celery neaktualizuje – viz
  `ARUP-CAS/aiscr-webamcr#4541 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4541>`_)
* Při chybě načítání, chybějícím katalogu nebo zjištěné změně souborů během načítání proces ponechá
  dříve načtené překlady. Porovnání metadat před načtením a po něm omezuje souběh se zápisem, ale
  nezaručuje konzistentní snímek: změna tam a zpět se shodnými metadaty může uniknout
* Pro stejný neúspěšný stav se zapíše jedno varování. Změněný otisk souborů dovolí nový pokus při další
  běžné kontrole; nezměněný neúspěšný stav se znovu zkusí nejdříve za pět minut od posledního pokusu.
  Opakovaná selhání stejného stavu už nevarují. Tato pevná prodleva umožňuje zotavení z přechodné chyby
  čtení i bez dalšího zápisu; každý proces při trvajícím nezměněném chybném stavu spotřebuje nejvýše
  jeden pokus za pět minut.
  K prodlevě se může přidat čekání na běžný interval kontroly a na požadavek či úlohu. Nově spuštěnému
  procesu, který platný katalog dříve nenačetl, mechanismus nezaručí dostupnost starých překladů
* Katalogy Djanga a knihoven třetích stran, které Rosetta také zobrazuje, jsou součástí image; jejich
  změna se projeví až s novou image
* Totéž platí po nasazení nové verze: procesy, které katalogy načetly ještě před jejich aktualizací,
  převezmou nové katalogy automaticky a překlady přidané ve verzi se zobrazí bez druhého restartu
* Úprava provedená v běžící aplikaci platí jen do dalšího nasazení nebo restartu webového kontejneru,
  kdy katalogy nahradí obsah z repozitáře (postup přenosu úpravy do repozitáře popisuje
  :doc:`preklady`)
* Interval kontroly změn určuje nastavení ``TRANSLATION_CATALOG_CHECK_INTERVAL`` (výchozí 60 sekund);
  hodnota ``None`` vypne kontrolu a Django zachová běžné načítání překladů až při použití a jejich
  ukládání v procesu. Změna nastavení vyžaduje doručení konfigurace do procesů; přepínač nemá vlastní
  proměnnou prostředí pro změnu za běhu
* Akce pro restart aplikace zůstává k dispozici jako záložní možnost pro okamžité projevení změn ve webové
  aplikaci
