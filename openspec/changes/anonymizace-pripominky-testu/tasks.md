# Tasks

Ověřovací příkazy (spouštěné z `webclient/`):

- testy: `../../penv14/Scripts/python.exe manage.py test core.tests.test_anonymizace --settings=webclient.settings.local_settings`
- hooky: `../../penv14/Scripts/python.exe -m pre_commit run --files <změněné soubory>` z kořene repozitáře

## 1. Nedoručitelné adresy

- [x] 1.1 Změnit `ANONYM_DOMENA` na `anonymizace.invalid` a upravit docstringy, které tvrdí rezervovanost; ověřit testem, že všechny zástupné adresy končí na `.invalid`
- [x] 1.2 Nahradit neprázdné e-maily krajů tvarem `kraj_{kod}@anonymizace.invalid` (sekce `uzivatele`); ověřit databázovým testem s krajem s e-mailem a bez něj
- [x] 1.3 Ověřit databázovým testem, že oznamovatel se zástupnou adresou v `example.cz` dostane při opakovaném běhu adresu v `.invalid`

## 2. Uživatelé

- [x] 2.1 Přidat konstantu `IDENT_ANONYMNI_OSOBY = "OS-007414"` a nahradit výjimku podle příjmení výjimkou podle napojené osoby; chybějící osoba vede k varování a vyloučení jen administrátorů; ověřit databázovými testy pro napojený účet, účet „Anonym“ bez napojení a databázi bez osoby
- [x] 2.2 Anonymizovaným účtům vynulovat `osoba` a `orcid`, záznam osoby nechat beze změny; ověřit databázovým testem
- [x] 2.3 Aktualizovat docstring třídy `Command` (výjimky z anonymizace, odpojení od osob)

## 3. Chráněné texty a historie

- [x] 3.1 Omezit sekci `texty` na záznamy s přístupností vyšší než A podle modelu (projekt včetně neurčené přístupnosti, archeologický záznam, akce, lokalita, ADB, samostatný nález); ověřit databázovým testem s veřejnou i chráněnou lokalitou a akcí
- [x] 3.2 V sekci `texty` vynulovat poznámku historie typu `KAT` u chráněných archeologických záznamů, projektů a samostatných nálezů; ověřit databázovým testem s chráněným a veřejným záznamem
- [x] 3.3 Upravit docstring sekce a třídy `Command` (rozsah textů, historie)

## 4. Náhradní řešení polohy

- [x] 4.1 PIAN bez polohy v průniku okresu a listu ZM50 přesunout kamkoli v okresu a přepočítat `zm10` i `zm50`, se samostatným důvodem ve výpisu; ověřit testem s okresem, jehož list ZM50 polohu neumožní
- [x] 4.2 Katastrální PIAN bez kandidáta v listu ZM50 nahradit jiným katastrem okresu a přepočítat listy; ověřit testem
- [x] 4.3 Bodovému záznamu bez možné polohy vynulovat `geom` a `geom_sjtsk`; samostatnému nálezu nahradit katastr náhodným katastrem okresu nebo ho vynulovat; ověřit databázovým testem s okresem bez hranice

## 5. Předběžná kontrola a výsledek běhu

- [x] 5.1 Vytáhnout predikáty nevyřešitelnosti (okres bez hranice, okres bez jiného katastru, vadná zdrojová geometrie bez možnosti vypnout trigger) do sdílených metod a použít je v sekcích; stávající testy musí projít beze změny
- [x] 5.2 Přidat předběžnou kontrolu před první sekcí: počty a identifikátory podle důvodu, při nálezu `CommandError` bez zápisu; v dry-runu jen výpis; ověřit testem, že s nevyřešitelným PIANem se nic nezapíše a návratový kód je nenulový
- [x] 5.3 Souhrn běhu: nenahrazené chráněné polohy a katastry i chyby vedou na `CommandError`, hláška o úspěchu jen při nule; ověřit testem s chybou převodu a s přeskočeným záznamem
- [x] 5.4 Hláška předběžné kontroly pro okresy bez hranice odkáže na plný sync `aktualizuj_ruian_shp`; ověřit testem s okresem bez hranice
- [x] 5.5 Doplnit poznámku o nutnosti plného syncu katastrů před anonymizací (dokud ho neprošla produkce) do docstringu třídy `Command` a do postupu prvního nasazení v `docs/source/02_instalace_nasazeni/ruian_sync_nasazeni.rst`; ověřit, že se poznámka objeví v přegenerované `management_commands.rst`
- [x] 5.6 Přegenerovat dokumentaci hookem a spustit testy a hooky nad všemi změněnými soubory

## 6. Uzavření

- [x] 6.1 Ověřit změnu proti specifikaci (`openspec validate anonymizace-pripominky-testu`) a zapsat záznam do `.agents/reports/usage/`

## Workflow follow-up

- Po sloučení archivovat change a přenést specifikaci `anonymizace-dat` do `openspec/specs/`.
- Doplnit do specifikace zbytek chování příkazu z [ARUP-CAS/aiscr-webamcr#4333](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4333).
- Spustit příkaz na testovacím serveru a ověřit body 3 a 6 nad skutečnými daty.
