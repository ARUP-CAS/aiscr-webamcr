-- Nova tabulka historie
-- 1. historie
CREATE SEQUENCE public.historie_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE historie (
    id integer DEFAULT nextval('public.historie_id_seq'::regclass) not null,
    datum_zmeny timestamp with time zone not null,
    typ_zmeny integer not null,
    uzivatel integer not null,
    poznamka text,
    vazba integer not null,
    PRIMARY KEY (id)
);
-- 2. historie_vazby
CREATE SEQUENCE public.historie_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE historie_vazby (
    id integer DEFAULT nextval('public.historie_vazby_id_seq'::regclass) not null,
    typ_vazby text not null,
    PRIMARY KEY (id)
);

-- Nove sloupce s cizim klicem na historie_vazby
-- 1. akce.historie
alter table akce add column historie integer;
alter table akce add constraint akce_historie_fkey foreign key (historie) references historie_vazby(id);
-- 2. dokument.historie
alter table dokument add column historie integer;
alter table dokument add constraint dokument_historie_fkey foreign key (historie) references historie_vazby(id);
-- 3. externi_zdroj.historie
alter table externi_zdroj add column historie integer;
alter table externi_zdroj add constraint externi_zdroj_historie_fkey foreign key (historie) references historie_vazby(id);
-- 4. lokalita.historie
alter table lokalita add column historie integer;
alter table lokalita add constraint lokalita_historie_fkey foreign key (historie) references historie_vazby(id);
-- 5. pian.historie
alter table pian add column historie integer;
alter table pian add constraint pian_historie_fkey foreign key (historie) references historie_vazby(id);
-- 6. projekt.historie
alter table projekt add column historie integer;
alter table projekt add constraint projekt_historie_fkey foreign key (historie) references historie_vazby(id);
-- 7. samostatny_nalez.historie
alter table samostatny_nalez add column historie integer;
alter table samostatny_nalez add constraint samostatny_nalez_historie_fkey foreign key (historie) references historie_vazby(id);
-- 8. user_storage.historie
alter table user_storage add column historie integer;
alter table user_storage add constraint user_storage_historie_fkey foreign key (historie) references historie_vazby(id);
-- 9. vazba_spoluprace.historie
alter table vazba_spoluprace add column historie integer;
alter table vazba_spoluprace add constraint vazba_spoluprace_historie_fkey foreign key (historie) references historie_vazby(id);

-- Migrace sloupcu do historie
-- Akce
-- 1. akce.odpovedny_pracovnik_zapisu (typ_tranzakce = 1), odpovedny_pracovnik_autorizace (typ_tranzakce = 2), odpovedny_pracovnik_zamitnuti neni potreba migrovat, odpovedny_pracovnik_archivace (typ_tranzakce = 8), odpovedny_pracovnik_podani_nz (typ_tranzakce = 6), odpovedny_pracovnik_archivace_zaa (typ_tranzakce = 4), odpovedny_pracovnik_vraceni_zaa neni potreba migrovat, odpovedny_pracovnik_odlozeni_nz (typ_tranzakce = 5)
-- 2. akce.datum_zapisu, datum_autorizace, datum_zamitnuti bez migrace, datum_archivace, datum_podani_nz, datum_archivace_zaa, datum_vraceni_zaa bez migrace, datum_odlozeni_nz
insert into historie_vazby(typ_vazby) select 'akce' from akce;
update akce d set historie = sub.rn from (select id, row_number() OVER (order by id) as rn from akce) sub where d.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_zapisu, 1, odpovedny_pracovnik_zapisu, historie from akce where odpovedny_pracovnik_zapisu is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_autorizace, 2, odpovedny_pracovnik_autorizace, historie from akce where odpovedny_pracovnik_autorizace is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_archivace_zaa, 4, odpovedny_pracovnik_archivace_zaa, historie from akce where odpovedny_pracovnik_archivace_zaa is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (datum_odlozeni_nz::int) * INTERVAL '1 second'), 5, odpovedny_pracovnik_odlozeni_nz, historie from akce where odpovedny_pracovnik_odlozeni_nz is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_podani_nz, 6, odpovedny_pracovnik_podani_nz, historie from akce where odpovedny_pracovnik_podani_nz is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_archivace, 8, odpovedny_pracovnik_archivace, historie from akce where odpovedny_pracovnik_archivace is not null;

