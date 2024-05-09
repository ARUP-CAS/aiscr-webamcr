-- ************ V MIGRACI 1 *************

--Mazani sloupcu:
ALTER TABLE samostatny_nalez drop column typ_nalezu;
ALTER TABLE akce drop column n_id;
ALTER TABLE dokument drop column poradi;
ALTER TABLE dokument drop column rok_vzniku_cj;
ALTER TABLE dokument drop column letter_cj;
ALTER TABLE dokumentacni_jednotka drop column poradi;
ALTER TABLE externi_zdroj drop column poradi;
ALTER TABLE dokument_cast drop column poradi;
ALTER TABLE komponenta drop column parent_poradi;
ALTER TABLE komponenta_dokument drop column parent_poradi;
ALTER TABLE lokalita drop column poradi;
ALTER TABLE lokalita drop column is_id;
ALTER TABLE projekt drop column id_rok;
ALTER TABLE projekt drop column id_poradi;
ALTER TABLE samostatny_nalez drop column poradi;

-- Mazani tabulek a sloupcu
drop table dokument_soubor_fs;
drop table edit_lock;
drop table fulltext;
drop table log;
drop table search_cache;
drop table user_deactivation_times;
drop table vazba_pian_parent;
drop table vazba_projekt_akce;
drop table dokumentacni_bod;
drop table heslar_souradnicovy_system;
drop table nivelacni_bod;
drop table heslar_pismeno_cj;
drop table pian_projekt;

-- ************ V MIGRACI 2 *************

-- CAST MAZANI

--Odstranit sloupce:
-- TODO zkontrolovat ze sloupce jsou migrovane a nebo nejsou potreba
--1. akce vedouci_akce, vedouci_akce_ostatni, dalsi_katastry, katastr, okres, organizace, organizace_ostatni
alter table akce drop column vedouci_akce;
alter table akce drop column vedouci_akce_ostatni;
alter table akce drop column dalsi_katastry;
alter table akce drop column katastr;
alter table akce drop column okres;
alter table akce drop column organizace_ostatni;
--2. dokument autor, jazyk_dokumentu, typ_dokumentu_posudek
alter table dokument drop column autor;
alter table dokument drop column jazyk_dokumentu;
alter table dokument drop column typ_dokumentu_posudek;
--3. dokument_cast.vazba_druha
alter table dokument_cast drop column vazba_druha;
--4. dokumentacni_jednotka.parent
alter table dokumentacni_jednotka drop column parent;
--6. externi_zdroj.autori, sbornik_editor, podnazev, odznaceni
alter table externi_zdroj drop column autori;
alter table externi_zdroj drop column sbornik_editor;
alter table externi_zdroj drop column podnazev;
alter table externi_zdroj drop column oznaceni;
--7. komponenta.parent, vsechny aktivity
alter table komponenta drop column parent;
alter table komponenta drop column aktivita_boj;
alter table komponenta drop column aktivita_deponovani;
alter table komponenta drop column aktivita_intruze;
alter table komponenta drop column aktivita_jina;
alter table komponenta drop column aktivita_komunikace;
alter table komponenta drop column aktivita_kultovni;
alter table komponenta drop column aktivita_pohrebni;
alter table komponenta drop column aktivita_sidlistni;
alter table komponenta drop column aktivita_tezebni;
alter table komponenta drop column aktivita_vyrobni;
--8. lokalita.okres, katastr, dalsi_katastry, puvodni_stav
alter table lokalita drop column okres;
alter table lokalita drop column katastr;
alter table lokalita drop column dalsi_katastry;
alter table lokalita drop column puvodni_stav;
--10. neident_akce.okres, vedouci
alter table neident_akce drop column okres;
alter table neident_akce drop column vedouci;
--11. pian.organizace, puvodni_cj, cj
alter table pian drop column organizace;
alter table pian drop column puvodni_cj;
alter table pian drop column cj;
--12. projekt.okres, katastr, dalsi_katastry
alter table projekt drop column okres;
alter table projekt drop column katastr;
alter table projekt drop column dalsi_katastry;
--13. soubor.nahled
alter table soubor drop column nahled;
--15. extra_data.northing, easting, pas, osoby, index
alter table dokument_extra_data drop column northing;
alter table dokument_extra_data drop column easting;
alter table dokument_extra_data drop column pas;
alter table dokument_extra_data drop column osoby;
alter table dokument_extra_data drop column index;

