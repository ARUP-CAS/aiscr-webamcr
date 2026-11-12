# Design

## Context

Příkaz `anonymizace_dat` je rozdělený na sekce (`uzivatele`, `oznamovatele`, `logy`, `texty`, `geometrie`, `pid`), které zapisují dávkově přes `QuerySet.update()` a `bulk_update` s potlačenými signály. Formát zástupných hodnot drží `utils/anonymizace.py`, geometrické operace `utils/anonymizace_geometrie.py`. Důvody přeskočení se dnes sbírají až během zápisu a souhrn na konci je jen vypíše. Motivace viz `proposal.md`, požadavky viz `specs/anonymizace-dat/spec.md`.

Ověřeno v kopii aktuální produkce (`prod_old`, stav k 11. 11. 2026): 7 394 účtů, z toho 4 260 napojených na osobu a 150 s ORCID; na osobu `OS-007414` je napojeno právě 198 účtů a jsou to přesně všechny účty s příjmením „Anonym“ (jeden z nich je administrátor), takže změna pravidla výjimky nemění množinu vyloučených účtů; 14 krajů, 4 s e-mailem; 3 042 chráněných PIANů, z toho 52 se zdrojovou geometrií porušující pravidla databáze; historie `KAT` u chráněných záznamů nyní žádná (v kopii ze srpna 2026 byly dva případy, záznamy se mezitím zveřejnily); žádný okres nemá méně než dva katastry.

Produkce zatím neprošla nasazením přechodu katastrů na EPSG:5514 (issue #372) a **žádný okres nemá vyplněnou hranici** – plní ji až plný sync `aktualizuj_ruian_shp`, krok prvního nasazení. Bez hranic okresů sekce `geometrie` nemá kde generovat nové polohy.

## Goals / Non-Goals

**Goals:**
- Nevyřešitelné chráněné polohy zjistit před prvním zápisem, ne v půlce běhu.
- Kontrola a zápis musí rozhodovat stejnými podmínkami, aby se nerozešly.

**Non-Goals:**
- Záznamy osob (`Osoba`) a kontaktní údaje organizací zůstávají beze změny.
- Úprava oprávnění a Digiarchivu kvůli historii `KAT` – řešeno mimo tento repozitář.
- Doplnění trvalé specifikace o chování příkazu zavedené dříve.
- Explicitní karanténa nevyřešitelných záznamů bez zastavení běhu.

## Decisions

**Předběžná kontrola jako samostatný krok před sekcemi.** Spustí se v `handle` před první sekcí, pokud je vybraná sekce `geometrie`, a v dry-runu se jen vypíše. Kontrolu tvoří množinové dotazy nad stejnými predikáty, které používají sekce (chráněnost záznamu, okres, hranice okresu, počet katastrů okresu, možnost vypnout trigger). Predikáty se proto vytáhnou do sdílených metod volaných z kontroly i ze sekcí. *Alternativa:* nechat běh dojít a selhat na konci – zamítnuto, protože po částečném zápisu je databáze nekonzistentní a uživatel výslovně chce vědět „kde a kolik“ na začátku.

**Co kontrola považuje za nevyřešitelné.** Po uplatnění náhradních řešení zbývají jen strukturální stavy, které náhoda nezmění: PIAN v okrese bez hranice; katastrální PIAN v okrese bez jiného katastru; PIAN se zdrojovou geometrií porušující pravidla databáze, když trigger nejde vypnout; chráněný archeologický záznam nebo projekt, jehož katastr nejde nahradit, protože okres nemá jiný katastr. Náhodná selhání (minimální posun, hranice listu) mají v produkčních datech zanedbatelnou pravděpodobnost a pokrývá je závěrečná kontrola výsledku.

**Náhradní poloha PIANu mimo list ZM50.** Když generátor pro klíč (okres, list ZM50) nic nevrátí, použije se klíč okresu a `zm10` i `zm50` se přepočítají z nové polohy. `ident_cely` se nemění, takže u takového PIANu číslo listu v identu přestane odpovídat sloupci `zm50`; na testovacích datech je to přijatelné a vypíše se samostatným důvodem. Totéž platí pro katastrální PIAN: když v listu není jiný katastr, vybere se kterýkoli jiný katastr okresu.

**Odstranění geometrie bodového záznamu.** Projekt, samostatný nález a dokument mají geometrii nepovinnou, takže při nemožné poloze se vynuluje `geom` i `geom_sjtsk`. Samostatný nález zároveň dostane náhodný katastr okresu, nebo žádný, když okres neznáme; hlavní katastr projektu už nahrazuje sekce náhodných katastrů.

**Výjimka podle osoby.** Identifikátor `OS-007414` se drží jako konstanta v `utils/anonymizace.py`, primární klíč osoby se dohledá na začátku sekce. Chybí-li osoba, vypíše se varování a vyloučení zůstanou jen administrátoři – lokální databáze tuto osobu nemají a blokovat kvůli tomu běh by znemožnilo vývoj.

**Doména `anonymizace.invalid`.** RFC 2606 rezervuje nejvyšší doménu `.invalid` pro adresy, které nesmí být doručitelné; `example.cz` je běžně registrovatelná. Předfiltry idempotence pracují s novou doménou, takže opakovaný běh přepíše i starší hodnoty v `example.cz`.

**Historie `KAT`.** Poznámka se vynuluje jedním `UPDATE` přes vazbu historie chráněných archeologických záznamů, projektů a samostatných nálezů, v sekci `texty`, která už teď pracuje s chráněnými záznamy.

**Výsledek běhu.** Souhrn přidá počet nenahrazených chráněných poloh a katastrů (podle důvodů, které nejsou náhradním řešením) a s chybami ho promítne do `CommandError`. Hláška o úspěchu se vypíše jen při nule obou.

**Chybějící hranice okresů se řeší postupem, ne kódem.** Jde o dočasný stav do nasazení nové verze na produkci a aktualizace katastrů. Příkaz proto hranici okresu z katastrů nedopočítává; předběžná kontrola takové záznamy nahlásí a běh zablokuje. Do docstringu příkazu (a tím do generované dokumentace) a do postupu prvního nasazení se doplní poznámka, že na testovacím serveru je před anonymizací potřeba spustit plný sync `aktualizuj_ruian_shp`, dokud ho nemá produkce. *Alternativa:* dopočítat hranici sjednocením katastrů okresu – zamítnuto jako kód pro dočasný stav.

## Risks / Trade-offs

- [Aktuální produkce nemá historii `KAT` u chráněných záznamů] → testy založí vlastní data; požadavek zůstává, protože taková data mohou vzniknout.
- [Na testovacím serveru někdo zapomene před anonymizací spustit sync katastrů] → předběžná kontrola běh zablokuje před zápisem a hláška odkáže na sync.
- [Predikáty kontroly a sekcí se mohou rozejít] → sdílené metody a test, který porovná výsledek kontroly s tím, co sekce opravdu přeskočí.
- [PIAN přesunutý mimo list ZM50 má ident neodpovídající listu] → samostatný důvod ve výpisu; `check_pian_properties` ho nahlásí.
- [Blokace zastaví migraci na TR kvůli jednomu vadnému záznamu] → výpis identifikátorů umožní data opravit před dalším pokusem.

## Migration Plan

Nasazení s další verzí aplikace. Na testovacím serveru: obnova kopie produkce → migrace → plný sync `aktualizuj_ruian_shp` (dokud ho neprošla produkce) → `anonymizace_dat` → generování metadat. Opakovaný běh nad již anonymizovanými daty přepíše adresy do domény `.invalid`.