-- Dokument
-- 1. dokument.odpovedny_pracovnik_vlozeni (typ_tranzakce = 1), odpovedny_pracovnik_archivace (typ_tranzakce = 3)
-- 2. dokument.datum_vlozeni, datum_archivace
insert into historie_vazby(typ_vazby) select 'dokument' from dokument;
update dokument d set historie = sub.rn from (select id, (select count(*) from akce) +row_number() OVER (order by id) as rn from dokument) sub where d.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP 'epoch' + (datum_vlozeni::int) * INTERVAL '1 second'), 1, odpovedny_pracovnik_vlozeni, historie from dokument where odpovedny_pracovnik_vlozeni is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP 'epoch' + (datum_archivace::int) * INTERVAL '1 second'), 3, odpovedny_pracovnik_archivace, historie from dokument where odpovedny_pracovnik_archivace is not null;

-- Externi_zdroj
-- 1. externi_zdroj.odpovedny_pracovnik_vlozeni (typ_tranzakce = 1)
-- 2. externi_zdroj.datum_vlozeni
insert into historie_vazby(typ_vazby) select 'externi_zdroj' from externi_zdroj;
update externi_zdroj e set historie = sub.rn from (select id, (select count(*) from akce) + (select count(*) from dokument) + row_number() OVER (order by id) as rn from externi_zdroj) sub where e.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_vlozeni, 1, odpovedny_pracovnik_vlozeni, historie from externi_zdroj where odpovedny_pracovnik_vlozeni is not null;

-- Lokalita
-- 1. lokalita.odpovedny_pracovnik_zapisu (typ_tranzakce = 1), odpovedny_pracovnik_archivace (typ_tranzakce = 3)
-- 2. lokalita.datum_zapisu, lokalita.datum_archivace
insert into historie_vazby(typ_vazby) select 'lokalita' from lokalita;
update lokalita l set historie = sub.rn from (select id, (select count(*) from akce) + (select count(*) from dokument) + (select count(*) from externi_zdroj) + row_number() OVER (order by id) as rn from lokalita) sub where l.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP 'epoch' + (datum_zapisu::int) * INTERVAL '1 second'), 1, odpovedny_pracovnik_zapisu, historie from lokalita where odpovedny_pracovnik_zapisu is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP 'epoch' + (datum_archivace::int) * INTERVAL '1 second'), 3, odpovedny_pracovnik_archivace, historie from lokalita where odpovedny_pracovnik_archivace is not null;

-- Pian
-- 1. pian.vymezil (typ_tranzakce = 1), potvrdil (typ_tranzakce = 2)
insert into historie_vazby(typ_vazby) select 'pian' from pian;
update pian p set historie = sub.rn from (select id, (select count(*) from akce) + (select count(*) from dokument) + (select count(*) from externi_zdroj) + (select count(*) from lokalita) + row_number() OVER (order by id) as rn from pian) sub where p.id = sub.id;
-- 2. pian.datum_vymezeni, datum_potvrzeni
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_vymezeni, 1, vymezil, historie from pian where vymezil is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select (SELECT TIMESTAMP 'epoch' + (datum_potvrzeni::int) * INTERVAL '1 second'), 2, potvrdil, historie from pian where potvrdil is not null;
-- Vlozit sloupec stav do pian
alter table pian add column stav smallint;
-- kde pian.ident_cely zacina na N vlozit do stav 1 jinak 2
update pian set stav = 1 where ident_cely LIKE 'N%';
update pian set stav = 2 where ident_cely LIKE 'P%';
alter table pian alter column stav set not null;