-- Tabulky s nespecifickou relaci na Atree
--Odstraneni tabulek:
--1. odkaz
drop table odkaz;
--2. transaction_lock
drop table transaction_lock;
--3. user_group_auth_storage
drop table user_group_auth_storage;
--7. soubor_docasny_projekt (smazat obsah soubor_docasny)
drop table soubor_docasny_projekt;
--9. atree
drop table atree;

-- Migrace + smazani (TODO):
--4. user_password_reset
drop table user_password_reset;
--6. nalez_dokument (zmigrovat do tabulky nalez)
drop table nalez_dokument;
--5. komponenta_dokument (zmigrovat do tabulky komponenta)
drop table komponenta_dokument;
--8. heslar_jmena (migrace dle schema do osob) COMMENT: Tohle se nemaze protoze se tabulka jen prejmenovala.


-- ************ V MIGRACI 3 *************

-- Mazani sloupcu
-- Smazani sloupcu souvisejicich s historii
-- Akce
alter table akce drop column odpovedny_pracovnik_zapisu;
alter table akce drop column odpovedny_pracovnik_autorizace;
alter table akce drop column odpovedny_pracovnik_zamitnuti;
alter table akce drop column odpovedny_pracovnik_archivace;
alter table akce drop column odpovedny_pracovnik_podani_nz;
alter table akce drop column odpovedny_pracovnik_archivace_zaa;
alter table akce drop column odpovedny_pracovnik_vraceni_zaa;
alter table akce drop column odpovedny_pracovnik_odlozeni_nz;
alter table akce drop column datum_zapisu;
alter table akce drop column datum_autorizace;
alter table akce drop column datum_zamitnuti;
alter table akce drop column datum_archivace;
alter table akce drop column datum_podani_nz;
alter table akce drop column datum_archivace_zaa;
alter table akce drop column datum_vraceni_zaa;
alter table akce drop column datum_odlozeni_nz;
-- Dokument
alter table dokument drop column odpovedny_pracovnik_vlozeni;
alter table dokument drop column odpovedny_pracovnik_archivace;
alter table dokument drop column datum_vlozeni;
alter table dokument drop column datum_archivace;
-- Externi_zdroj
alter table externi_zdroj drop column odpovedny_pracovnik_vlozeni;
alter table externi_zdroj drop column datum_vlozeni;
-- Lokalita
alter table lokalita drop column odpovedny_pracovnik_zapisu;
alter table lokalita drop column odpovedny_pracovnik_archivace;
alter table lokalita drop column datum_zapisu;
alter table lokalita drop column datum_archivace;
-- Pian
alter table pian drop column vymezil;
alter table pian drop column potvrdil;
alter table pian drop column datum_vymezeni;
alter table pian drop column datum_potvrzeni;
-- Projekt
alter table projekt drop column odpovedny_pracovnik_zapisu;
alter table projekt drop column odpovedny_pracovnik_prihlaseni;
alter table projekt drop column odpovedny_pracovnik_archivace;
alter table projekt drop column odpovedny_pracovnik_navrhu_zruseni;
alter table projekt drop column odpovedny_pracovnik_zruseni;
alter table projekt drop column odpovedny_pracovnik_navrhu_archivace;
alter table projekt drop column odpovedny_pracovnik_zahajeni;
alter table projekt drop column odpovedny_pracovnik_ukonceni;
alter table projekt drop column datum_zapisu;
alter table projekt drop column datum_prihlaseni;
alter table projekt drop column datum_archivace;
alter table projekt drop column datum_navrzeni_zruseni;
alter table projekt drop column datum_zruseni;
alter table projekt drop column datum_navrhu_archivace;
alter table projekt drop column datum_zapisu_zahajeni;
alter table projekt drop column datum_zapisu_ukonceni;
alter table projekt drop column datetime_born;
alter table projekt drop column duvod_navrzeni_zruseni;
-- Organizace
alter table organizace drop column zkratka;
-- Uzivatel
alter table uzivatel drop column news;

