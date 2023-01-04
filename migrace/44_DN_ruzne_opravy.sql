-- Řešení pro chybějící či duplkicitní EN hesla.
UPDATE heslar SET heslo_en = 'translate: ' || ident_cely WHERE (heslo_en Is Null);
UPDATE heslar SET heslo_en = 'chain necklace' WHERE ident_cely = 'HES-000756';
UPDATE heslar SET heslo_en = 'chopper' WHERE ident_cely = 'HES-000801';
UPDATE organizace SET nazev_zkraceny_en = 'translate: ' || id WHERE (nazev_zkraceny_en Is Null);

-- Odstranění dokumentů ZA/ZL
DELETE FROM dokument, soubor USING dokument
INNER JOIN heslar ON dokument.rada = heslar.id
INNER JOIN soubor ON soubor.vazba = dokument.soubory
WHERE heslar.ident_cely = 'HES-000884' OR heslar.ident_cely = 'HES-000885';

-- Migrace soubor.vlastnik a soubor.vytvoreno do historie
UPDATE soubor SET historie = (INSERT INTO historie_vazby (typ_vazby) VALUES 'soubor' RETURNING id) WHERE soubor.historie IS NULL;
ALTER TABLE soubor ADD CONSTRAINT soubor_historie_key UNIQUE (historie);
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT vytvoreno, vlastnik, nazev_puvodni, historie, 'SBR0' FROM soubor;
ALTER TABLE soubor DROP COLUMN vytvoreno, vlastnik;

-- Smazat oznamovatele, pokud je všude „údaj odstraněn“
DELETE FROM oznamovatel WHERE email = 'údaj odstraněn' AND adresa = 'údaj odstraněn' AND odpovedna_osoba = 'údaj odstraněn' AND oznamovatel = 'údaj odstraněn' AND telefon = 'údaj odstraněn';

-- Odstranění nepotřebných tabulek
DROP TABLE projekt_oznameni_suffix;
DROP TABLE systemove_promenne;

-- Odstranění nepotřebných heslářů
DELETE FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'autorska_role');
DELETE FROM heslar_nazev WHERE nazev = 'autorska_role';

-- Nastavení editovatelnosti heslářů
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'adb_podnet';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'adb_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'akce_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'akce_typ_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'aktivita';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'areal';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'areal_kat';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'datum_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dohlednost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dok_jednotka_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_format';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_material';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_nahrada';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_rada';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_ulozeni';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_zachovalost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'ext_zdroj_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'jazyk';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'jistota_urceni';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'letfoto_tvar';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'letiste';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'lokalita_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'lokalita_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'lokalita_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'nalez_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'nalezove_okolnosti';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'obdobi';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'obdobi_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_specifikace_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'organizace_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pamatkova_ochrana';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pian_presnost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pian_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'pocasi';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'posudek_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pristupnost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'projekt_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'stav_dochovani';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'udalost_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'vyskovy_bod_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'zeme';

