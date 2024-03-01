-- SQL prikazy migrace struktury a dat databaze AMCR. V teto casti jde hlavne o vytvoreni a migraci dat do nove struktury tabulek heslaru.

-- Prejmenovat sloupce
--1. ruian_okres.en -> nazev_en
alter table ruian_okres rename column en to nazev_en;
--2. stats_login.user_id -> uzivatel
alter table stats_login rename column user_id to uzivatel;

-- Nove tabulky a sekvence

--1. heslar
CREATE SEQUENCE public.heslar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.heslar_id_seq OWNER TO cz_archeologickamapa_api;
CREATE TABLE public.heslar (
    id integer DEFAULT nextval('public.heslar_id_seq'::regclass) NOT NULL,
    ident_cely text NOT NULL UNIQUE,
    nazev_heslare integer NOT NULL,
    heslo text NOT NULL,
    popis text,
    zkratka text,
    heslo_en text NOT NULL,
    popis_en text,
    zkratka_en text,
    razeni integer
);
ALTER TABLE heslar ADD CONSTRAINT heslar_pkey PRIMARY KEY (id);
ALTER TABLE heslar ADD CONSTRAINT heslar_heslo_key UNIQUE(nazev_heslare, heslo);
ALTER TABLE heslar ADD CONSTRAINT heslar_zkratka_key UNIQUE(nazev_heslare, zkratka);
ALTER TABLE heslar ADD CONSTRAINT heslar_heslo_en_key UNIQUE(nazev_heslare, heslo_en);
ALTER TABLE heslar ADD CONSTRAINT heslar_zkratka_en_key UNIQUE(nazev_heslare, zkratka_en);
--2. heslar_datace
CREATE TABLE public.heslar_datace (
    obdobi integer PRIMARY KEY,
    rok_od_min integer not null,
    rok_od_max integer not null,
    rok_do_min integer not null,
    rok_do_max integer not null,
    region integer unique
);
ALTER TABLE heslar_datace ADD CONSTRAINT heslar_datace_obdobi_fkey foreign key (obdobi) references heslar(id);
ALTER TABLE heslar_datace ADD CONSTRAINT heslar_datace_region_fkey foreign key (region) references heslar(id);
--3. heslar_hierarchie
CREATE TABLE public.heslar_hierarchie (
    heslo_podrazene integer not null,
    heslo_nadrazene integer not null,
    typ text not null

);
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_heslo_podrazene_fkey foreign key (heslo_podrazene) references heslar(id);
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_heslo_nadrazene_fkey foreign key (heslo_nadrazene) references heslar(id);
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_pkey PRIMARY KEY (heslo_podrazene, heslo_nadrazene, typ);
--5. heslar_nazev
CREATE SEQUENCE public.heslar_nazev_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.heslar_nazev_id_seq OWNER TO cz_archeologickamapa_api;
CREATE TABLE public.heslar_nazev (
    id integer DEFAULT nextval('public.heslar_nazev_id_seq'::regclass) NOT NULL,
    heslar text not null unique,
    povolit_zmeny boolean not null default true
);
ALTER TABLE heslar_nazev ADD CONSTRAINT heslar_nazev_pkey PRIMARY KEY (id);
--6. heslar_odkaz
CREATE SEQUENCE public.heslar_odkaz_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.heslar_odkaz_id_seq OWNER TO cz_archeologickamapa_api;
CREATE TABLE public.heslar_odkaz (
    id integer DEFAULT nextval('public.heslar_odkaz_id_seq'::regclass) NOT NULL,
    heslo integer not null,
    zdroj text not null,
    nazev_kodu text not null,
    kod text not null,
    uri text
);
ALTER TABLE heslar_odkaz ADD CONSTRAINT heslar_odkaz_pkey PRIMARY KEY (id);
ALTER TABLE heslar_odkaz ADD CONSTRAINT heslar_odkaz_heslo_fkey foreign key (heslo) references heslar(id);

-- Novy sloupec

--1. akce.ulozeni_dokumentace
alter table akce add column ulozeni_dokumentace text;
--2. dokument.licence
alter table dokument add column licence_id integer;
--3. lokalita.zachovalost
alter table lokalita add column zachovalost integer;
--4. lokalita.jistota
alter table lokalita add column jistota integer;
--5. organizace.ident_cely
-- ERROR: je poteba vygenerovat ident_cely
--alter table organizace add column ident_cely text not null unique;
--6. osoba.ident_cely
-- ERROR: je poteba vygenerovat ident_cely
--alter table osoba add column ident_cely text not null unique;
--7. projekt.oznaceni_stavby
alter table projekt add column oznaceni_stavby text;