-- Projekt migrace do historie
-- 1. projekt.odpovedny_pracovnik_zapisu (typ_tranzakce = 1), odpovedny_pracovnik_prihlaseni (typ_tranzakce = 2), odpovedny_pracovnik_archivace (typ_tranzakce = 6), odpovedny_pracovnik_navrhu_zruseni (typ_tranzakce = 7), odpovedny_pracovnik_zruseni (typ_tranzakce = 8), odpovedny_pracovnik_navrhu_archivace (typ_tranzakce = 5), odpovedny_pracovnik_zahajeni (typ_tranzakce = 3), odpovedny_pracovnik_ukonceni (typ_tranzakce = 4)
-- 2. projekt.datum_zapisu, datum_prihlaseni, datum_archivace, datum_navrhu_zruseni, datum_zruseni, datum_navrhu_archivace, datum_zapisu_zahajeni (je tam pole datum_zahajeni a to nemazat je to neco jineho), datum_zapisu_ukonceni (je tam datum ukonceni a to je neco jine, nemazat)
-- 3. projekt.datetime_born (typ_tranzakce = 0, uzivatel = amcr@arup.cas.cz)
-- 4. projekt.duvod_navrzeni_zruseni (ulozit k typu tranzakce 7 do poznamky)
insert into historie_vazby(typ_vazby) select 'projekt' from projekt;
update projekt p set historie = sub.rn from (select id, (select count(*) from akce) + (select count(*) from dokument) + (select count(*) from externi_zdroj) + (select count(*) from lokalita) + (select count(*) from pian) + row_number() OVER (order by id) as rn from projekt) sub where p.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_zapisu, 1, odpovedny_pracovnik_zapisu, historie from projekt where odpovedny_pracovnik_zapisu is not null and datum_zapisu is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_prihlaseni, 2, odpovedny_pracovnik_prihlaseni, historie from projekt where odpovedny_pracovnik_prihlaseni is not null and datum_prihlaseni is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_archivace, 6, odpovedny_pracovnik_archivace, historie from projekt where odpovedny_pracovnik_archivace is not null and datum_archivace is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba, poznamka) select datum_navrzeni_zruseni, 7, odpovedny_pracovnik_navrhu_zruseni, historie, duvod_navrzeni_zruseni from projekt where odpovedny_pracovnik_navrhu_zruseni is not null and datum_navrzeni_zruseni is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_zruseni, 8, odpovedny_pracovnik_zruseni, historie from projekt where odpovedny_pracovnik_zruseni is not null and datum_zruseni is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_navrhu_archivace, 5, odpovedny_pracovnik_navrhu_archivace, historie from projekt where odpovedny_pracovnik_navrhu_archivace is not null and datum_navrhu_archivace is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_zapisu_zahajeni, 3, odpovedny_pracovnik_zahajeni, historie from projekt where odpovedny_pracovnik_zahajeni is not null and datum_zapisu_zahajeni is not null;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datum_zapisu_ukonceni, 4, odpovedny_pracovnik_ukonceni, historie from projekt where odpovedny_pracovnik_ukonceni is not null and datum_zapisu_ukonceni is not null;
-- COMMENT: vetsina projektu ma v datetime_born null
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select datetime_born, 0, 598610, historie from projekt where datetime_born is not null;
-- COMMENT: Protoze zaznamy typu 7 v historii chybi je potreba nejdriv vyresit chybu predtim COMMENT: docela dlouhy dotaz - DN: toto se zdá být úplně irelevantní řešení, když to jde ošetřit na řádku 120 velice snadno
--update historie set poznamka = sel.d from (select p.id, p.odpovedny_pracovnik_navrhu_zruseni, p.duvod_navrzeni_zruseni as d from projekt p join historie h on p.historie = h.vazba where p.odpovedny_pracovnik_navrhu_zruseni is not null) as sel where historie.typ_zmeny = 7;