-- Doplnění check na hesláře, aby nemohlo dojít k tomu, že bude použito heslo ze špatného hesláře
ALTER TABLE adb ADD CONSTRAINT adb_typ_sondy_check CHECK (typ_sondy IS NULL OR typ_sondy IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'adb_typ')));
ALTER TABLE adb ADD CONSTRAINT adb_podnet_check CHECK (podnet IS NULL OR podnet IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'adb_podnet')));
ALTER TABLE akce ADD CONSTRAINT akce_specifikace_data_check CHECK (specifikace_data IS NULL OR specifikace_data IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'datum_specifikace')));
ALTER TABLE akce ADD CONSTRAINT akce_hlavni_typ_check CHECK (hlavni_typ IS NULL OR hlavni_typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'akce_typ')));
ALTER TABLE akce ADD CONSTRAINT akce_vedlejsi_typ_check CHECK (vedlejsi_typ IS NULL OR vedlejsi_typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'akce_typ')));
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_pristupnost_check CHECK (pristupnost IS NULL OR pristupnost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pristupnost')));
ALTER TABLE dokument ADD CONSTRAINT dokument_rada_check CHECK (rada IS NULL OR rada IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_rada')));
ALTER TABLE dokument ADD CONSTRAINT dokument_typ_dokumentu_check CHECK (typ_dokumentu IS NULL OR typ_dokumentu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_typ')));
ALTER TABLE dokument ADD CONSTRAINT dokument_pristupnost_check CHECK (pristupnost IS NULL OR pristupnost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pristupnost')));
ALTER TABLE dokument ADD CONSTRAINT dokument_material_originalu_check CHECK (material_originalu IS NULL OR material_originalu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_material')));
ALTER TABLE dokument ADD CONSTRAINT dokument_ulozeni_originalu_check CHECK (ulozeni_originalu IS NULL OR ulozeni_originalu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_ulozeni')));
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_zachovalost_check CHECK (zachovalost IS NULL OR zachovalost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_zachovalost')));
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_nahrada_check CHECK (nahrada IS NULL OR nahrada IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_nahrada')));
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_format_check CHECK (format IS NULL OR format IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_format')));
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_zeme_check CHECK (zeme IS NULL OR zeme IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'zeme')));
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_udalost_typ_check CHECK (udalost_typ IS NULL OR udalost_typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'udalost_typ')));
ALTER TABLE dokument_jazyk ADD CONSTRAINT dokument_jazyk_jazyk_check CHECK (jazyk IS NULL OR jazyk IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'jazyk')));
ALTER TABLE dokument_posudek ADD CONSTRAINT dokument_posudek_posudek_check CHECK (posudek IS NULL OR posudek IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'posudek_typ')));
ALTER TABLE dokument_sekvence ADD CONSTRAINT dokument_sekvence_rada_check CHECK (rada IS NULL OR rada IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_rada')));
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_typ_check CHECK (typ IS NULL OR typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dok_jednotka_typ')));
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_typ_check CHECK (typ IS NULL OR typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'ext_zdroj_typ')));
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_typ_dokumentu_check CHECK (typ_dokumentu IS NULL OR typ_dokumentu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_typ')));
ALTER TABLE heslar_datace ADD CONSTRAINT heslar_datace_obdobi_check CHECK (obdobi IS NULL OR obdobi IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'obdobi')));
ALTER TABLE heslar_dok_typ_material_rada ADD CONSTRAINT heslar_dok_typ_material_rada_dokument_rada_check CHECK (dokument_rada IS NULL OR dokument_rada IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_rada')));
ALTER TABLE heslar_dok_typ_material_rada ADD CONSTRAINT heslar_dok_typ_material_rada_dokument_typ_check CHECK (dokument_typ IS NULL OR dokument_typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_typ')));
ALTER TABLE heslar_dok_typ_material_rada ADD CONSTRAINT heslar_dok_typ_material_rada_dokument_material_check CHECK (dokument_material IS NULL OR dokument_material IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dokument_material')));
ALTER TABLE komponenta ADD CONSTRAINT komponenta_obdobi_check CHECK (obdobi IS NULL OR obdobi IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'obdobi')));
ALTER TABLE komponenta ADD CONSTRAINT komponenta_areal_check CHECK (areal IS NULL OR areal IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'areal')));
ALTER TABLE komponenta_aktivita ADD CONSTRAINT komponenta_aktivita_aktivita_check CHECK (aktivita IS NULL OR aktivita IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'aktivita')));
ALTER TABLE let ADD CONSTRAINT let_letiste_start_check CHECK (letiste_start IS NULL OR letiste_start IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'letiste')));
ALTER TABLE let ADD CONSTRAINT let_letiste_cil_check CHECK (letiste_cil IS NULL OR letiste_cil IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'letiste')));
ALTER TABLE let ADD CONSTRAINT let_pocasi_check CHECK (pocasi IS NULL OR pocasi IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pocasi')));
ALTER TABLE let ADD CONSTRAINT let_dohlednost_check CHECK (dohlednost IS NULL OR dohlednost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'dohlednost')));
ALTER TABLE lokalita ADD CONSTRAINT lokalita_druh_check CHECK (druh IS NULL OR druh IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'lokalita_druh')));
ALTER TABLE lokalita ADD CONSTRAINT lokalita_typ_lokality_check CHECK (typ_lokality IS NULL OR typ_lokality IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'lokalita_typ')));
ALTER TABLE lokalita ADD CONSTRAINT lokalita_zachovalost_check CHECK (zachovalost IS NULL OR zachovalost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'stav_dochovani')));
ALTER TABLE lokalita ADD CONSTRAINT lokalita_jistota_check CHECK (jistota IS NULL OR jistota IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'jistota_urceni')));
ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_druh_check CHECK (druh IS NULL OR druh IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'objekt_druh')));
ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_specifikace_check CHECK (specifikace IS NULL OR specifikace IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'objekt_specifikace')));
ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_druh_check CHECK (druh IS NULL OR druh IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'predmet_druh')));
ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_specifikace_check CHECK (specifikace IS NULL OR specifikace IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'predmet_specifikace')));
ALTER TABLE organizace ADD CONSTRAINT organizace_typ_organizace_check CHECK (typ_organizace IS NULL OR typ_organizace IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'organizace_typ')));
ALTER TABLE organizace ADD CONSTRAINT organizace_zverejneni_pristupnost_check CHECK (zverejneni_pristupnost IS NULL OR zverejneni_pristupnost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pristupnost')));
ALTER TABLE pian ADD CONSTRAINT pian_presnost_check CHECK (presnost IS NULL OR presnost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pian_presnost')));
ALTER TABLE pian ADD CONSTRAINT pian_typ_check CHECK (typ IS NULL OR typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pian_typ')));
ALTER TABLE projekt ADD CONSTRAINT projekt_typ_projektu_check CHECK (typ_projektu IS NULL OR typ_projektu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'projekt_typ')));
ALTER TABLE projekt ADD CONSTRAINT projekt_kulturni_pamatka_check CHECK (kulturni_pamatka IS NULL OR kulturni_pamatka IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pamatkova_ochrana')));
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_okolnosti_check CHECK (okolnosti IS NULL OR okolnosti IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'nalezove_okolnosti')));
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_pristupnost_check CHECK (pristupnost IS NULL OR pristupnost IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'pristupnost')));
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_obdobi_check CHECK (obdobi IS NULL OR obdobi IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'obdobi')));
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_druh_nalezu_check CHECK (druh_nalezu IS NULL OR druh_nalezu IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'predmet_druh')));
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_specifikace_check CHECK (specifikace IS NULL OR specifikace IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'predmet_specifikace')));
ALTER TABLE tvar ADD CONSTRAINT tvar_tvar_check CHECK (tvar IS NULL OR tvar IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'letfoto_tvar')));
ALTER TABLE vyskovy_bod ADD CONSTRAINT vyskovy_bod_typ_check CHECK (typ IS NULL OR typ IN (SELECT id FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'vyskovy_bod_typ')));

