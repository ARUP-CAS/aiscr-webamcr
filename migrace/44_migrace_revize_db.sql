ALTER TABLE vyskovy_bod DROP CONSTRAINT vyskovy_bod_adb_fkey;
ALTER TABLE adb DROP CONSTRAINT adb_dokumentacni_jednotka_key;
ALTER TABLE vyskovy_bod ADD CONSTRAINT vyskovy_bod_adb_fkey FOREIGN KEY (adb) REFERENCES adb (dokumentacni_jednotka) ON UPDATE CASCADE ON DELETE CASCADE;
COMMENT ON COLUMN adb.dokumentacni_jednotka IS NULL;

ALTER TABLE akce_vedouci DROP CONSTRAINT akce_vedouci_akce_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_organizace_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_archeologicky_zaznam_key;
ALTER TABLE akce ADD CONSTRAINT akce_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace(id) ON UPDATE CASCADE ON DELETE NO ACTION;

ALTER TABLE akce_vedouci ALTER COLUMN organizace set NOT NULL;
ALTER TABLE akce_vedouci DROP CONSTRAINT akce_vedouci_pkey;
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_pkey PRIMARY KEY (id);
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_akce_vedouci_key UNIQUE (akce, vedouci);

ALTER TABLE archeologicky_zaznam ALTER COLUMN ident_cely SET NOT NULL;
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_ident_cely_key UNIQUE (ident_cely);
ALTER TABLE archeologicky_zaznam DROP COLUMN stav_stary;
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_historie_key UNIQUE (historie);
ALTER TABLE archeologicky_zaznam ALTER COLUMN hlavni_katastr SET NOT NULL;

ALTER TABLE archeologicky_zaznam_katastr DROP CONSTRAINT archeologicky_zaznam_katastr_pkey;
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_akce_fkey FOREIGN KEY (akce) REFERENCES akce (archeologicky_zaznam) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE archeologicky_zaznam_katastr ADD CONSTRAINT archeologicky_zaznam_katastr_pkey PRIMARY KEY (id);
ALTER TABLE archeologicky_zaznam_katastr ADD CONSTRAINT archeologicky_zaznam_katastr_archeologicky_zaznam_id_katastr_id_key UNIQUE ( archeologicky_zaznam_id, katastr_id);

ALTER TABLE auth_user DROP COLUMN email_potvrzen;
ALTER TABLE auth_user ADD CONSTRAINT auth_user_email_key UNIQUE (email);
ALTER TABLE auth_user ADD CONSTRAINT auth_user_historie_key UNIQUE (historie);

ALTER TABLE dokument ADD CONSTRAINT dokument_soubory_key UNIQUE (soubory);
ALTER TABLE dokument ADD CONSTRAINT dokument_historie_key UNIQUE (historie);
COMMENT ON COLUMN dokument.let IS NULL;
COMMENT ON COLUMN dokument.rada IS NULL;
COMMENT ON COLUMN dokument.typ_dokumentu IS NULL;
COMMENT ON COLUMN dokument.rok_vzniku IS NULL;
COMMENT ON COLUMN dokument.material_originalu IS NULL;
COMMENT ON COLUMN dokument.ulozeni_originalu IS NULL;

ALTER TABLE dokument_autor DROP CONSTRAINT dokument_autor_pkey;
ALTER TABLE dokument_autor ADD CONSTRAINT dokument_autor_pkey PRIMARY KEY (id);
ALTER TABLE dokument_autor ADD CONSTRAINT dokument_autor_dokument_autor_key UNIQUE ( dokument, autor);
ALTER TABLE dokument_autor ADD CONSTRAINT dokument_autor_dokument_poradi_key UNIQUE (dokument, poradi);