-- Pridat not null
-- 1. soubor.vytvoreno
alter table soubor alter column vytvoreno set not null;
-- 2. heslar_typ_material_rada.heslar_rada_id
alter table heslar_typ_material_rada alter column heslar_rada_id set not null;
-- 3. heslar_typ_material_rada.heslar_typ_dokumentu_id
alter table heslar_typ_material_rada alter column heslar_typ_dokumentu_id set not null;
-- 4. heslar_typ_material_rada.heslar_material_dokumentu_id
alter table heslar_typ_material_rada alter column heslar_material_dokumentu_id set not null;
-- 5. organizace.nazev
alter table organizace alter column nazev set not null;
-- 6. organizace.nazev_zkraceny
alter table organizace alter column nazev_zkraceny set not null;
-- 7. organizace.typ_organizace
alter table organizace alter column typ_organizace set not null;
-- 8. organizace.oao
alter table organizace alter column oao set not null;
-- 9. kladyzm.(vsechny sloupce)
alter table kladyzm alter column objectid set not null;
alter table kladyzm alter column kategorie set not null;
alter table kladyzm alter column cislo set not null;
alter table kladyzm alter column natoceni set not null;
alter table kladyzm alter column shape_leng set not null;
alter table kladyzm alter column shape_area set not null;
alter table kladyzm alter column the_geom set not null;

-- Pridat unique constraints
-- 1. heslar_typ_material_rada (heslar_typ_dokumentu_id, heslar_material_dokumentu_id)
ALTER TABLE public.heslar_typ_material_rada ADD CONSTRAINT heslar_typ_material_rada_key UNIQUE (heslar_typ_dokumentu_id, heslar_material_dokumentu_id);
-- 2. kladyzm.objectid
ALTER TABLE public.kladyzm ADD CONSTRAINT kladyzm_objectid_key UNIQUE (objectid);
-- 3. kladyzm.cislo
ALTER TABLE public.kladyzm ADD CONSTRAINT kladyzm_cislo_key UNIQUE (cislo);
-- 4. kladyzm.nazev 4600 zaznamu ma jako nazev N_A  COMMENT: nebude se nakonec pridavat
-- 5. tvar (dokument, tvar, poznamka)
ALTER TABLE public.tvar ADD CONSTRAINT tvar_key UNIQUE (dokument, tvar, poznamka);
-- 6. uzivatel_spoluprace (badatel, archeolog)
alter table vazba_spoluprace add constraint badatel_archeolog_key unique (archeolog, badatel);

-- Prejmenovat tabulky a sekvence
-- 1. archeologicky_dokumentacni_bod -> adb + sekvence
alter table archeologicky_dokumentacni_bod rename to adb;
alter sequence archeologicky_dokumentacni_bod_id_seq rename to adb_id_seq;
-- 2. heslar_typ_material_rada -> heslar_dokument_typ_material_rada
alter table heslar_typ_material_rada rename to heslar_dokument_typ_material_rada;
alter sequence heslar_typ_material_rada_id_seq rename to heslar_dokument_typ_material_rada_id_seq;
-- 3. project_announcement_suffix -> projekt_oznameni_suffix
alter table project_announcement_suffix rename to projekt_oznameni_suffix;
alter sequence project_announcement_suffix_id_seq rename to projekt_oznameni_suffix_id_seq;
-- 4. katastr_storage -> ruian_katastr
alter table katastr_storage rename to ruian_katastr;
alter sequence katastr_storage_id_seq rename to ruian_katastr_id_seq;
-- 5. spz_storage -> ruian_okres
alter table spz_storage rename to ruian_okres;
alter sequence spz_storage_id_seq rename to ruian_okres_id_seq;
-- 6. heslar_kraj -> ruian_kraj
alter table heslar_kraj rename to ruian_kraj;
alter sequence heslar_kraj_id_seq rename to ruian_kraj_id_seq;
-- 7. megalit_info -> systemove_promenne
alter table megalit_info rename to systemove_promenne;
-- 8. user_storage -> uzivatel
alter table user_storage rename to uzivatel;
alter sequence user_storage_id_seq rename to uzivatel_id_seq;
-- 9. user_notify -> uzivatel_notifikace_projekty
alter table user_notify rename to uzivatel_notifikace_projekty;
alter sequence user_notify_id_seq rename to uzivatel_notifikace_projekty_id_seq;
-- 10. vazba_spoluprace -> uzivatel_spoluprace
alter table vazba_spoluprace rename to uzivatel_spoluprace;
alter sequence vazba_spoluprace_id_seq rename to uzivatel_spoluprace_id_seq;

