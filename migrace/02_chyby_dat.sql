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
update akce set odpovedny_pracovnik_podani_nz = null where odpovedny_pracovnik_podani_nz = -1;
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

-- DN: Pokud je vazba null a vazba druhá něco obsahuje, přesuň data do vazba
UPDATE jednotka_dokument SET vazba = vazba_druha  WHERE vazba is null AND vazba_druha is not null;

-- DN: Pokud je v jednotka_dokument.vazba totéž co ve vazba_druha, nastavit vazba_druha na null.
UPDATE jednotka_dokument SET vazba_druha = Null WHERE vazba = vazba_druha;

-- DN: Pokud je odkaz na neident_akce ve vazba a ve vazba_druha je odkaz na akci/lokalitu, tyto hodnoty je třeba prohodit
WITH prohodit AS
(
  SELECT id, vazba, vazba_druha FROM jednotka_dokument
  WHERE ((vazba_druha IN (SELECT id FROM akce WHERE jednotka_dokument.vazba_druha = akce.id))
    OR (vazba_druha IN (SELECT id FROM lokalita WHERE jednotka_dokument.vazba_druha = lokalita.id)))
    AND vazba IN (SELECT id FROM neident_akce WHERE jednotka_dokument.vazba = neident_akce.id)
)
UPDATE jednotka_dokument SET vazba = prohodit.vazba_druha, vazba_druha = prohodit.vazba FROM prohodit WHERE jednotka_dokument.id = prohodit.id;

-- DN: Smazání sirotků v neident. akcích
WITH del AS(
WITH pom AS
(
SELECT neident_akce.*
FROM neident_akce LEFT JOIN jednotka_dokument ON neident_akce.id = jednotka_dokument.vazba
WHERE (((jednotka_dokument.id) Is Null))
)
SELECT pom.id
FROM pom LEFT JOIN jednotka_dokument ON pom.id = jednotka_dokument.vazba_druha
WHERE (((jednotka_dokument.id) Is Null))
)
DELETE FROM neident_akce USING del WHERE del.id = neident_akce.id;

-- DN: Smazání neplatných vazeb
WITH del AS(
SELECT jednotka_dokument.*
FROM neident_akce RIGHT JOIN (lokalita RIGHT JOIN (akce RIGHT JOIN jednotka_dokument ON akce.id = jednotka_dokument.vazba) ON lokalita.id = jednotka_dokument.vazba) ON neident_akce.id = jednotka_dokument.vazba
WHERE (((akce.id) Is Null) AND ((jednotka_dokument.vazba) Is Not Null) AND ((neident_akce.id) Is Null) AND ((lokalita.id) Is Null))
)
UPDATE jednotka_dokument SET vazba = null FROM del WHERE jednotka_dokument.id = del.id;

WITH del AS(
SELECT jednotka_dokument.*
FROM neident_akce RIGHT JOIN (lokalita RIGHT JOIN (akce RIGHT JOIN jednotka_dokument ON akce.id = jednotka_dokument.vazba_druha) ON lokalita.id = jednotka_dokument.vazba_druha) ON neident_akce.id = jednotka_dokument.vazba_druha
WHERE (((akce.id) Is Null) AND ((jednotka_dokument.vazba_druha) Is Not Null) AND ((neident_akce.id) Is Null) AND ((lokalita.id) Is Null))
)
UPDATE jednotka_dokument SET vazba_druha = null FROM del WHERE jednotka_dokument.id = del.id;

-- DN: Doplnění hodnot do prázdných ale potřebných polí u záchranných projektů (nemělo by ale být potřeba, data se zdají být v pořádku).
UPDATE projekt SET email = '-' WHERE (typ_projektu = 2) and coalesce(email, '') = '';
UPDATE projekt SET adresa = '-' WHERE (typ_projektu = 2) and coalesce(adresa, '') = '';
UPDATE projekt SET telefon = '-' WHERE (typ_projektu = 2) and coalesce(telefon, '') = '';
UPDATE projekt SET odpovedna_osoba = '-' WHERE (typ_projektu = 2) and coalesce(odpovedna_osoba, '') = '';
UPDATE projekt SET objednatel = '-' WHERE (typ_projektu = 2) and coalesce(objednatel, '') = '';

-- Příprava pole autori v ext. zdrojích
UPDATE externi_zdroj SET autori = REPLACE(autori, ' (ed.)', '') WHERE autori LIKE '% (ed.)%';

UPDATE komponenta_dokument SET obdobi = (SELECT id FROM heslar_obdobi_druha WHERE ident_cely = 'HES-000316')
WHERE obdobi is null;

UPDATE komponenta_dokument SET areal = (SELECT id FROM heslar_areal_druha WHERE ident_cely = 'HES-000060')
WHERE areal is null;