-- Nove foreign keys

--1. heslar.nazev_heslare -> heslar_nazev
alter table heslar add constraint heslar_nazev_heslare_fkey foreign key (nazev_heslare) references heslar_nazev(id);
--2. heslar_datace.obdobi -> heslar DONE
--3. heslar_datace.region -> heslar DONE
--4. heslar_hierarchie.heslo_podrazene -> heslar DONE
--5. heslar_hierarchie.heslo_nadrazene -> heslar DONE
--6. heslar_odkaz.heslo -> heslar DONE
--7. lokalita.zachovalost -> heslar
alter table lokalita add constraint lokalita_zachovalost_fkey foreign key (zachovalost) references heslar(id);
--8. lokalita.jistota -> heslar
alter table lokalita add constraint lokalita_jistota_fkey foreign key (jistota) references heslar(id);

-- Odebrat ID a sekvence a primarni klic bude sloupec ciziho klice na parent zaznam
-- Odebrat unique constraint COMMENT: tohle podle mne neni potreba delat.
--1. adb.dokumentacni_jednotka
alter table adb drop constraint adb_dokumentacni_jednotka_key;
--2. neident_akce.dokument_cast COMMENT: tady nebyl unique constraint
--3. dokument_extra_data.dokument
alter table dokument_extra_data drop constraint dokument_extra_data_dokument_key;

-- Upravit cizi klic (odstaneni stareho, namapovani referenci z vyskovy_bod na novy budouci primarni klic a vytvoreni ciziho klice)
--1. vyskovy_bod.adb -> adb.dokumentacni_jednotka
alter table vyskovy_bod drop constraint vyskovy_bod_parent_fkey;
alter table adb add constraint adb_dokumentacni_jednotka_key unique(dokumentacni_jednotka);
-- COMMENT: mapovani adb.id na adb.dokumentacni_jednotka
update vyskovy_bod b set adb = sub.dj from (select b.adb as adb, a.id as id, a.dokumentacni_jednotka as dj from vyskovy_bod b join adb a on b.adb = a.id) sub where b.adb = sub.id;
alter table vyskovy_bod add constraint vyskovy_bod_adb_fkey foreign key (adb) references adb(dokumentacni_jednotka);

--2. neident_akce_vedouci.neident_akce -> neident_akce.dokument_cast
alter table neident_akce_vedouci drop constraint neident_akce_vedouci_neident_akce_fk;
alter table neident_akce add constraint neident_akce_dokument_cast_key unique(dokument_cast);
-- COMMENT: Tohle by bylo potreba volat kdyby tabulka neident_akce_vedouci nebyla prazdna
--update neident_akce_vedouci nav set neident_akce = sub.dc from (select nav.neident_akce as nakce, na.id as id, na.dokument_cast as dc from neident_akce_vedouci nav join neident_akce na on nav.neident_akce = na.id) sub where nav.neident_akce = sub.id;
alter table neident_akce_vedouci add constraint neident_akce_vedouci_neident_akce_fk foreign key (neident_akce) references neident_akce(dokument_cast);

-- Pridat primarni klic
--1. adb.dokumentacni_jednotka
alter table adb drop constraint archeologicky_dokumentacni_bod_id;
alter table adb add constraint adb_pkey primary key (dokumentacni_jednotka);
--2. neident_akce.dokument_cast
--alter table neident_akce drop constraint neident_akce_pkey;
-- MIGRACE: v tabulce dokument_cast je sloupec vazba a ten obsahuje id zaznamu 3 typu (akce, lokalita nebo neident_akce), je potreba vybrat ty ktere ukazuji na id-cka zaznamu z tabulky neident_akce a zmigrovat tuto referenci do sloupce dokument_cast v tabulce neident_akce)
--alter table neident_akce add constraint neident_akce_pkey primary key (dokument_cast);
--3. dokument_extra_data.dokument
alter table dokument_extra_data drop constraint extra_data_pkey;
alter table dokument_extra_data add constraint dokument_extra_data_pkey PRIMARY KEY(dokument);