-- Prejmenovat sloupce
-- 1. adb.parent -> dokumentacni_jednotka -- Prejmenovat sloupce
alter table adb rename column parent to dokumentacni_jednotka;
-- 2. heslar_dokument_typ_material_rada.heslar_rada_id -> dokument_rada, heslar_typ_dokumentu_id -> dokument_typ, heslar_material_dokumentu_id -> dokument_material
alter table heslar_dokument_typ_material_rada rename column heslar_rada_id to dokument_rada;
alter table heslar_dokument_typ_material_rada rename column heslar_typ_dokumentu_id to dokument_typ;
alter table heslar_dokument_typ_material_rada rename column heslar_material_dokumentu_id to dokument_material;
-- 3. organizace.months_to_publication -> mesicu_do_zverejneni, published_accessibility -> zverejneni_pristupnost
alter table organizace rename column months_to_publication to mesicu_do_zverejneni;
alter table organizace rename column published_accessibility to zverejneni_pristupnost;
alter table organizace alter column zverejneni_pristupnost drop default;
-- 4. projekt.lokalita -> lokalizace, nkp_cislo -> kulturni_pamatka_cislo, nkp_popis -> kulturni_pamatka_popis, objednatel -> oznamovatel
alter table projekt rename column lokalita to lokalizace;
alter table projekt rename column nkp_cislo to kulturni_pamatka_cislo;
alter table projekt rename column nkp_popis to kulturni_pamatka_popis;
alter table projekt rename column objednatel to oznamovatel;
-- 5. samostatny_nalez.inv_cislo -> evidencni_cislo
alter table samostatny_nalez rename column inv_cislo to evidencni_cislo;
-- COMMENT: Rozparsovani auth_level nedelam v ramci teto iterace
-- 6. uzivatel.pasw -> heslo, auth_level -> role + migrace opravneni do tabulky uzivatel_opravneni, confirmation -> email_potvrzen
alter table uzivatel rename column pasw to heslo;
alter table uzivatel rename column confirmation to email_potvrzen;
-- 7. uzivatel_notifikace_projekty.user_id -> uzivatel
alter table uzivatel_notifikace_projekty rename column user_id to uzivatel;
-- 8. vyskovy_bod.parent -> adb
alter table vyskovy_bod rename column parent to adb;
-- 9. organizace.en -> nazev_zkraceny_en
alter table organizace rename column en to nazev_zkraceny_en;
-- 10. ruian_kraj.heslo -> nazev
alter table ruian_kraj rename column heslo to nazev;
-- 11. ruian_kraj.kod_ruian -> kod
alter table ruian_kraj rename column kod_ruian to kod;
-- 12. ruian_kraj.id_c_m -> rada_id
alter table ruian_kraj rename column id_c_m to rada_id;
-- 13. ruian_okres.full_name -> nazev
alter table ruian_okres rename column full_name to nazev;
-- 14. soubor.uzivatelske_oznaceni -> nazev_puvodni
alter table soubor rename column uzivatelske_oznaceni to nazev_puvodni;
-- 17. uzivatel_spoluprace.badatel -> spolupracovnik
alter table uzivatel_spoluprace rename column badatel to spolupracovnik;
-- 18. uzivatel_spoluprace.archeolog -> vedouci
alter table uzivatel_spoluprace rename column archeolog to vedouci;
-- 19. soubor.sha_512
ALTER TABLE soubor ADD COLUMN sha_512 text;

