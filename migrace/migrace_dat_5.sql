-- Kontrola po migraci

-- 1. Neni dodelana migrace tabulku nalez_dokument do tabulky nalez
alter table nalez_dokument add column komponenta_new_id integer;
-- Vlozim si nove id-cka referenci na zmigrovanie zaznamy z tabulky komponenta_dokument do komponenty do sloupce komponenta_new_id
update nalez_dokument set komponenta_new_id = sel.kid from (select k.id as kid, n.id as nid, n.komponenta_dokument from komponenta k join nalez_dokument n on n.komponenta_dokument = k.komponenta_dokument_id) sel where sel.nid = id;

-- nelez migrovat mrtve reference
update nalez_dokument set specifikace = null where specifikace = -1;

-- ted premapuji reference na heslare
-- SPATNE: update nalez_dokument set druh_nalezu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 22) sel where druh_nalezu = sel.puvodni;
-- COMMENT: zda se ze druh_nalezu je vzdy z heslare 22 - ANO PROTOZE TO BYLO BLBE
-- SPATNE: update nalez_dokument set druh_nalezu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 17) sel where druh_nalezu = sel.puvodni;

-- DOBRE:
UPDATE nalez_dokument AS n SET druh_nalezu = h.id FROM heslar AS h WHERE h.puvodni_id = n.druh_nalezu and h.nazev_heslare = 22 and n.typ_nalezu = 2;
UPDATE nalez_dokument AS n SET druh_nalezu = h.id FROM heslar AS h WHERE h.puvodni_id = n.druh_nalezu and h.nazev_heslare = 17 and n.typ_nalezu = 1;

alter table nalez_dokument add constraint nalez_dokument_druh_nalezu_fkey foreign key (druh_nalezu) references heslar(id);
-- COMMENT: 199 specifikaci je z heslare 28 a 1 z 30
-- SPATNE: update nalez_dokument set specifikace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 28) sel where specifikace = sel.puvodni;
-- SPATNE: update nalez_dokument set specifikace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 30) sel where specifikace = sel.puvodni;

-- DOBRE:
UPDATE nalez_dokument AS n SET specifikace = h.id FROM heslar AS h WHERE h.puvodni_id = n.specifikace and h.nazev_heslare = 30 and n.typ_nalezu = 2;
UPDATE nalez_dokument AS n SET specifikace = h.id FROM heslar AS h WHERE h.puvodni_id = n.specifikace and h.nazev_heslare = 28 and n.typ_nalezu = 1;

alter table nalez_dokument add constraint nalez_dokument_specifikace_fkey foreign key (specifikace) references heslar(id);

-- zmigruju zaznamy z tabulky nalez_dokument do nalez (opet nove id-cka)
alter table nalez add column nalez_puvodni_id integer;
insert into nalez(komponenta, typ_nalezu, kategorie, druh_nalezu, specifikace, pocet, poznamka, nalez_puvodni_id) select komponenta_new_id, typ_nalezu, kategorie, druh_nalezu, specifikace, pocet, poznamka, id from nalez_dokument;

-- TODO test migrace 9631 nalezu dokumentu zmigrovano

-- 2. externi_zdroj.podnazev (migrace do nazev), oznaceni (migrace do nazev)
UPDATE externi_zdroj SET nazev = externi_zdroj.nazev || ': ' || externi_zdroj.podnazev WHERE not(coalesce(externi_zdroj.podnazev, '') = '');
UPDATE externi_zdroj SET nazev = externi_zdroj.oznaceni WHERE not(coalesce(externi_zdroj.oznaceni, '') = '') AND externi_zdroj.typ = (SELECT id FROM heslar WHERE ident_cely = 'HES-001121');

-- 3. TODO vyskovy_bod.geom co kam?

-- 4. vytvoreni referenci z uzivatelu na osoby z migrace_3.sql 134 COMMENT: tady je potreba to skontrolovat. Je tam 199 lidi kteri k sobe nemaji osobu.
update uzivatel set osoba = sel.oid from (select o.id as oid, u.id as uzivatelid from osoba o join uzivatel u on u.jmeno = o.jmeno and u.prijmeni = o.prijmeni) sel where id = sel.uzivatelid;

-- 5. TODO migrace do tabulek ruian_kraj a ruian_okres popsane v souboru migrace_3.sql 127-132 COMMENT: postponed

-- Kontrola integritnich omezeni
-- COMMENT: soubory ktere nemaji vazby na nic, lze smazat viz. komentar Davida v chyby_dat.sql
delete from soubor where vazba is null;
alter table soubor alter column vazba set not null;
alter table dokumentacni_jednotka alter column vazba set not null;