-- Migrace akce.organizace_ostatni
UPDATE akce_vedouci SET organizace = (SELECT id FROM organizace WHERE organizace.nazev_zkraceny = (SELECT organizace_ostatni FROM akce WHERE akce.id = akce_vedouci.akce))
WHERE akce IN (SELECT id FROM akce WHERE akce.organizace_ostatni IN (SELECT nazev_zkraceny FROM organizace))
AND akce IN (SELECT akce FROM (SELECT akce, count(id) as cnt FROM akce_vedouci GROUP BY akce) pom WHERE pom.cnt = 1);
UPDATE akce_vedouci SET organizace = (SELECT organizace FROM akce WHERE akce.id = akce_vedouci.akce)
WHERE akce IN (SELECT id FROM akce WHERE (akce.organizace_ostatni IS NULL OR akce.organizace_ostatni = ''));

-- Oprava typů polí v návaznosti na #385 a #384 (aby nebyla moc velká v administraci)
ALTER TABLE heslar ALTER COLUMN heslo TYPE varchar(255);
ALTER TABLE heslar ALTER COLUMN heslo_en TYPE varchar(255);
ALTER TABLE heslar ALTER COLUMN zkratka TYPE varchar(100);
ALTER TABLE heslar ALTER COLUMN zkratka_en TYPE varchar(100);
ALTER TABLE heslar_odkaz ALTER COLUMN zdroj TYPE varchar(255);
ALTER TABLE heslar_odkaz ALTER COLUMN nazev_kodu TYPE varchar(100);
ALTER TABLE heslar_odkaz ALTER COLUMN kod TYPE varchar(100);
ALTER TABLE organizace ALTER COLUMN nazev TYPE varchar(255);
ALTER TABLE organizace ALTER COLUMN nazev_zkraceny TYPE varchar(255);
ALTER TABLE organizace ALTER COLUMN adresa TYPE varchar(255);
ALTER TABLE organizace ALTER COLUMN nazev_en TYPE varchar(255);
ALTER TABLE organizace ALTER COLUMN nazev_zkraceny_en TYPE varchar(255);
ALTER TABLE organizace ALTER COLUMN email TYPE varchar(100);
ALTER TABLE organizace ALTER COLUMN telefon TYPE varchar(100);
ALTER TABLE organizace ALTER COLUMN ico TYPE varchar(100);
ALTER TABLE osoba ALTER COLUMN jmeno TYPE varchar(100);
ALTER TABLE osoba ALTER COLUMN prijmeni TYPE varchar(100);
ALTER TABLE osoba ALTER COLUMN rodne_prijmeni TYPE varchar(100);
ALTER TABLE osoba ALTER COLUMN vypis TYPE varchar(200);
ALTER TABLE osoba ALTER COLUMN vypis_cely TYPE varchar(200);
ALTER TABLE auth_user ALTER COLUMN telefon TYPE varchar(100);

