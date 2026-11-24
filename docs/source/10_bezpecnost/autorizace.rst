Autorizace
==========

Hlavní a doplňkové role
-----------------------

Matice oprávnění pracuje se čtyřmi hlavními rolemi: badatel, archeolog,
archivář a administrátor (ID skupin 1–4, sloupce B–E matice). Hlavní role
se vybírá pouze z těchto skupin. Aktivní uživatel bez některé z nich používá
roli badatele. Ostatní členství jsou doplňková: nemění hlavní roli a mohou
zpřístupňovat samostatně chráněné funkce, například úpravu překladů.

Přístup k seznamu překladových souborů AMČR prochází dvěma kontrolami. Matice
povoluje hlavní roli administrátora; Rosetta navíc vyžaduje skupinu
``ROLE_UPRAVA_TEXTU`` (ID 6). Administrátor bez této skupiny proto neprojde
kontrolou Rosetty. Badatel, archeolog ani archivář neprojdou kontrolou matice
seznamu, ani když doplňkovou skupinu mají.

Vyhodnocení matice
------------------

Matice v ``webclient/core/resources/uzivatelska_prava.csv`` obsahuje pravidla
pro URL vzory a případně také pojmenované akce. Prázdná akce je platné pravidlo
pouze pro URL. Jedna akce se může vyskytovat u více URL. URL se porovnává se
vzorem z Django resolveru včetně převodníků a koncového lomítka.

Při importu se některé neomezené povolující záznamy záměrně odstraní
kompakcí. Pokud pro hlavní roli a URL nebo akci nezůstane žádný odpovídající
záznam, současné vyhodnocení přístup **povolí**. Existuje-li více odpovídajících
záznamů, stačí splnění jednoho z nich; pokud všechny selžou, přístup se zamítne.
Jednotlivé podmínky mohou zohledňovat stav, vlastnictví, přístupnost a existující
výjimky pro záznamy či soubory.

Kontrola zdrojové matice není běhovou politikou „vše chybějící zakázat“.
Chybějící databázový záznam zůstává povolující i po přímé ruční úpravě nebo
neúplném importu mimo tuto službu. Pokrytí parametrického URL vzoru také
nedokazuje existenci pravidla pro každou jednotlivou hodnotu parametru,
například ``typ_vazby``.

Balíček Rosetta obsahuje i vlastní regulární URL vzory. Běžné URL s ASCII
indexem zachytí dřívější routy AMČR. U ne-ASCII číslic indexu mohou formulář
a stažení přejít na routy balíčku: ty používají samostatnou kontrolu skupiny
pro překlady a jiný klíč oprávnění než routy AMČR. Toto stávající chování se
nemění; při změně rout nebo ochrany je nutné znovu posoudit příslušné výjimky.

Kontrola zdroje a výjimky
-------------------------

Z kořene repozitáře lze celou matici ověřit bez zápisu do databáze::

    python webclient/manage.py check_permission_policy --settings=webclient.settings.permissions_check

Volba ``--file cesta/soubor.csv`` nebo ``--file cesta/soubor.xlsx`` ověří jiný
úplný soubor. Příkaz kontroluje hlavičky, role a jejich podmínky, známé a
nepokryté akce, chybějící i zastaralé URL vzory a dostupné doslovné odkazy na
akce v kódu. Při chybách vypíše jejich umístění a skončí s nenulovým kódem.
Izolované nastavení načte stejný produkční URL strom včetně Rosetty, ale
neotevírá spojení s PostgreSQL, Redisem ani Fedorou.

Lokální běh vyžaduje instalované projektové Python závislosti podle verzovaných
``webclient/requirements-dev.txt`` a ``webclient/requirements-docs.txt`` a
nativní knihovny GDAL, GEOS a libmagic. Na Ubuntu je poskytují balíčky
``libgdal-dev``, ``libgeos-dev`` a ``libmagic1``. Stejný příkaz používá hook
pre-commit a sestavení runtime obrazu; neplatná matice tak zastaví sestavení
před publikací obrazu.

Výjimky pro nezávisle chráněné routy jsou uvedeny jako přesné vzory v
``ROSETTA_ROUTE_EXCEPTIONS`` v ``webclient/core/permission_validation.py``;
každá uvádí důvod a existující ochranu. Před přidáním či změnou výjimky je
nutné ověřit skutečně dosažitelný pohled, jeho ochranu a pořadí překrývajících
se rout a doplnit test. Stávající vynechání prefixů administrace a debug
toolbaru odpovídá jejich vlastní ochraně; nové plošné výjimky se nepřidávají.

Import a obnova
---------------

Administrátor může nahrát úplnou CSV/XLSX matici v administraci nebo znovu
načíst verzovaný CSV soubor. Příkazový import se spouští z adresáře
``webclient/`` v běžném provozním nastavení::

    python manage.py import_permissions

Všechny vstupy používají stejnou validaci před smazáním stávajících záznamů.
Nahrazení a kompakce probíhají v jedné transakci: neplatný soubor, chybějící
standardní skupina nebo chyba zápisu zachovají předchozí politiku. CLI vrátí
nenulový kód a administrace zobrazí chybu místo potvrzení úspěchu. Po opravě
zdroje spusťte kontrolu znovu a ověřte přístup dotčených hlavních i doplňkových
rolí.

Importy je nutné provozně koordinovat: administrátoři spouštějí nahrání,
opětovné načtení a CLI import jednotlivě a mimo nasazení či restarty, které
rovněž importují matici. Transakce sama souběžné importy neřadí. Při selhání
startovního importu se webový proces nespustí; předcházející migrace již mohly
proběhnout. Nasazení, které obchází standardní entrypoint, musí úspěšný import
nebo již nainstalovanou politiku ověřit před zahájením provozu.

Nasazovací wrapper zapíše novou verzi do ``logs/last_deployment_tag.txt`` až
po úspěšném zdravotním testu nového místního webového kontejneru odpovídajícího
aktuální službě a obrazu. Kontrola má omezenou dobu čekání; pokud je úloha na
jiném Swarm uzlu a místní stav nelze ověřit, skončí chybou a ponechá předchozí
úspěšnou verzi. Výchozí limit je 900 sekund, s intervalem 5 sekund. Zachovaná
hodnota je podklad pro operátorem schválenou obnovu, nikoli automatický návrat:
předchozí služba již mohla být při nasazení odstraněna.
