--Novy sloupec:
ALTER TABLE dokumentacni_jednotka ADD pian int;
ALTER TABLE akce ADD projekt int;

--Migrace tabulky:
-- Migrace tabulky dokument_soubor_fs
update soubor set dokument = dokument_soubor_fs.dokument from dokument_soubor_fs where dokument_soubor_fs.soubor_fs = soubor.id and dokument_soubor_fs.dokument in (select id from dokument);

-- Vytvoreni tabulky
CREATE SEQUENCE public.historie_akce_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE public.historie_akce (
    id integer DEFAULT nextval('public.historie_akce_seq'::regclass) NOT NULL,
    datum_zmeny timestamp with time zone,
    typ_zmeny integer,
    akce integer,
    uzivatel integer,
    zprava text
);
ALTER TABLE ONLY public.historie_akce ADD CONSTRAINT historie_akce_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.historie_akce ADD CONSTRAINT historie_akce_uzivatel_fkey FOREIGN KEY (uzivatel) REFERENCES public.user_storage(id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE ONLY public.historie_akce ADD CONSTRAINT historie_akce_akce_fkey FOREIGN KEY (akce) REFERENCES public.akce(id) ON UPDATE CASCADE ON DELETE CASCADE;
-- Migrace sloupce zprava do historie_akce a typ_logu(0 = 7, 1 = 3) do typ zmeny a id_objektu do akce
insert into historie_akce(typ_zmeny, akce, uzivatel, zprava, datum_zmeny) select typ_logu, id_objektu, uzivatel, zprava, (SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (cas::int) * INTERVAL '1 second') from log where log.id_objektu in (select id from akce);
update historie_akce set typ_zmeny = 3 where typ_zmeny = 1;
update historie_akce set typ_zmeny = 7 where typ_zmeny = 0;

-- Doplnění historie_akce o chybějící údaje stejného typu z tabulky akce (zbytek migrován v migrace_3.sql).
-- Stav 3
INSERT INTO historie_akce ( uzivatel, datum_zmeny, typ_zmeny, akce )
SELECT akce.odpovedny_pracovnik_vraceni_zaa, (SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (akce.datum_vraceni_zaa::int) * INTERVAL '1 second'), 3 AS typ, akce.id
FROM akce LEFT JOIN historie_akce ON (akce.odpovedny_pracovnik_vraceni_zaa = historie_akce.uzivatel) AND ((SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (akce.datum_vraceni_zaa::int) * INTERVAL '1 second') = historie_akce.datum_zmeny) AND (akce.id = historie_akce.akce)
WHERE (((akce.odpovedny_pracovnik_vraceni_zaa) Is Not Null) AND ((historie_akce.id) Is Null)) OR (((akce.datum_vraceni_zaa) Is Not Null) AND ((historie_akce.id) Is Null));

-- Stav 7
INSERT INTO historie_akce ( uzivatel, datum_zmeny, typ_zmeny, akce )
SELECT akce.odpovedny_pracovnik_zamitnuti, akce.datum_zamitnuti, 7 AS typ, akce.id
FROM akce LEFT JOIN historie_akce ON (akce.odpovedny_pracovnik_zamitnuti = historie_akce.uzivatel) AND (akce.datum_zamitnuti = (historie_akce.datum_zmeny::date)) AND (akce.id = historie_akce.akce)
WHERE (((akce.odpovedny_pracovnik_zamitnuti) Is Not Null) AND ((historie_akce.id) Is Null)) OR (((akce.datum_zamitnuti) Is Not Null) AND ((historie_akce.id) Is Null));


--migrace pian_parent.geom do projekt.geom)
ALTER TABLE projekt ADD geom public.geometry;
update projekt set geom = pian_projekt.geom from pian_projekt where pian_projekt.projekt = projekt.id and pian_projekt.projekt in (select id from projekt);

-- migrace user_deactivation_times
insert into historie_user_storage(typ_zmeny, ucet, datum_zmeny, komentar) select activation::int, user_id, time, auth_level from user_deactivation_times where user_id in (select id from user_storage);
update historie_user_storage set uzivatel = '598610';

-- migrace vazba_pian_parent
update dokumentacni_jednotka set pian = vazba_pian_parent.pian from vazba_pian_parent where vazba_pian_parent.parent = dokumentacni_jednotka.id and vazba_pian_parent.pian in (select id from pian);

-- migrace vazba_projekt_akce
update akce set projekt = vazba_projekt_akce.projekt from vazba_projekt_akce where vazba_projekt_akce.akce = akce.id;

-- Nove cizi klice:
ALTER TABLE akce ADD CONSTRAINT akce_hlavni_typ_fkey FOREIGN KEY (hlavni_typ) REFERENCES heslar_typ_akce_druha(id);
UPDATE akce SET vedlejsi_typ = null WHERE vedlejsi_typ = -1;
ALTER TABLE akce ADD CONSTRAINT akce_vedlejsi_typ_fkey FOREIGN KEY (vedlejsi_typ) REFERENCES heslar_typ_akce_druha(id);
UPDATE akce SET organizace = null WHERE organizace = -1;
ALTER TABLE akce ADD CONSTRAINT akce_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace(id);
ALTER TABLE dokument ADD CONSTRAINT dokument_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace(id);
ALTER TABLE dokument ADD CONSTRAINT dokument_odpovedny_pracovnik_archivace_fkey FOREIGN KEY (odpovedny_pracovnik_archivace) REFERENCES user_storage(id);