COMMENT ON COLUMN dokument_extra_data.zachovalost IS NULL;
COMMENT ON COLUMN dokument_extra_data.nahrada IS NULL;
COMMENT ON COLUMN dokument_extra_data.format IS NULL;
COMMENT ON COLUMN dokument_extra_data.zeme IS NULL;
COMMENT ON COLUMN dokument_extra_data.region IS NULL;
COMMENT ON COLUMN dokument_extra_data.udalost_typ IS NULL;

COMMENT ON COLUMN dokument_cast.archeologicky_zaznam IS NULL;
ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_vazba_check CHECK (NOT(archeologicky_zaznam IS NOT NULL AND projekt IS NOT NULL));
ALTER TABLE dokument_jazyk ADD CONSTRAINT dokument_jazyk_dokument_jazyk_key UNIQUE (dokument, jazyk);

ALTER TABLE dokument_osoba DROP CONSTRAINT dokument_osoba_pkey;
ALTER TABLE dokument_osoba ADD CONSTRAINT dokument_osoba_pkey PRIMARY KEY (id);
ALTER TABLE dokument_osoba ADD CONSTRAINT dokument_osoba_dokument_osoba_key UNIQUE (dokument, osoba);

ALTER TABLE dokument_posudek ADD CONSTRAINT dokument_posudek_dokument_posudek_key UNIQUE (dokument, posudek);

ALTER TABLE dokument_sekvence ADD CONSTRAINT dokument_sekvence_pkey PRIMARY KEY (id);

ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_komponenty_key UNIQUE (komponenty);
ALTER TABLE dokumentacni_jednotka ALTER COLUMN ident_cely SET NOT NULL;

ALTER TABLE externi_odkaz ALTER COLUMN externi_zdroj SET NOT NULL;
ALTER TABLE externi_odkaz ALTER COLUMN archeologicky_zaznam SET NOT NULL;
COMMENT ON COLUMN externi_odkaz.archeologicky_zaznam IS NULL;

ALTER TABLE externi_zdroj DROP COLUMN final_cj;
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_historie_key UNIQUE (historie);
ALTER TABLE externi_zdroj ALTER COLUMN ident_cely SET NOT NULL;
COMMENT ON COLUMN externi_zdroj.typ IS NULL;
COMMENT ON COLUMN externi_zdroj.typ_dokumentu IS NULL;

ALTER TABLE externi_zdroj_autor DROP CONSTRAINT externi_zdroj_autor_pkey;
CREATE SEQUENCE externi_zdroj_autor_id_seq;
ALTER TABLE externi_zdroj_autor ADD COLUMN id integer NOT NULL default nextval('externi_zdroj_autor_id_seq'::regclass) PRIMARY KEY;
ALTER TABLE externi_zdroj_autor ADD CONSTRAINT externi_zdroj_autor_externi_zdroj_autor_key UNIQUE (externi_zdroj, autor);
ALTER TABLE externi_zdroj_autor ADD CONSTRAINT externi_zdroj_autor_externi_zdroj_poradi_key UNIQUE (externi_zdroj, poradi);

CREATE SEQUENCE externi_zdroj_editor_id_seq;
ALTER TABLE externi_zdroj_editor DROP constraint externi_zdroj_editor_pkey;
ALTER TABLE externi_zdroj_editor ADD COLUMN id integer NOT NULL default nextval('externi_zdroj_editor_id_seq'::regclass) PRIMARY KEY;
ALTER TABLE externi_zdroj_editor ADD CONSTRAINT externi_zdroj_editor_externi_zdroj_editor_key UNIQUE (externi_zdroj, editor);

ALTER TABLE heslar ALTER COLUMN ident_cely SET NOT NULL;
ALTER TABLE heslar ALTER COLUMN heslo SET NOT NULL;
ALTER TABLE heslar ALTER COLUMN heslo_en SET NOT NULL;
ALTER TABLE heslar DROP COLUMN puvodni_id;
ALTER TABLE heslar ADD CONSTRAINT heslar_nazev_heslare_heslo_key UNIQUE (nazev_heslare, heslo);
ALTER TABLE heslar ADD CONSTRAINT heslar_nazev_heslare_heslo_en_key UNIQUE (nazev_heslare, heslo_en);