-- uzivatel.jmeno, prijmeni (migrace do sloupce uzivatel.osoba na zaklade jmena a prijmeni)
-- TODO: smazat az bude vyplnen sloupec uzivatel.osoba
-- alter table uzivatel drop column jmeno;
-- alter table uzivatel drop column prijmeni;
-- Mazani dalsich sloupcu bez migrace
-- 142. akce.time_of_change
alter table akce drop column time_of_change;
-- 143. dokumentacni_jednotka.time_of_change
alter table dokumentacni_jednotka drop column time_of_change;
-- 144. lokalita.time_of_change
alter table lokalita drop column time_of_change;
-- 145. projekt.time_of_change
alter table projekt drop column time_of_change;
-- 146. samostatny_nalez.odpovedny_pracovnik_vlozeni, odpovedny_pracovnik_archivace, datum_vlozeni, datum_archivace
alter table samostatny_nalez drop column odpovedny_pracovnik_vlozeni;
alter table samostatny_nalez drop column odpovedny_pracovnik_archivace;
alter table samostatny_nalez drop column datum_vlozeni;
alter table samostatny_nalez drop column datum_archivace;
-- 147. vazba_spoluprace.datum_vytvoreni
alter table uzivatel_spoluprace drop column datum_vytvoreni;
-- 148. ruian_katastr.hranice TOHLE JE CHYBA HRANICE TAM MAJI BYT
-- alter table ruian_katastr drop column hranice;
-- 149. soubor.dokument
alter table soubor drop column dokument;
-- 150. soubor.projekt
alter table soubor drop column projekt;
-- 160. soubor.samostatny_nalez
alter table soubor drop column samostatny_nalez;
-- 161. komponenta.komponenta_dokument_id PUVODNI ID KOMPONENTY PRED MIGRACI
alter table komponenta drop column komponenta_dokument_id;
-- soubor.filepath
alter table soubor drop column filepath;

-- Mazani tabulek sloucene historie
drop table historie_user_storage;
drop table historie_spoluprace;
drop table historie_akce;
drop table historie_samostatny_nalez;
drop table historie_dokumentu;

-- ************ V MIGRACI 4 *************

-- Drop ID
--1. adb.id
alter table adb drop column id;
--2. neident_akce.id
--alter table neident_akce drop column id;
--3. dokument_extra_data.id
alter table dokument_extra_data drop column id;

-- Odebrat sekvence tabulkam
--1. adb
--2. neident_akce
--drop sequence neident_akce_id_seq; COMMENT: tohle nakonec nedropovat, bude mit svuj id
--3. dokument_extra_data
drop sequence extra_data_id_seq;

-- Mazani sloupcu
-- Mazani tabulek
--1. update_pian
drop table update_pian;
--2. pian_import
drop table pian_import;

-- Smazani vsech heslaru
-- Smazani vsech heslaru
drop table heslar_aktivity;
drop table heslar_areal_druha;
drop table heslar_areal_prvni;
drop table heslar_autorska_role;
drop table heslar_backup;
drop table heslar_dohlednost;
drop table heslar_druh_lokality_druha;
drop table heslar_druh_lokality_prvni;
drop table heslar_format_dokumentu;
drop table heslar_jazyk_dokumentu;
drop table heslar_kulturni_pamatka;
drop table heslar_letiste;
drop table heslar_material_dokumentu;
drop table heslar_nahrada;
drop table heslar_nalezove_okolnosti;
drop table heslar_obdobi_druha;
drop table heslar_obdobi_prvni;
drop table heslar_objekt_druh;
drop table heslar_objekt_kategorie;
drop table heslar_pocasi;
drop table heslar_podnet;
drop table heslar_posudek;
drop table heslar_predmet_druh;
drop table heslar_predmet_kategorie;
drop table heslar_presnost;
drop table heslar_pristupnost;
drop table heslar_pristupnost_akce;
drop table heslar_pristupnost_dokument;
drop table heslar_rada;
drop table heslar_specifikace_data;
drop table heslar_specifikace_objektu_druha;
drop table heslar_specifikace_objektu_prvni;
drop table heslar_specifikace_predmetu;
drop table heslar_tvar;
drop table heslar_typ_akce_druha;
drop table heslar_typ_akce_prvni;
drop table heslar_typ_dj;
drop table heslar_typ_dokumentu;
drop table heslar_typ_externiho_zdroje;
drop table heslar_typ_lokality;
drop table heslar_typ_nalezu;
drop table heslar_typ_organizace;
drop table heslar_typ_pian;
drop table heslar_typ_projektu;
drop table heslar_typ_sondy;
drop table heslar_typ_udalosti;
drop table heslar_typ_vyskovy_bod;
drop table heslar_ulozeni_originalu;
drop table heslar_zachovalost;
drop table heslar_zeme;

