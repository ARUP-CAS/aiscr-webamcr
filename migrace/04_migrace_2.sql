--Nove tabulky (implementace many-to-many relationships):
--1. akce_katastr (migrace sloupce katastr a dalsi_katastry do sloupce katastr)
CREATE TABLE akce_katastr (
    akce integer not null,
    katastr integer not null,
    hlavni boolean not null default false,
    PRIMARY KEY (akce, katastr),
    CONSTRAINT akce_katastr_akce_fk FOREIGN KEY (akce)
      REFERENCES akce (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT akce_katastr_katastr_fk FOREIGN KEY (katastr)
      REFERENCES katastr_storage (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
create unique index on akce_katastr (akce) where hlavni = true;
-- MIGRACE (mapovani katastru na jejich id) MIGRACE_DAT_1.sql

--2. lokalita_katastr (-||-)
CREATE TABLE lokalita_katastr (
    lokalita integer not null,
    katastr integer not null,
    hlavni boolean not null default false,
    PRIMARY KEY (lokalita, katastr),
    CONSTRAINT lokalita_katastr_lokalita_fk FOREIGN KEY (lokalita)
      REFERENCES lokalita (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT lokalita_katastr_katastr_fk FOREIGN KEY (katastr)
      REFERENCES katastr_storage (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
create unique index on lokalita_katastr (lokalita) where hlavni = true;
-- MIGRACE (mapovani katastru na jejich id) MIGRACE_DAT_1.sql

--3. projekt_katastr (-||-)
CREATE TABLE projekt_katastr (
    projekt integer not null,
    katastr integer not null,
    hlavni boolean not null default false,
    PRIMARY KEY (projekt, katastr),
    CONSTRAINT projekt_katastr_projekt_fk FOREIGN KEY (projekt)
      REFERENCES projekt (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT projekt_katastr_katastr_fk FOREIGN KEY (katastr)
      REFERENCES katastr_storage (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
create unique index on projekt_katastr (projekt) where hlavni = true;
-- MIGRACE (mapovani katastru na jejich id) MIGRACE_DAT_1.sql

--4. osoba
ALTER TABLE heslar_jmena RENAME TO osoba;
ALTER SEQUENCE heslar_jmena_id_seq RENAME TO osoba_id_seq;
ALTER TABLE osoba DROP COLUMN validated;
ALTER TABLE osoba ALTER COLUMN jmeno set not null;
ALTER TABLE osoba ALTER COLUMN prijmeni set not null;
ALTER TABLE osoba ALTER COLUMN vypis set not null;
ALTER TABLE osoba ALTER COLUMN vypis_cely set not null;
ALTER TABLE osoba ADD COLUMN rok_narozeni integer;
ALTER TABLE osoba ADD COLUMN rok_umrti integer;
ALTER TABLE osoba ADD COLUMN rodne_prijmeni text;

--5. akce_vedouci (migrace vedouci do nove tabulky + organizace)
CREATE TABLE akce_vedouci (
    akce integer not null,
    vedouci integer not null,
    organizace integer not null,
    hlavni boolean not null default false,
    PRIMARY KEY (akce, vedouci),
    CONSTRAINT akce_vedouci_akce_fk FOREIGN KEY (akce)
      REFERENCES akce (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT akce_vedouci_vedouci_fk FOREIGN KEY (vedouci)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
create unique index on akce_vedouci (akce) where hlavni = true;
-- MIGRACE (mapovani vedouci akce na jejich id z heslare jmen) MIGRACE_DAT_2.sql

--6. neident_akce_vedouci (migrace vedouci do nove tabulky)
CREATE SEQUENCE neident_akce_vedouci_id_seq;
CREATE TABLE neident_akce_vedouci (
    neident_akce integer NOT NULL,
    vedouci integer NOT NULL,
    id integer NOT NULL DEFAULT nextval('neident_akce_vedouci_id_seq'::regclass) PRIMARY KEY,
    CONSTRAINT neident_akce_vedouci_neident_akce_vedouci_key UNIQUE (neident_akce, vedouci),
    CONSTRAINT neident_akce_vedouci_neident_akce_fk FOREIGN KEY (neident_akce)
      REFERENCES neident_akce (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT neident_akce_vedouci_vedouci_fk FOREIGN KEY (vedouci)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- MIGRACE (mapovani vedouci akce na jejich id z heslare jmen) MIGRACE_DAT_2.sql

--7. dokument_autor (migrace autor do nove tabulky)
CREATE TABLE dokument_autor (
    dokument integer not null,
    autor integer not null,
    poradi integer not null,
    PRIMARY KEY (dokument, autor),
    CONSTRAINT dokument_autor_dokument_fk FOREIGN KEY (dokument)
      REFERENCES dokument (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT dokument_autor_autor_fk FOREIGN KEY (autor)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- MIGRACE  (mapovani autor dokumentu na jejich id z heslare jmen) MIGRACE_DAT_2.sql

--8. dokument_osoba (migrace z extra_data.osoby COMMENT: ted tam nic neni)
CREATE TABLE dokument_osoba (
    dokument integer not null,
    osoba integer not null,
    PRIMARY KEY (dokument, osoba),
    CONSTRAINT dokument_autor_dokument_fk FOREIGN KEY (dokument)
      REFERENCES dokument (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT dokument_autor_autor_fk FOREIGN KEY (osoba)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

--9. externi_zdroj_autor (migrace z externi_zdroj autor do nove tabulky)
CREATE TABLE externi_zdroj_autor (
    externi_zdroj integer not null,
    autor integer not null,
    poradi integer not null,
    PRIMARY KEY (externi_zdroj, autor),
    CONSTRAINT externi_zdroj_autor_externi_zdroj_fk FOREIGN KEY (externi_zdroj)
      REFERENCES externi_zdroj (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT externi_zdroj_autor_autor_fk FOREIGN KEY (autor)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- MIGRACE  (mapovani autora externiho zdroje na jejich id z heslare jmen) MIGRACE_DAT_2.sql

--10. dokument_posudek (migrace dokument.typ_dokumentu_posudek dle heslar_posudek do nove tabulky)
CREATE TABLE dokument_posudek (
    dokument integer not null,
    posudek integer not null,
    PRIMARY KEY (dokument, posudek),
    CONSTRAINT dokument_posudek_dokument_fk FOREIGN KEY (dokument)
      REFERENCES dokument (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT dokument_posudek_posudek_fk FOREIGN KEY (posudek)
      REFERENCES heslar_posudek (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- MIGRACE (mapovani posudku dokumentu dle heslare posudek) MIGRACE_DAT_3.sql (1)

-- 11. dokument_jazyk (migrace dokument.jazyk_dokumentu dle heslar_jazyk_dokumentu do nove tabulky)
CREATE TABLE dokument_jazyk (
    dokument integer not null,
    jazyk integer not null,
    PRIMARY KEY (dokument, jazyk),
    CONSTRAINT dokument_jazyk_dokument_fk FOREIGN KEY (dokument)
      REFERENCES dokument (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT dokument_jazyk_jazyk_fk FOREIGN KEY (jazyk)
      REFERENCES heslar_jazyk_dokumentu (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
insert into dokument_jazyk(dokument, jazyk) select id, jazyk_dokumentu from dokument;

-- 12. komponenta_aktivita(migrace boolean sloupcu dle heslar_aktivity)
CREATE TABLE komponenta_aktivita (
    komponenta integer not null,
    aktivita integer not null,
    PRIMARY KEY (komponenta, aktivita),
    CONSTRAINT komponenta_aktivita_komponenta_fk FOREIGN KEY (komponenta)
      REFERENCES komponenta (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT komponenta_aktivita_aktivita_fk FOREIGN KEY (aktivita)
      REFERENCES heslar_aktivity (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- COMMENT: udelano v migraci_dat_3.sql spolecne s komponenta_dokument zaznamy
--insert into komponenta_aktivita(komponenta, aktivita) select id, 1 from komponenta where aktivita_sidlistni = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 2 from komponenta where aktivita_pohrebni = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 3 from komponenta where aktivita_vyrobni = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 4 from komponenta where aktivita_tezebni = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 5 from komponenta where aktivita_kultovni = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 6 from komponenta where aktivita_komunikace = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 7 from komponenta where aktivita_deponovani = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 8 from komponenta where aktivita_boj = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 9 from komponenta where aktivita_jina = true;
--insert into komponenta_aktivita(komponenta, aktivita) select id, 10 from komponenta where aktivita_intruze = true;

--13. dokument_cast_vazby (migrace dokument_cast.vazba do dokument_cast.vazba, akce.dokumenty_casti, lokalita.dokumenty_casti)
CREATE SEQUENCE public.dokument_cast_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE dokument_cast_vazby (
    id integer DEFAULT nextval('public.dokument_cast_vazby_id_seq'::regclass) not null,
    PRIMARY KEY (id)
);
ALTER TABLE dokument_cast_vazby add column typ_vazby text;
ALTER TABLE jednotka_dokument RENAME TO dokument_cast;
ALTER SEQUENCE jednotka_dokument_id_seq RENAME TO dokument_cast_id_seq;
-- MIGRACE (vytvoreni zaznamu v dokument_cast_vazby seskupujici casti_dokumentu ktere jsou v relaci s konkretni akcemi a lokalitami)
-- Je tady potreba prochazet vsechny zaznamy dokument_cast a pro kazdou vazbu najit lokalitu nebo akci na kterou odkazuje tato vazba. Pro kazdou takovou mnozinu dokument_casti(ktere ukazuji na stejnou lokalitu nebo akci) je pak potreba vytvorit novy zaznam v tabulce dokument_cast_vazby a odkazovat na nej v sloupci akce/lokalita.dokumenty_casti. Sloupec dokumenty_cast.vazba ted budou ukazovat ne na akci/lokalitu ale na tento novy seskupujici zaznam.
-- Podminky:
-- 1. Na jeden zaznam z dokument_cast_vazba muzou ukazovat pouze zaznamy z jedne tabulky tj. vsechny z lokality nebo vsechny z akce
-- 2. Kazda akce/lokalita by mela mit prideleny svuj unikatni zaznam v tabulce dokument_cast_vazby
-- MIGRACE_DAT_3.sql (2)

--15. dokumentacni_jednotka_vazby (migrace dokumentacni_jednotka.parent do dokumentacni_jednotka.vazba, akce.dokumentacni_jednotky, lokalita.dokumentacni_jednotky)
CREATE SEQUENCE public.dokumentacni_jednotka_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE dokumentacni_jednotka_vazby (
    id integer DEFAULT nextval('public.dokumentacni_jednotka_vazby_id_seq'::regclass) not null,
    PRIMARY KEY (id)
);
ALTER TABLE dokumentacni_jednotka_vazby add column typ_vazby text;
-- MIGRACE (vytvoreni seskupujiciho zaznamu)

--17. externi_odkaz_vazby (migrace externi_odkaz.vazba do akce.externi_odkazy, lokalita.externi_odkazy)
CREATE SEQUENCE public.externi_odkaz_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE externi_odkaz_vazby (
    id integer DEFAULT nextval('public.externi_odkaz_vazby_id_seq'::regclass) not null,
    PRIMARY KEY (id)
);
ALTER TABLE externi_odkaz_vazby add column typ_vazby text;
-- MIGRACE  (vytvoreni seskupujiciho zaznamu)

--19. soubor_vazby (migrace sloupců soubor.dokument, projekt, samostatny_nalez do soubor.vazba, projekt.soubory, samostatny_nalez.soubory, dokument.soubory)
CREATE SEQUENCE public.soubor_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE soubor_vazby (
    id integer DEFAULT nextval('public.soubor_vazby_id_seq'::regclass) not null,
    PRIMARY KEY (id)
);
-- MIGRACE  (vytvoreni seskupujiciho zaznamu - ukazkovy priklad)
alter table soubor_vazby add column typ_vazby text not null;
-- Vytvoreni seskupovacich zaznamu s prirazenym typen
insert into soubor_vazby(typ_vazby) select 'samostatny_nalez' from samostatny_nalez;
insert into soubor_vazby(typ_vazby) select 'dokument' from dokument;
insert into soubor_vazby(typ_vazby) select 'projekt' from projekt;


--22. komponenta_vazby (migrace komponenta.parent, komponenta_dokument.jednotka_dokument do komponenta.vazba, dokument_cast.komponenty, dokumentacni_jednotka.komponenty)
CREATE SEQUENCE public.komponenta_vazby_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE komponenta_vazby (
    id integer DEFAULT nextval('public.komponenta_vazby_id_seq'::regclass) not null,
    PRIMARY KEY (id)
);
ALTER TABLE komponenta_vazby add column typ_vazby text;
-- MIGRACE MIGRACE_DAT_3.sql (3)

--24. externi_zdroj.editor (migrace z externi_zdroj.sbornik_editor do nove tabulky)
CREATE TABLE externi_zdroj_editor (
    externi_zdroj integer not null,
    editor integer not null,
    PRIMARY KEY (externi_zdroj, editor),
    CONSTRAINT externi_zdroj_editor_externi_zdroj_fk FOREIGN KEY (externi_zdroj)
      REFERENCES externi_zdroj (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT externi_zdroj_editor_editor_fk FOREIGN KEY (editor)
      REFERENCES osoba (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- MIGRACE (tady je pouze 10 zaznamu nejspis je lze pouze vlozit inzertem manualne) MIGRACE_DAT_3.sql (8)

--Pridat check:
--1. check ze akce.typ vs akce.projekt (R->P and projekt not null, N->S and projek null)
-- alter table akce add check ((typ = 'N' and projekt is null) or (typ = 'R' and projekt is not null));

--Novy sloupec:
--1. neident_akce.dokument_cast (not null, unique, foreign key na dokument_cast, migrace vazba z jednotka_dokument kde ukazuje na neident_akci)
ALTER TABLE neident_akce add column dokument_cast integer;
ALTER TABLE neident_akce ADD CONSTRAINT neident_akce_dokument_cast_fkey FOREIGN KEY (dokument_cast) REFERENCES dokument_cast(id);
-- MIGRACE a PRIDAT NOT NULL constraint MIGRACE_DAT_3.sql (7)

--2. vyskovy_bod.geom
ALTER TABLE vyskovy_bod ADD COLUMN geom geometry;
-- TODO MIGRACE a PRIDAT NOT NULL constraint

--5. samostatny_nalez.soubory
ALTER TABLE samostatny_nalez ADD COLUMN soubory integer;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby(id);
-- Napojit nalez na vazbu
update samostatny_nalez d set soubory = sub.rn from (select id, row_number() OVER (order by id) as rn from samostatny_nalez) sub where d.id = sub.id;

--4. dokument.soubory
ALTER TABLE dokument ADD COLUMN soubory integer;
ALTER TABLE dokument ADD CONSTRAINT dokument_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby(id);
update dokument d set soubory = sub.rn from (select id, (select count(*) from samostatny_nalez) + row_number() OVER (order by id) as rn from dokument) sub where d.id = sub.id;

--3. projekt.soubory
ALTER TABLE projekt ADD COLUMN soubory integer;
ALTER TABLE projekt ADD CONSTRAINT projekt_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby(id);
update projekt d set soubory = sub.rn from (select id, (select count(*) from dokument) + (select count(*) from samostatny_nalez) + row_number() OVER (order by id) as rn from projekt) sub where d.id = sub.id;

--6. soubor.vazba
ALTER TABLE soubor ADD COLUMN vazba integer;
ALTER TABLE soubor ADD CONSTRAINT soubor_vazba_fkey FOREIGN KEY (vazba) REFERENCES soubor_vazby(id);
-- Napojit soubor na vazbu dle reference
update soubor s set vazba = d.soubory from (select id, soubory from dokument) d where d.id = s.dokument;
update soubor s set vazba = p.soubory from (select id, soubory from projekt) p where p.id = s.projekt;
update soubor s set vazba = sn.soubory from (select id, soubory from samostatny_nalez) sn where sn.id = s.samostatny_nalez;
-- COMMENT 299 souboru nema referenci ani na projekt, ani na dokument ani na samostatny_nalez select count(*) from soubor where vazba is null;

-- 7. komponenta.vazba
ALTER TABLE komponenta ADD COLUMN vazba integer;
ALTER TABLE komponenta ADD CONSTRAINT komponenta_vazba_fkey FOREIGN KEY (vazba) REFERENCES komponenta_vazby(id);
-- MIGRACE a PRIDAT NOT NULL CONSTRAINT MIGRACE_DAT_3.sql (3)

--8. dokumentacni_jednotka.komponenty
ALTER TABLE dokumentacni_jednotka ADD COLUMN komponenty integer;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_komponenty_fkey FOREIGN KEY (komponenty) REFERENCES komponenta_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (3)

--9. dokument_cast.komponenty
ALTER TABLE dokument_cast ADD COLUMN komponenty integer unique;
ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_komponenty_fkey FOREIGN KEY (komponenty) REFERENCES komponenta_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (3)

--10. akce.dokumentacni_jednotky
ALTER TABLE akce ADD COLUMN dokumentacni_jednotky integer unique;
ALTER TABLE akce ADD CONSTRAINT akce_dokumentacni_jednotky_fkey FOREIGN KEY (dokumentacni_jednotky) REFERENCES dokumentacni_jednotka_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (4)

--11. lokalita.dokumentacni_jednotky
ALTER TABLE lokalita ADD COLUMN dokumentacni_jednotky integer unique;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_dokumentacni_jednotky_fkey FOREIGN KEY (dokumentacni_jednotky) REFERENCES dokumentacni_jednotka_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (4)

--12. dokumentacni_jednotka.vazba
ALTER TABLE dokumentacni_jednotka ADD COLUMN vazba integer;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_vazba_fkey FOREIGN KEY (vazba) REFERENCES dokumentacni_jednotka_vazby(id);

--13. akce.externi_odkazy
ALTER TABLE akce ADD COLUMN externi_odkazy integer unique;
ALTER TABLE akce ADD CONSTRAINT akce_externi_odkazy_fkey FOREIGN KEY (externi_odkazy) REFERENCES externi_odkaz_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (5)

--14. lokalita.externi_odkazy
ALTER TABLE lokalita ADD COLUMN externi_odkazy integer unique;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_externi_odkazy_fkey FOREIGN KEY (externi_odkazy) REFERENCES externi_odkaz_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (5)

--13. akce.dokumenty_casti
ALTER TABLE akce ADD COLUMN dokumenty_casti integer unique;
ALTER TABLE akce ADD CONSTRAINT akce_dokumenty_casti_fkey FOREIGN KEY (dokumenty_casti) REFERENCES dokument_cast_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (2)

--14. lokalita.dokumenty_casti
ALTER TABLE lokalita ADD COLUMN dokumenty_casti integer unique;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_dokumenty_casti_fkey FOREIGN KEY (dokumenty_casti) REFERENCES dokument_cast_vazby(id);
-- MIGRACE MIGRACE_DAT_3.sql (2)

--Zmena typu sloupce:
--1. let.pilot (string -> integer, migrace dle heslar_jmena na osobu)
-- MIGRACE_DAT_3.sql (6)

--2. lokalita.stav (int -> smallint)
alter table lokalita alter column stav type smallint;
--3. dokument.stav (int -> smallint)
alter table dokument alter column stav type smallint;
--4. samostatny_nalez.stav (int -> smallint)
alter table samostatny_nalez alter column stav type smallint;

--Nove not null:
--1. akce.stav
alter table akce alter column stav set not null;
--2. akce.specifikace_data
alter table akce alter column specifikace_data set not null;
--3. akce.pristupnost default 1
alter table akce alter column pristupnost set not null;
alter table akce alter column pristupnost set default 1;

--4. dokument.pristupnost
alter table dokument alter column pristupnost set not null;
--5. dokumentacni_jednotka.typ, negativni_jednotka
alter table dokumentacni_jednotka alter column typ set not null;
alter table dokumentacni_jednotka alter column negativni_jednotka set not null;
--6. externi_zdroj.stav, typ
alter table externi_zdroj alter column stav set not null;
alter table externi_zdroj alter column typ set not null;
--7. lokalita.stav, druh, nazev, typ_lokality, pristupnost
alter table lokalita alter column stav set not null;
alter table lokalita alter column druh set not null;
alter table lokalita alter column nazev set not null;
alter table lokalita alter column typ_lokality set not null;
alter table lokalita alter column pristupnost set not null;
--8. nalez.komponenta, druh_nalezu
alter table nalez alter column komponenta set not null;
alter table nalez alter column druh_nalezu set not null;
--9. pian.presnost, typ, geom, buffer, zm10, zm50, ident_cely
alter table pian alter column presnost set not null;
alter table pian alter column typ set not null;
alter table pian alter column geom set not null;
alter table pian alter column buffer set not null;
alter table pian alter column zm10 set not null;
alter table pian alter column zm50 set not null;
alter table pian alter column ident_cely set not null;
--10. projekt.stav, typ_projektu, ident_cely
alter table projekt alter column typ_projektu set not null;
alter table projekt alter column stav set not null;
alter table projekt alter column ident_cely set not null;
--11. tvar.tvar
alter table tvar alter column tvar set not null;

--Odebrat not null:
--1. adb.typ_sondy, trat, parcelni_cislo, podnet, cislo_popisne
alter table archeologicky_dokumentacni_bod alter column typ_sondy drop not null;
alter table archeologicky_dokumentacni_bod alter column trat drop not null;
alter table archeologicky_dokumentacni_bod alter column parcelni_cislo drop not null;
alter table archeologicky_dokumentacni_bod alter column podnet drop not null;
alter table archeologicky_dokumentacni_bod alter column cislo_popisne drop not null;
--2. let.datum, pozorovatel
alter table let alter column datum drop not null;
alter table let alter column pozorovatel drop not null;
--3. neident_akce.katastr
alter table neident_akce alter column katastr drop not null;

--Upravit cizi klic:
--1. samostatny_nalez.katastr -> katastr_storage
-- DONE
-- 2. externi_odkaz.vazba -> externi_odkaz_vazby
-- tohle je mozne udelat az po migraci dat z vazba do odpovidajicich tabulek. Ted jsou tam reference ne na zaznamy z exteni_odkaz_vazby ale na akce a lokality DONE LATER
--3. dokument_cast.vazba -> dokument_cast_vazby
-- tohle je mozne udelat az po migraci dat z vazba do odpovidajicich tabulek DONE LATER

-- DRUHA CAST MIGRACE

--Odstraneni Atree foreign keys:
-- Reference na tabulku spz_storage
-- Akce
ALTER TABLE akce DROP CONSTRAINT akce_spz_fkey;
ALTER TABLE akce ADD CONSTRAINT akce_okres_fkey FOREIGN KEY (okres) REFERENCES spz_storage(id);
-- Lokalita
ALTER TABLE lokalita DROP CONSTRAINT lokalita_okres_fkey;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_okres_fkey FOREIGN KEY (okres) REFERENCES spz_storage(id);
-- Projekt
ALTER TABLE projekt DROP CONSTRAINT projekt_spz_fkey;
ALTER TABLE projekt ADD CONSTRAINT projekt_okres_fkey FOREIGN KEY (okres) REFERENCES spz_storage(id);
-- Neident akce
ALTER TABLE neident_akce DROP CONSTRAINT neident_akce_okres_fkey;
ALTER TABLE neident_akce ADD CONSTRAINT neident_akce_okres_fkey FOREIGN KEY (okres) REFERENCES spz_storage(id);
-- Reference na tabulku katastr_storage
-- Projekt
ALTER TABLE projekt DROP CONSTRAINT projekt_katastr_fkey;
ALTER TABLE projekt ADD CONSTRAINT projekt_katastr_fkey FOREIGN KEY (katastr) REFERENCES katastr_storage(id);
-- Lokalita
ALTER TABLE lokalita DROP CONSTRAINT lokalita_katastr_fkey;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_katastr_fkey FOREIGN KEY (katastr) REFERENCES katastr_storage(id);
-- Samostatny nalez
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostany_nalez_katastr_fkey;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_katastr_fkey FOREIGN KEY (katastr) REFERENCES katastr_storage(id);
-- Reference na user_group_auth_storage
-- Migrace auth_level sloupce
update user_storage as t1 set auth_level = (select t2.auth_level from user_group_auth_storage as t2 where t2.user_group_id = t1.id);
-- Reference na tabulku organizace
-- User storage
ALTER TABLE user_storage DROP CONSTRAINT user_storage_organizace_fkey;
ALTER TABLE user_storage ADD CONSTRAINT user_storage_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace(id);

-- Identifikujici reference
ALTER TABLE akce DROP CONSTRAINT akce_id_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_id_fkey;
ALTER TABLE dokumentacni_jednotka DROP CONSTRAINT dokumentacni_jednotka_id_fkey;
ALTER TABLE externi_zdroj DROP CONSTRAINT externi_zdroj_id_fkey;
ALTER TABLE katastr_storage DROP CONSTRAINT katastr_storage_id_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_id_fkey;
ALTER TABLE mass_storage DROP CONSTRAINT mass_storage_id_fkey;
ALTER TABLE neident_akce DROP CONSTRAINT neident_akce_id_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_id_fkey;
ALTER TABLE spz_storage DROP CONSTRAINT spz_storage_id_fkey;
ALTER TABLE user_storage DROP CONSTRAINT user_storage_id_fkey;
-- Dalsi neidentifikujici reference
ALTER TABLE spz_storage DROP constraint spz_storage_kraj_fkey;
update spz_storage set kraj = 1 where kraj = 67;
update spz_storage set kraj = 2 where kraj = 66;
update spz_storage set kraj = 3 where kraj = 68;
update spz_storage set kraj = 4 where kraj = 69;
update spz_storage set kraj = 5 where kraj = 71;
update spz_storage set kraj = 6 where kraj = 70;
update spz_storage set kraj = 7 where kraj = 72;
update spz_storage set kraj = 8 where kraj = 75;
update spz_storage set kraj = 9 where kraj = 73;
update spz_storage set kraj = 10 where kraj = 329173;
update spz_storage set kraj = 11 where kraj = 329174;
update spz_storage set kraj = 12 where kraj = 329175;
update spz_storage set kraj = 13 where kraj = 329176;
update spz_storage set kraj = 14 where kraj = 74;

ALTER TABLE user_notify DROP constraint user_notify_kraj_id_fkey;
-- Reference typu parent, vazba ...
ALTER TABLE dokumentacni_jednotka drop constraint dj_parent_fkey;
ALTER TABLE komponenta drop constraint komponenta_parent_fkey;
ALTER TABLE komponenta_dokument drop constraint komponenta_dokument_parent_fkey;
ALTER TABLE externi_odkaz drop constraint externi_odkaz_vazba_fkey;
ALTER TABLE dokument_cast drop constraint jednotka_dokument_vazba_fkey;

-- Vytvorit sekvence pro tabulky ktere meli spolecnou sekvenci s atree
CREATE SEQUENCE public.akce_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('akce_id_seq', (select MAX(id) from akce) + 1);
CREATE SEQUENCE public.dokument_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('dokument_id_seq', (select MAX(id) from dokument) + 1);
CREATE SEQUENCE public.dokumentacni_jednotka_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('dokumentacni_jednotka_id_seq', (select MAX(id) from dokumentacni_jednotka) + 1);
CREATE SEQUENCE public.externi_zdroj_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('externi_zdroj_id_seq', (select MAX(id) from externi_zdroj) + 1);
CREATE SEQUENCE public.katastr_storage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('katastr_storage_id_seq', (select MAX(id) from katastr_storage) + 1);
CREATE SEQUENCE public.lokalita_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('lokalita_id_seq', (select MAX(id) from lokalita) + 1);
-- COMMENT: tady jsem se zda se spletl a neident_akce ma svuj vlastni primarni klic
--CREATE SEQUENCE public.neident_akce_id_seq
--    START WITH 1
--    INCREMENT BY 1
--    NO MINVALUE
--    NO MAXVALUE
--    CACHE 1;
--select setval('neident_akce_id_seq', (select MAX(id) from neident_akce) + 1);
CREATE SEQUENCE public.projekt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('projekt_id_seq', (select MAX(id) from projekt) + 1);
CREATE SEQUENCE public.spz_storage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('spz_storage_id_seq', (select MAX(id) from spz_storage) + 1);
CREATE SEQUENCE public.user_storage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
select setval('user_storage_id_seq', (select MAX(id) from user_storage) + 1);