ALTER TABLE heslar_datace DROP COLUMN region;
ALTER TABLE heslar_datace ADD COLUMN poznamka text;

ALTER TABLE heslar_dokument_typ_material_rada DROP COLUMN validated;
ALTER TABLE heslar_dokument_typ_material_rada DROP constraint heslar_typ_material_rada_heslar_rada_id_heslar_typ_dokumentu_id;

CREATE SEQUENCE heslar_hierarchie_id_seq;
ALTER TABLE heslar_hierarchie drop constraint heslar_hierarchie_pkey;
ALTER TABLE heslar_hierarchie ADD COLUMN id integer NOT NULL default nextval('heslar_hierarchie_id_seq'::regclass) PRIMARY KEY;
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_heslo_podrazene_heslo_nadrazene_typ_key UNIQUE (heslo_podrazene, heslo_nadrazene, typ);
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_typ_check CHECK (typ IN ('podřízenost', 'uplatnění', 'výchozí hodnota'));

ALTER TABLE historie DROP COLUMN typ_zmeny_old;

ALTER TABLE komponenta ALTER COLUMN komponenta_vazby SET NOT NULL;

ALTER TABLE komponenta_vazby ALTER COLUMN typ_vazby SET NOT NULL;

ALTER TABLE komponenta_aktivita DROP CONSTRAINT komponenta_aktivita_pkey;
ALTER TABLE komponenta_aktivita ADD CONSTRAINT komponenta_aktivita_pkey PRIMARY KEY (id);
ALTER TABLE komponenta_aktivita ADD CONSTRAINT komponenta_aktivita_komponenta_aktivita_key UNIQUE (komponenta, aktivita);

ALTER TABLE let ALTER COLUMN ident_cely SET NOT NULL;
COMMENT ON COLUMN let.pozorovatel IS NULL;
COMMENT ON COLUMN let.letiste_start IS NULL;
COMMENT ON COLUMN let.letiste_cil IS NULL;
COMMENT ON COLUMN let.pocasi IS NULL;
COMMENT ON COLUMN let.dohlednost IS NULL;
ALTER TABLE let ALTER COLUMN datum TYPE date USING DATE(datum);

ALTER TABLE lokalita DROP CONSTRAINT lokalita_archeologicky_zaznam_key;

ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_pkey PRIMARY KEY (id);

ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_pkey PRIMARY KEY (id);

ALTER TABLE neident_akce DROP COLUMN ident_cely;
COMMENT ON COLUMN neident_akce.katastr IS NULL;

CREATE SEQUENCE notifikace_projekt_id_seq;
ALTER TABLE notifikace_projekt ADD COLUMN id integer NOT NULL DEFAULT nextval('notifikace_projekt_id_seq'::regclass) PRIMARY KEY;

ALTER TABLE odstavky_systemu ADD CONSTRAINT odstavky_systemu_pkey PRIMARY KEY (id);

ALTER TABLE organizace ALTER COLUMN nazev_zkraceny_en SET NOT NULL;
CREATE SEQUENCE organizace_ident_cely_seq START WITH 1 INCREMENT BY 1 MINVALUE 0 MAXVALUE 999999 ;
ALTER TABLE organizace ADD COLUMN ident_cely text NOT NULL DEFAULT('ORG-'::text || right(concat('000000', nextval('organizace_ident_cely_seq')::text), 6));
ALTER TABLE organizace ADD CONSTRAINT organizace_ident_cely_key UNIQUE(ident_cely);
ALTER TABLE organizace ADD CONSTRAINT organizace_nazev_zkraceny_key UNIQUE(nazev_zkraceny);
COMMENT ON COLUMN organizace.typ_organizace IS NULL;