-- Odstranění nepotřebných sekvencí
DROP SEQUENCE akce_id_seq;
DROP SEQUENCE akce_n_is_id_seq;
DROP SEQUENCE atree_id_seq;
DROP SEQUENCE dj_lh_seq;
DROP SEQUENCE docasne_id;
DROP SEQUENCE dokument_cast_vazby_id_seq;
DROP SEQUENCE dokumentacni_jednotka_vazby_id_seq;
DROP SEQUENCE externi_odkaz_vazby_id_seq;
DROP SEQUENCE ft_delayed_id_seq;
DROP SEQUENCE ft_documents_id_seq;
DROP SEQUENCE ft_terms_id_seq;
DROP SEQUENCE heslar_druh_lokality_druha_seq;
DROP SEQUENCE heslar_druh_vyzkumu_id_seq;
DROP SEQUENCE heslar_jmeno_id_seq;
DROP SEQUENCE heslar_kultura_druha_id_seq;
DROP SEQUENCE heslar_kultura_prvni_id_seq;
DROP SEQUENCE heslar_lokalita_druh_druha_id_seq;
DROP SEQUENCE heslar_lokalita_druh_id_seq;
DROP SEQUENCE heslar_lokalita_typ_druha_id_seq;
DROP SEQUENCE heslar_material_id_seq;
DROP SEQUENCE heslar_nalez_druha_id_seq;
DROP SEQUENCE heslar_nalez_prvni_id_seq;
DROP SEQUENCE heslar_osoby_id_seq;
DROP SEQUENCE heslar_pristupnost_dokuemnt_id_seq;
DROP SEQUENCE heslar_puvod_pian_id_seq;
DROP SEQUENCE heslar_specifikace_objekt_prvni_id_seq;
DROP SEQUENCE heslar_typ_akce_id_seq;
DROP SEQUENCE heslar_typ_akce_rozsah_do_seq;
DROP SEQUENCE heslar_typ_komponenty_id_seq;
DROP SEQUENCE heslar_ulozeni_nalezu_id_seq;
DROP SEQUENCE historie_akce_seq;
DROP SEQUENCE historie_dokumentu_seq;
DROP SEQUENCE historie_samostatny_nalez_seq;
DROP SEQUENCE historie_spoluprace_seq;
DROP SEQUENCE historie_user_storage_seq;
DROP SEQUENCE katastr_arup_id_seq;
DROP SEQUENCE komponenta_dokument_id_seq;
DROP SEQUENCE literatura_is_id_seq;
DROP SEQUENCE log_id_seq;
DROP SEQUENCE lokalita_id_seq;
DROP SEQUENCE lokalita_is_id_seq;
DROP SEQUENCE lokalita_poradi_seq;
DROP SEQUENCE nalez_dokument_id_seq;
DROP SEQUENCE nalez_id_seq;
DROP SEQUENCE nivelacni_bod_id_seq;
DROP SEQUENCE odkaz_id_seq;
DROP SEQUENCE pian_is_id_seq;
DROP SEQUENCE pian_nepotvrzene_seq;
DROP SEQUENCE pian_potvrzene_seq;
DROP SEQUENCE projekt_poradi_2013;
DROP SEQUENCE projekt_poradi_2014;
DROP SEQUENCE projekt_poradi_2015;
DROP SEQUENCE projekt_poradi_2016;
DROP SEQUENCE projekty_is_id_seq;
DROP SEQUENCE soubor_fs_id_seq;
DROP SEQUENCE user_storage_user_id;
DROP SEQUENCE uzivatel_id_seq;
DROP SEQUENCE vyskovy_bod_reorder;