-- Pridat not null
-- 109. uzivatel.role COMMENT: tohle se zatim jmenuje auth_level
update uzivatel set auth_level = 0 where auth_level is null;
alter table uzivatel alter column auth_level set not null;
-- 110. ruian_katastr.okres
alter table ruian_katastr alter column okres set not null;
-- 111. ruian_katastr.nazev
alter table ruian_katastr alter column nazev set not null;
-- 112. ruian_katastr.kod
alter table ruian_katastr alter column kod set not null;
-- 113. ruian_katastr.definicni_bod
alter table ruian_katastr alter column definicni_bod set not null;
-- 114. ruian_katastr.pian
alter table ruian_katastr alter column pian set not null;
-- 115. ruian_katastr.aktualni
alter table ruian_katastr alter column aktualni set not null;
-- 116. soubor.typ_souboru
alter table soubor alter column typ_souboru set not null;
-- 117. soubor.nazev_puvodni
alter table soubor alter column nazev_puvodni set not null;
-- 118. uzivatel.organizace
alter table uzivatel alter column organizace set not null;

-- Nove cizi klice
-- COMMENT: tohle jde udelat az bude role oddelena od opravneni.
-- 121. uzivatel.role -> heslar_pristupnost

-- Novy sloupec
-- 124. adb.sm5 (migrace vytvoreni vazby na kladysm5 na zaklade indet_cely AAA-BBB-PPP kde BB napr. PRAH71 je relace na kladysm5.mapno)
alter table adb add column sm5 integer;
update adb set sm5 = sel.g from (select k.gid as g, a.id as id from kladysm5 k join adb a on a.ident_cely LIKE '%-' || k.mapno || '-%') as sel where adb.id = sel.id;
alter table adb alter column sm5 set not null;
alter table adb add constraint adb_sm5_fkey FOREIGN KEY (sm5) REFERENCES kladysm5(gid);
-- 125. organizace.email, telefon, adresa, ico, soucast, nazev_en, zanikla
alter table organizace add column email text;
alter table organizace add column telefon text;
alter table organizace add column adresa text;
alter table organizace add column ico text;
alter table organizace add column soucast integer;
alter table organizace add constraint organizace_soucast_fkey FOREIGN KEY (soucast) REFERENCES organizace(id);
-- TODO: add not null after its filled
alter table organizace add column nazev_en text;
-- TODO: add not null after its filled
alter table organizace add column zanikla boolean DEFAULT FALSE NOT NULL;
-- 126. projekt.organizace (migrace vyplnit na zaklade organizace odpovedneho_pracovnika_prihlaseni)
alter table projekt add column organizace integer;
update projekt set organizace = sel.org from (select p.id as proj, u.organizace as org from projekt p join uzivatel u on u.id = p.odpovedny_pracovnik_prihlaseni) as sel where projekt.id = sel.proj;
alter table projekt add constraint projekt_organizace_fkey foreign key (organizace) references organizace(id);

-- 127. ruian_kraj.definicni_bod
-- TODO MIGRACE and add not null after its filled
alter table ruian_kraj add column definicni_bod geometry;
-- 128. ruian_kraj.hranice
-- TODO MIGRACE and add not null after its filled
alter table ruian_kraj add column hranice geometry;
-- 129. ruian_kraj.aktualni
-- TODO MIGRACE and add not null after its filled
alter table ruian_kraj add column aktualni boolean;
-- 130. ruian_okres.hranice
-- TODO MIGRACE and add not null after its filled
alter table ruian_okres add column hranice geometry;
-- 131. ruian_okres.definicni_bod
-- TODO MIGRACE and add not null after its filled
alter table ruian_okres add column definicni_bod geometry;
-- 132. ruian_okres.aktualni
-- TODO MIGRACE and add not null after its filled
alter table ruian_okres add column aktualni boolean;
-- 133. soubor_docasny.vazba + cizi klic na soubor_vazby
alter table soubor_docasny add column vazba integer;
alter table soubor_docasny add constraint soubor_docasny_vazba_fkey FOREIGN KEY (vazba) references soubor_vazby(id);
-- 134. uzivatel.osoba + cizi klic na osoby
-- TODO migrace mapovani osoby na uzivatele
alter table uzivatel add column osoba integer;
alter table uzivatel add constraint uzivatel_osoba_fkey foreign key (osoba) references osoba(id);