UPDATE externi_zdroj SET typ_dokumentu = null WHERE typ_dokumentu = -1;
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_typ_dokumentu_fkey FOREIGN KEY (typ_dokumentu) REFERENCES heslar_typ_dokumentu(id);
UPDATE extra_data SET zachovalost = null WHERE zachovalost = -1;
ALTER TABLE extra_data ADD CONSTRAINT extra_data_zachovalost_fkey FOREIGN KEY (zachovalost) REFERENCES heslar_zachovalost(id);
UPDATE extra_data SET nahrada = null WHERE nahrada = -1;
ALTER TABLE extra_data ADD CONSTRAINT extra_data_nahrada_fkey FOREIGN KEY (nahrada) REFERENCES heslar_nahrada(id);
UPDATE extra_data SET format = null WHERE format = -1;
ALTER TABLE extra_data ADD CONSTRAINT extra_data_format_fkey FOREIGN KEY (format) REFERENCES heslar_format_dokumentu(id);
UPDATE extra_data SET zeme = null WHERE zeme = -1;
ALTER TABLE extra_data ADD CONSTRAINT extra_data_zeme_fkey FOREIGN KEY (zeme) REFERENCES heslar_zeme(id);
UPDATE extra_data SET udalost_typ = null WHERE udalost_typ = -1;
ALTER TABLE extra_data ADD CONSTRAINT extra_data_udalost_typ_fkey FOREIGN KEY (udalost_typ) REFERENCES heslar_typ_udalosti(id);
update heslar_predmet_druh set implicitni_material = null where implicitni_material = -1;
ALTER TABLE heslar_predmet_druh ADD CONSTRAINT predmet_druh_implicitni_material_fkey FOREIGN KEY (implicitni_material) REFERENCES heslar_specifikace_predmetu(id);
ALTER TABLE heslar_specifikace_objektu_druha ADD CONSTRAINT specifikace_objektu_druha_prvni_fkey FOREIGN KEY (prvni) REFERENCES heslar_specifikace_objektu_prvni(id);
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_nalezce_fkey FOREIGN KEY (nalezce) REFERENCES heslar_jmena(id);
-- ERROR Neexistujici vlastnik a je tam not-null constraint??
--UPDATE soubor SET vlastnik = null WHERE vlastnik = 66050;
ALTER TABLE soubor ADD CONSTRAINT soubor_vlastnik_fkey FOREIGN KEY (vlastnik) REFERENCES user_storage(id);
ALTER TABLE soubor ADD CONSTRAINT soubor_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt(id);
ALTER TABLE tvar ADD CONSTRAINT tvar_tvar_fkey FOREIGN KEY (tvar) REFERENCES heslar_tvar(id);
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_pian_fkey FOREIGN KEY (pian) REFERENCES pian(id);
ALTER TABLE akce ADD CONSTRAINT akce_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt(id);

-- Smazat unique constraints (musim nejdriv smazat zavisle constrainy aby se pri vytvoreni constraint navazal na primary key ne na unique index)
ALTER TABLE nalez_dokument DROP CONSTRAINT nalez_dokument_komponenta_dokument_fkey;
ALTER TABLE komponenta_dokument DROP CONSTRAINT komponenta_dokument_nova_id_key;
ALTER TABLE nalez_dokument ADD CONSTRAINT nalez_dokument_komponenta_dokument_fkey FOREIGN KEY (komponenta_dokument) REFERENCES komponenta_dokument(id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE projekt DROP CONSTRAINT projekt_ident_cely_key1;

-- Nove not null constraints
ALTER TABLE samostatny_nalez alter column projekt set not null;
ALTER TABLE samostatny_nalez alter column pristupnost set not null;
-- ALTER TABLE samostatny_nalez alter column pristupnost set default 3;
ALTER TABLE vazba_spoluprace alter column aktivni set not null;
ALTER TABLE vazba_spoluprace alter column aktivni set default false;
ALTER TABLE vazba_spoluprace alter column potvrzeno set not null;
ALTER TABLE vazba_spoluprace alter column potvrzeno set default false;

-- Novy primarni klic
ALTER TABLE lokalita ADD PRIMARY KEY (id);
ALTER TABLE pian_sekvence ADD PRIMARY KEY (id);
ALTER TABLE user_notify ADD PRIMARY KEY (id);

-- Vytvorit heslar kraju
CREATE SEQUENCE public.heslar_kraj_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
CREATE TABLE public.heslar_kraj (
    id integer DEFAULT nextval('public.heslar_kraj_id_seq'::regclass) NOT NULL,
    heslo text NOT NULL,
    kod_ruian integer NOT NULL,
    id_c_m char(1) NOT NULL
);
ALTER TABLE ONLY public.heslar_kraj ADD CONSTRAINT heslar_kraj_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.heslar_kraj ADD CONSTRAINT heslar_kraj_heslo_key UNIQUE(heslo);
ALTER TABLE ONLY public.heslar_kraj ADD CONSTRAINT heslar_kraj_kod_ruian_key UNIQUE(kod_ruian);
ALTER SEQUENCE public.heslar_kraj_id_seq OWNED BY public.heslar_kraj.id;

-- Naplnit heslar kraju
insert into heslar_kraj(heslo,kod_ruian, id_c_m) values
('Středočeský kraj',27,'C'),
('Hlavní město Praha',19,'C'),
('Jihočeský kraj',35,'C'),
('Plzeňský kraj',43,'C'),
('Ústecký kraj',60,'C'),
('Karlovarský kraj',51,'C'),
('Liberecký kraj',78,'C'),
('Pardubický kraj',94,'C'),
('Královéhradecký kraj',86,'C'),
('Olomoucký kraj',124,'M'),
('Moravskoslezský kraj',132,'M'),
('Jihomoravský kraj',116,'M'),
('Zlínský kraj',141,'M'),
('Vysočina',108,'M');
