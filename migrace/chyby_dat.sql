--1. Neexistujici vlastnik s id 66050 v tabulce souboru (nelze smazat protoze tam bude not-null constraint)
---- COMMENT: v tabulce soubor ve sloupci vlastnik je uvedeno cislo 66050 u 6078 zaznamu. Toto id neexituje v tabulce uzivatel takze nelze pridat foreign key. Smazat tohoto vlastnika nejde taky, protoze vlasnik je povinny.
---- DN: Jde o soubory projektové dokumentace z úvodní migrace dat do AMČR. Vlastníka lze změnit na 598610 (amcr@arup.cas.cz)
update soubor set vlastnik = 598610 where vlastnik = 66050;
-- DONE 2. Projekt s id 1009028 nema ident_cely (nelze pridat not-null constraint)
---- COMMENT: Jde ale jen o jeden projekt (select * from projekt where id = 1009028;)
---- delete from projekt where id = 1009028; dalsi nulove projekty TODO zeptat se zda je mozne je smazat 1058367
---- DN: Projekt smazán. Patrně vznikl chybou při zápisu.
--3. 299 souboru nema referenci ani na projekt, ani na dokument ani na samostatny_nalez
---- COMMENT: select * from soubor left join dokument_soubor_fs ON soubor.id = dokument_soubor_fs.soubor_fs where dokument_soubor_fs.dokument not in (select id from dokument) and projekt is null and samostatny_nalez is null;
---- DN: takto nalezené sirotky lze bez náhrady vymazat (nezapomenout smazat i ve fs) - uděláme ručně před migrací
--4. V produkcnich datech jsou projekty ktere nemaji datum zapisu. Projekty ktere maji odovedneho_pracovnika_archivace ale nemaji datum_archivace
---- COMMENT: select ident_cely, stav from projekt where odpovedny_pracovnik_archivace is not null and datum_archivace is null;)
---- DN:
update projekt set odpovedny_pracovnik_archivace = null where odpovedny_pracovnik_archivace is not null and datum_archivace is null and stav = 5;
---- projekty, které nemají datum_zapisu jsem nenašel, resp. jsou to jen projekty ve stavu 0, což je v pořádku; datetime_born skutečně chybět může (pro projekty vzniklé před zavedením atributu)
--5. Projekty ktere maji odpovedny_pracovnik_navrhu_zruseni ale nemaji datum_navrzeni_zruseni. Nejde kvuli tomu udelat migraci duvod_navrzeni_zruseni.
---- COMMENT: select ident_cely, stav from projekt where odpovedny_pracovnik_navrhu_zruseni is not null and datum_navrzeni_zruseni is null;
---- DN:
update projekt set odpovedny_pracovnik_navrhu_zruseni = null where odpovedny_pracovnik_navrhu_zruseni is not null and datum_navrzeni_zruseni is null and stav < 7;
-- DONE 6. Nelze pridat unique constraint do kladyzm.nazev je tam mnoho zaznamu ktere tam maji N_A.
-- DN: Sloupec odstraníme, není k ničemu potřebný a obsahuje částečně poškozená data (chyba kódování textu).
ALTER TABLE kladyzm drop column nazev;
-- DONE 7. Nelze pridat not null pro auth_level protoze tam je 71 uzivatelu kteri to maji NULL. Tohle se uz resilo a mam pocit ze auth_level maji NULL kdyz jsou to neaktivni ucty ale nejsem si jisty.
update user_storage set auth_level = 0 where auth_level is null;
-- DONE 8. nelze pridat not null na uzivatel.heslo a email protoze uzivatel s ID -1 nema heslo ani email
---- COMMENT: existuje jedna akce ktera na neho ukazuje asi to je chyba, to same plati pro jeden externi zdroj a pian.potvrdil, 10 pripadu pian.vymezil, 7 pripadu projekt.odpovedny_pracovnik_zahajeni, 808 pripadu dokument.odpovedny_pracovnik_archivace, historie.uzivatel tam ma taky -1 (nastavim je na tebe, protoze tam chci ponechat not null constraint)
update akce set odpovedny_pracovnik_archivace_zaa = null where odpovedny_pracovnik_archivace_zaa = -1;
update externi_zdroj set odpovedny_pracovnik_vlozeni = null where odpovedny_pracovnik_vlozeni = -1;
update pian set potvrdil = null where potvrdil = -1;
update pian set vymezil = null where vymezil = -1;
update projekt set odpovedny_pracovnik_zahajeni = null where odpovedny_pracovnik_zahajeni = -1;
alter table dokument alter column odpovedny_pracovnik_archivace drop not null;
update dokument set odpovedny_pracovnik_archivace = null where odpovedny_pracovnik_archivace = -1;

--9. Mapovani pilotu (je jich 29) neni k dispozici -> jsou tam nejednoznacne prijmeni + nekdy tam je jmeno a prijmeni a nekdy jen prijmeni
---- DN: nakonec nechat let.pilot jako text; když vidím data, nemá smysl to předělávat
--10. Heslarum chybi preklad: heslar_letiste, heslar_specifikace_data, heslar_typ_organizace
---- DN: dořešíme po migraci, zatím vložit zástupné hodnoty
--11. Duplicity v heslarech (v sloupci en a v sloupci nazev)
---- COMMENT: preklad 'hradba' a 'val' v heslar_objekt_druh je stejny, taky problem je v heslari heslar_specifikace_objektu_druha u sloupce heslo (stribro je tam 2x) dalsi jsem zatim nenasel
---- DN: heslar_specifikace_objektu_druha - zde se to vyřeší smazáním části hesel ještě před převodem, resp. použít vždy heslo, kde poradi <99999 (duplicit je tam jinak mnoho)
update heslar_objekt_druh set en = 'defensive wall' where nazev = 'hradba';
--Jiz opravene (mam SQL):
-- DONE 1. V nekterych pripadech je v databazi v poli dalsi_katastry nazev katastru, ktery je uz uveden ve sloupci katastr (jako hlavni) - taky jsou duplicity v sloupci dalsi_katastry
-- DONE 2. Duplicity v pripade dalsi_katastry u projektu
-- DONE 3. Duplicity v pripade typ_dokumentu_posudek v dokumentech
-- DONE 4. Duplicity v dokument.autor
update samostatny_nalez set odpovedny_pracovnik_archivace = null where odpovedny_pracovnik_archivace = -1;
update samostatny_nalez set katastr = null where katastr = -1;

-- DN: Pokud je v jednotka_dokument.vazba totéž co ve vazba_druha, nastavit vazba_druha na null.
UPDATE jednotka_dokument SET vazba_druha = Null WHERE vazba = vazba_druha;

-- DN: Doplnění hodnot do prázdných ale potřebných polí u záchranných projektů (nemělo by ale být potřeba, data se zdají být v pořádku).
UPDATE projekt SET email = '-' WHERE (typ_projektu = 2) and email is null;
UPDATE projekt SET adresa = '-' WHERE (typ_projektu = 2) and adresa is null;
UPDATE projekt SET telefon = '-' WHERE (typ_projektu = 2) and telefon is null;
UPDATE projekt SET odpovedna_osoba = '-' WHERE (typ_projektu = 2) and odpovedna_osoba is null;
UPDATE projekt SET objednatel = '-' WHERE (typ_projektu = 2) and objednatel is null;

-- Příprava pole autori v ext. zdrojích
UPDATE externi_zdroj SET autori = REPLACE(autori, ' (ed.)', '') WHERE autori LIKE '% (ed.)%';