-- Slouceni stavajicich historii
-- 1. historie_user_storage
insert into historie_vazby(typ_vazby) select 'uzivatel' from uzivatel;
update uzivatel p set historie = sub.rn from (select id, (select min(id) from historie_vazby where typ_vazby = 'uzivatel') + row_number() OVER (order by id) -1 as rn from uzivatel) sub where p.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba, poznamka) select h.datum_zmeny, h.typ_zmeny, h.uzivatel, u.historie, h.komentar from historie_user_storage h join uzivatel u on u.id = h.ucet;
-- 2. historie_spoluprace
insert into historie_vazby(typ_vazby) select 'uzivatel_spoluprace' from uzivatel_spoluprace;
update uzivatel_spoluprace p set historie = sub.rn from (select id, (select min(id) from historie_vazby where typ_vazby = 'uzivatel_spoluprace') + row_number() OVER (order by id) -1 as rn from uzivatel_spoluprace) sub where p.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba) select h.datum_zmeny, h.typ_zmeny, h.uzivatel, u.historie from historie_spoluprace h join uzivatel_spoluprace u on u.id = h.vazba_spoluprace;
-- 3. historie_akce COMMENT: Tady jsou data jen kvuli tomu ze se tam premigrovali v ramci migrace 1 (2482 zaznamu)
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba, poznamka) select h.datum_zmeny, h.typ_zmeny, h.uzivatel, a.historie, zprava from historie_akce h join akce a on a.id = h.akce;
-- 4. historie_samostatny_nalez
insert into historie_vazby(typ_vazby) select 'samostatny_nalez' from samostatny_nalez;
update samostatny_nalez p set historie = sub.rn from (select id, (select min(id) from historie_vazby where typ_vazby = 'samostatny_nalez') + row_number() OVER (order by id) -1 as rn from samostatny_nalez) sub where p.id = sub.id;
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba, poznamka) select h.datum_zmeny, h.typ_zmeny, h.uzivatel, u.historie, h.duvod from historie_samostatny_nalez h join samostatny_nalez u on u.id = h.samostatny_nalez;
-- 5. historie_dokument
insert into historie(datum_zmeny, typ_zmeny, uzivatel, vazba, poznamka) select h.datum_zmeny, h.typ_zmeny, h.uzivatel, a.historie, duvod from historie_dokumentu h join dokument a on a.id = h.dokument;