-- sekvence heslaru COMMENT: nektere sekvence neexistuji ale tyto errory jsou v pohode
drop sequence heslar_aktivity_id_seq;
drop sequence heslar_areal_druha_id_seq;
drop sequence heslar_areal_prvni_id_seq;
drop sequence heslar_autorska_role_id_seq;
--drop sequence heslar_backup_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_dohlednost_id_seq;
drop sequence heslar_druh_lokality_druha_id_seq;
drop sequence heslar_druh_lokality_prvni_id_seq;
drop sequence heslar_format_dokumentu_id_seq;
drop sequence heslar_jazyk_dokumentu_id_seq;
drop sequence heslar_kulturni_pamatka_id_seq;
drop sequence heslar_letiste_id_seq;
drop sequence heslar_material_dokumentu_id_seq;
drop sequence heslar_nahrada_id_seq;
drop sequence heslar_nalezove_okolnosti_id_seq;
drop sequence heslar_obdobi_druha_id_seq;
drop sequence heslar_obdobi_prvni_id_seq;
--drop sequence heslar_objekt_druh_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
--drop sequence heslar_objekt_kategorie_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_pocasi_id_seq;
drop sequence heslar_podnet_id_seq;
--drop sequence heslar_posudek_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_presnost_id_seq;
drop sequence heslar_pristupnost_akce_id_seq;
drop sequence heslar_pristupnost_dokument_id_seq;
drop sequence heslar_rada_id_seq;
drop sequence heslar_specifikace_data_id_seq;
drop sequence heslar_specifikace_objektu_druha_id_seq;
drop sequence heslar_specifikace_objektu_prvni_id_seq;
drop sequence heslar_specifikace_predmetu_id_seq;
drop sequence heslar_tvar_id_seq;
--drop sequence heslar_typ_akce_druha_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
--drop sequence heslar_typ_akce_prvni_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_typ_dj_id_seq;
drop sequence heslar_typ_dokumentu_id_seq;
drop sequence heslar_typ_externiho_zdroje_id_seq;
drop sequence heslar_typ_lokality_id_seq;
drop sequence heslar_druh_nalezu_id_seq; -- COMMENT: tady se sekvence jmenuje jinak nez tabulka
--drop sequence heslar_typ_organizace_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_typ_pian_id_seq;
drop sequence heslar_typ_projektu_id_seq;
drop sequence heslar_typ_sondy_id_seq;
drop sequence heslar_typ_udalosti_id_seq;
--drop sequence heslar_typ_vyskovy_bod_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
--drop sequence heslar_ulozeni_originalu_id_seq; COMMENT: protze tabulka byla vlastnik tak uz neexistuje
drop sequence heslar_zachovalost_id_seq;
drop sequence heslar_zeme_id_seq;

-- mazani dodatecne
-- tabulky:
--1. mass_storage
drop table mass_storage;