CREATE INDEX IF NOT EXISTS soubor_id
    ON public.soubor USING btree
    (id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS dokument_soubor_fs_soubor_fs
    ON public.dokument_soubor_fs USING btree
    (soubor_fs ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS dokument_soubor_fs_dokument
    ON public.dokument_soubor_fs USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;

-- Odstranění dokumentů ZA/ZL
WITH za_zl AS
(
	SELECT dokument.id FROM dokument INNER JOIN heslar_rada ON dokument.rada = heslar_rada.id
	WHERE heslar_rada.ident_cely = 'HES-000884' OR heslar_rada.ident_cely = 'HES-000885'
)
DELETE FROM soubor USING dokument_soubor_fs WHERE soubor.id = dokument_soubor_fs.soubor_fs AND dokument_soubor_fs.dokument IN (SELECT id FROM za_zl);
WITH za_zl AS
(
	SELECT dokument.id FROM dokument INNER JOIN heslar_rada ON dokument.rada = heslar_rada.id
	WHERE heslar_rada.ident_cely = 'HES-000884' OR heslar_rada.ident_cely = 'HES-000885'
)
DELETE FROM dokument_soubor_fs USING za_zl WHERE za_zl.id = dokument_soubor_fs.dokument;

-- Běží cca 10 minut
CREATE INDEX IF NOT EXISTS jednotka_dokument_dokument
    ON public.jednotka_dokument USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS komponenta_dokument_dokument_idx
    ON public.komponenta_dokument USING btree
    (jednotka_dokument ASC NULLS LAST)
    TABLESPACE pg_default;
WITH za_zl AS
(
	SELECT dokument.id FROM dokument INNER JOIN heslar_rada ON dokument.rada = heslar_rada.id
	WHERE heslar_rada.ident_cely = 'HES-000884' OR heslar_rada.ident_cely = 'HES-000885'
)
DELETE FROM jednotka_dokument USING za_zl WHERE za_zl.id = jednotka_dokument.dokument;

CREATE INDEX IF NOT EXISTS extra_data_dokument_idx
    ON public.extra_data USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS historie_dokumentu_dokument_idx
    ON public.historie_dokumentu USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS jednotka_dokument_dokument_idx
    ON public.jednotka_dokument USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS odkaz_dokument_idx
    ON public.odkaz USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS soubor_dokument_idx
    ON public.soubor USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS tvar_dokument_idx
    ON public.tvar USING btree
    (dokument ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS dokument_id_idx
    ON public.dokument USING btree
    (id ASC NULLS LAST)
    TABLESPACE pg_default;

WITH za_zl AS
(
	SELECT dokument.id FROM dokument INNER JOIN heslar_rada ON dokument.rada = heslar_rada.id
	WHERE heslar_rada.ident_cely = 'HES-000884' OR heslar_rada.ident_cely = 'HES-000885'
)
DELETE FROM dokument USING za_zl WHERE za_zl.id = dokument.id;


-- Oprava špatného použití hesla anonym
UPDATE dokument SET autor = replace(autor, 'anonym, anonym', 'anonym') WHERE autor LIKE ('%anonym, anonym%');
UPDATE dokument SET autor = replace(autor, 'Anonym, Anonym', 'anonym') WHERE autor LIKE ('%Anonym, Anonym%');
UPDATE akce SET vedouci_akce_ostatni = replace(vedouci_akce_ostatni, 'anonym, anonym', 'anonym') WHERE vedouci_akce_ostatni LIKE ('%anonym, anonym%');
UPDATE akce SET vedouci_akce_ostatni = replace(vedouci_akce_ostatni, 'Anonym, Anonym', 'anonym') WHERE vedouci_akce_ostatni LIKE ('%Anonym, Anonym%');
UPDATE externi_zdroj SET autori = replace(autori, 'anonym, anonym', 'anonym') WHERE autori LIKE ('%anonym, anonym%');
UPDATE externi_zdroj SET autori = replace(autori, 'Anonym, Anonym', 'anonym') WHERE autori LIKE ('%Anonym, Anonym%');
UPDATE externi_zdroj SET sbornik_editor = replace(sbornik_editor, 'anonym, anonym', 'anonym') WHERE sbornik_editor LIKE ('%anonym, anonym%');
UPDATE externi_zdroj SET sbornik_editor = replace(sbornik_editor, 'Anonym, Anonym', 'anonym') WHERE sbornik_editor LIKE ('%Anonym, Anonym%');

-- Oprava chybné null hodnoty pro evidenční číslo nálezu
UPDATE samostatny_nalez SET inv_cislo = '' WHERE inv_cislo = '-1';

-- Úprava nesmyslných přístupností u akcí
UPDATE akce SET pristupnost = 1 WHERE pristupnost = 2;

-- Oprava falešně negativních DJ
UPDATE dokumentacni_jednotka SET negativni_jednotka = false FROM komponenta WHERE komponenta.parent = dokumentacni_jednotka.id AND dokumentacni_jednotka.negativni_jednotka = true;

-- Oprava emailových adres na lower-case
UPDATE user_storage SET email = LOWER(email);