-- Kontrola 1
-- cizi klic na kraj z okrasu
alter table ruian_okres add constraint ruian_okres_kraj_fkey foreign key (kraj) references ruian_kraj(id);
-- dalsi chybejici cizi klice
alter table historie add constraint historie_uzivatel_fkey foreign key (uzivatel) references uzivatel(id);
alter table historie add constraint historie_vazba_fkey foreign key (vazba) references historie_vazby(id);
-- prejmenovat extra_data -> dokument_extra_data
alter table extra_data rename to dokument_extra_data;
-- sekvence tabulkam
ALTER TABLE akce alter column id set NOT NULL;
ALTER TABLE akce alter column id set DEFAULT nextval('akce_id_seq');
ALTER TABLE dokument alter column id set DEFAULT nextval('dokument_id_seq');
ALTER TABLE dokumentacni_jednotka alter column id set DEFAULT nextval('dokumentacni_jednotka_id_seq');
ALTER TABLE externi_zdroj alter column id set DEFAULT nextval('externi_zdroj_id_seq');
ALTER TABLE ruian_katastr alter column id set DEFAULT nextval('ruian_katastr_id_seq');
ALTER TABLE lokalita alter column id set DEFAULT nextval('lokalita_id_seq');
ALTER TABLE neident_akce alter column id set DEFAULT nextval('neident_akce_id_seq');
ALTER TABLE projekt alter column id set DEFAULT nextval('projekt_id_seq');
ALTER TABLE ruian_okres alter column id set DEFAULT nextval('ruian_okres_id_seq');
ALTER TABLE uzivatel alter column id set DEFAULT nextval('uzivatel_id_seq');
CREATE SEQUENCE public.organizace_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('organizace_id_seq', (select MAX(id) from organizace) + 1);
ALTER TABLE organizace alter column id set DEFAULT nextval('organizace_id_seq');
-- Kontrola 2
ALTER TABLE externi_zdroj add constraint externi_zdroj_typ_fkey foreign key (typ) references heslar_typ_externiho_zdroje(id);
ALTER TABLE ONLY adb ADD CONSTRAINT adb_dokumentacni_jednotka_key  UNIQUE(dokumentacni_jednotka);
ALTER TABLE ONLY dokument_extra_data ADD CONSTRAINT dokument_extra_data_dokument_key  UNIQUE(dokument);
ALTER TABLE ONLY samostatny_nalez ADD CONSTRAINT samostatny_nalez_ident_cely_key  UNIQUE(ident_cely);
ALTER TABLE akce_vedouci add constraint akce_vedouci_organizace_fkey foreign key (organizace) references organizace(id);
alter table externi_zdroj_editor add column poradi integer;
alter table externi_zdroj_editor alter column poradi set not null;
alter table externi_zdroj_editor add constraint externi_zdroj_poradi_key UNIQUE(poradi, externi_zdroj);
alter table osoba drop constraint heslar_jmena_jmeno_prijmeni;
alter table osoba drop constraint heslar_jmena_vypis_cely;
alter table archeologicky_dokumentacni_bod_sekvence rename to adb_sekvence;
alter sequence archeologicky_dokumentacni_bod_sekvence_id_seq rename to adb_sekvence_id_seq;
---- COMMENT: nejdriv je potreba smazat uzivatele s id = -1 a kde na neho ukazuje historie nastavit na amcr@arup.cas.cz
update historie set uzivatel = 598610 where uzivatel = -1;
update soubor set vlastnik = 598610 where vlastnik = -1;
delete from uzivatel where id = -1;
alter table uzivatel alter column heslo set not null;
alter table uzivatel alter column email set not null;
alter table ruian_okres alter column spz set not null;
alter table ruian_okres alter column kod set not null;
alter table ruian_okres alter column kraj set not null;
alter table uzivatel_notifikace_projekty rename column kraj_id to kraj;
update uzivatel_notifikace_projekty set kraj = 1 where kraj = 67;
update uzivatel_notifikace_projekty set kraj = 2 where kraj = 66;
update uzivatel_notifikace_projekty set kraj = 3 where kraj = 68;
update uzivatel_notifikace_projekty set kraj = 4 where kraj = 69;
update uzivatel_notifikace_projekty set kraj = 5 where kraj = 71;
update uzivatel_notifikace_projekty set kraj = 6 where kraj = 70;
update uzivatel_notifikace_projekty set kraj = 7 where kraj = 72;
update uzivatel_notifikace_projekty set kraj = 8 where kraj = 75;
update uzivatel_notifikace_projekty set kraj = 9 where kraj = 73;
update uzivatel_notifikace_projekty set kraj = 10 where kraj = 329173;
update uzivatel_notifikace_projekty set kraj = 11 where kraj = 329174;
update uzivatel_notifikace_projekty set kraj = 12 where kraj = 329175;
update uzivatel_notifikace_projekty set kraj = 13 where kraj = 329176;
update uzivatel_notifikace_projekty set kraj = 14 where kraj = 74;
alter table uzivatel_notifikace_projekty add constraint uzivatel_notifikace_projekty_kraj_fkey foreign key (kraj) references ruian_kraj(id);