-- Uklid sloupcu
alter table projekt drop column oznamovatel_text;
alter table projekt drop column adresa;
alter table projekt drop column email;
alter table projekt drop column odpovedna_osoba;
alter table projekt drop column telefon;

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
DROP SEQUENCE projekt_oznameni_suffix_id_seq;
DROP SEQUENCE projekt_poradi_2013;
DROP SEQUENCE projekt_poradi_2014;
DROP SEQUENCE projekt_poradi_2015;
DROP SEQUENCE projekt_poradi_2016;
DROP SEQUENCE projekty_is_id_seq;
DROP SEQUENCE soubor_fs_id_seq;
DROP SEQUENCE vyskovy_bod_reorder;

DROP TABLE uzivatel;
DROP SEQUENCE uzivatel_id_seq;
alter sequence user_storage_user_id rename to auth_user_ident_cely_seq;

-- Ladění tabulek kladysm5 a kladyzm
ALTER TABLE kladysm5 drop column id;
ALTER TABLE kladysm5 drop column podil;
ALTER TABLE kladysm5 drop column cislo;

ALTER TABLE kladyzm drop column objectid;
ALTER TABLE kladyzm drop column natoceni;
ALTER TABLE kladyzm drop column shape_leng;
ALTER TABLE kladyzm drop column shape_area;

-- Zkontrolovat a odstranit nepoužitá jména z hesláře.
with pom AS
(
    SELECT os.id FROM osoba os
    LEFT JOIN adb adb1 ON adb1.autor_popisu = os.id
    LEFT JOIN adb adb2 ON adb2.autor_revize = os.id
    LEFT JOIN akce ak ON ak.hlavni_vedouci = os.id
    LEFT JOIN akce_vedouci av ON av.vedouci = os.id
    LEFT JOIN auth_user au ON au.osoba = os.id
    LEFT JOIN dokument_autor da ON da.autor = os.id
    LEFT JOIN dokument_osoba dos ON dos.osoba = os.id
    LEFT JOIN externi_zdroj_autor ea ON ea.autor = os.id
    LEFT JOIN externi_zdroj_editor ee ON ee.editor = os.id
    LEFT JOIN let l ON l.pozorovatel = os.id
    LEFT JOIN neident_akce_vedouci nv ON nv.vedouci = os.id
    LEFT JOIN projekt pr ON pr.vedouci_projektu = os.id
    LEFT JOIN samostatny_nalez sn ON sn.nalezce = os.id
    WHERE
    adb1.dokumentacni_jednotka is null AND
    adb2.dokumentacni_jednotka is null AND
    ak.archeologicky_zaznam is null AND
    av.id is null AND
    au.id is null AND
    da.id is null AND
    dos.id is null AND
    ea.id is null AND
    ee.id is null AND
    l.id is null AND
    nv.id is null AND
    pr.id is null AND
    sn.id is null
)
DELETE FROM osoba USING pom WHERE osoba.id = pom.id;

-- Zkontrolovat a odstranit sirotky z historie
CREATE TABLE pom AS
(
    SELECT h.* FROM historie h
    LEFT JOIN archeologicky_zaznam az ON az.historie = h.vazba
    LEFT JOIN auth_user au ON au.historie = h.vazba
    LEFT JOIN dokument d ON d.historie = h.vazba
    LEFT JOIN externi_zdroj ez ON ez.historie = h.vazba
    LEFT JOIN pian pi ON pi.historie = h.vazba
    LEFT JOIN projekt pr ON pr.historie = h.vazba
    LEFT JOIN samostatny_nalez sn ON sn.historie = h.vazba
    LEFT JOIN soubor so ON so.historie = h.vazba
    LEFT JOIN uzivatel_spoluprace us ON us.historie = h.vazba
    WHERE
    az.id is null AND
    au.id is null AND
    d.id is null AND
    ez.id is null AND
    pi.id is null AND
    pr.id is null AND
    sn.id is null AND
    so.id is null AND
    us.id is null
);
DELETE FROM historie USING pom WHERE historie.id = pom.id;
DELETE FROM historie_vazby USING pom WHERE historie_vazby.id = pom.id;
DROP TABLE pom;

-- Odstranění sysno
ALTER TABLE externi_zdroj DROP COLUMN sysno;