CREATE SEQUENCE osoba_ident_cely_seq START WITH 1 INCREMENT BY 1 MINVALUE 0 MAXVALUE 999999 ;
ALTER TABLE osoba ADD COLUMN ident_cely text NOT NULL DEFAULT('OS-'::text || right(concat('000000', nextval('osoba_ident_cely_seq')::text), 6));
ALTER TABLE osoba ADD CONSTRAINT osoba_ident_cely_key UNIQUE(ident_cely);

ALTER TABLE oznamovatel DROP COLUMN id;
ALTER TABLE oznamovatel ADD CONSTRAINT oznamovatel_pkey PRIMARY KEY (projekt);
ALTER TABLE oznamovatel DROP CONSTRAINT oznamovatel_projekt_key;

ALTER TABLE pian ADD CONSTRAINT pian_historie_key UNIQUE(historie);
COMMENT ON COLUMN ruian_katastr.id IS NULL;

ALTER TABLE projekt DROP COLUMN planovane_zahajeni_text;
ALTER TABLE projekt ALTER COLUMN ident_cely SET NOT NULL ;
ALTER TABLE projekt ADD CONSTRAINT projekt_soubory_key UNIQUE(soubory);
ALTER TABLE projekt ADD CONSTRAINT projekt_historie_key UNIQUE(historie);

ALTER TABLE projekt_katastr DROP CONSTRAINT projekt_katastr_pkey;
ALTER TABLE projekt_katastr ADD CONSTRAINT projekt_katastr_pkey PRIMARY KEY (id);
ALTER TABLE projekt_katastr ADD CONSTRAINT projekt_katastr_projekt_id_katastr_id_key UNIQUE (projekt_id, katastr_id);

ALTER TABLE projekt_sekvence ADD CONSTRAINT projekt_sekvence_pkey PRIMARY KEY (id);

ALTER TABLE ruian_katastr ALTER COLUMN hranice SET NOT NULL ;
ALTER TABLE ruian_katastr DROP COLUMN poznamka ;
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_pian_key UNIQUE(pian);

ALTER TABLE ruian_kraj DROP COLUMN aktualni;
ALTER TABLE ruian_kraj ADD COLUMN nazev_en text;
UPDATE ruian_kraj SET nazev_en = nazev;
ALTER TABLE ruian_kraj ALTER COLUMN nazev_en SET NOT NULL;

ALTER TABLE ruian_okres DROP COLUMN aktualni;
ALTER TABLE ruian_okres ALTER COLUMN nazev_en SET NOT NULL;
ALTER TABLE ruian_okres ADD CONSTRAINT ruian_okres_nazev_key UNIQUE(nazev);
ALTER TABLE ruian_okres ADD CONSTRAINT ruian_okres_kod_key UNIQUE(kod);
ALTER TABLE ruian_okres ADD CONSTRAINT ruian_okres_spz_key UNIQUE(spz);

ALTER TABLE samostatny_nalez ALTER COLUMN ident_cely SET NOT NULL;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_soubory_key UNIQUE(soubory);
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_historie_key UNIQUE(historie);

DROP TABLE stats_login;

COMMENT ON COLUMN tvar.tvar IS NULL;

CREATE SEQUENCE uzivatel_notifikace_id_seq;
ALTER TABLE uzivatel_notifikace ADD COLUMN id integer NOT NULL default nextval('uzivatel_notifikace_id_seq'::regclass) PRIMARY KEY;

ALTER TABLE uzivatel_spoluprace ADD CONSTRAINT uzivatel_spoluprace_historie_key UNIQUE(historie);

ALTER TABLE vyskovy_bod DROP COLUMN northing;
ALTER TABLE vyskovy_bod DROP COLUMN easting;
ALTER TABLE vyskovy_bod DROP COLUMN niveleta;
ALTER TABLE vyskovy_bod DROP COLUMN poradi;
ALTER TABLE vyskovy_bod ADD CONSTRAINT vyskovy_bod_pkey PRIMARY KEY (id);
