---this issue solve - revize cicic klicu bug id 48, it is not possible to update constraint, it must be deleted and created again.

ALTER TABLE adb DROP CONSTRAINT adb_podnet_fkey;
ALTER TABLE adb DROP CONSTRAINT adb_sm5_fkey;
ALTER TABLE adb DROP CONSTRAINT adb_typ_sondy_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_archeologicky_zaznam_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_hlavni_typ_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_hlavni_vedouci_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_projekt_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_specifikace_data_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_vedlejsi_typ_fkey;
ALTER TABLE akce_vedouci DROP CONSTRAINT akce_vedouci_akce_fkey;
ALTER TABLE akce_vedouci DROP CONSTRAINT akce_vedouci_organizace_fkey;
ALTER TABLE akce_vedouci DROP CONSTRAINT akce_vedouci_vedouci_fk;
ALTER TABLE adb DROP CONSTRAINT archeologicky_dokumentacni_bod_autor_popisu_fkey;
ALTER TABLE adb DROP CONSTRAINT archeologicky_dokumentacni_bod_autor_revize_fkey;
ALTER TABLE adb DROP CONSTRAINT archeologicky_dokumentacni_bod_parent_fkey;
ALTER TABLE adb_sekvence DROP CONSTRAINT archeologicky_dokumentacni_bod_sekvence_kladysm5_id_fkey;
ALTER TABLE archeologicky_zaznam DROP CONSTRAINT archeologicky_zaznam_historie_fkey;
ALTER TABLE archeologicky_zaznam DROP CONSTRAINT archeologicky_zaznam_hlavni_katastr_fkey;
ALTER TABLE archeologicky_zaznam_katastr DROP CONSTRAINT archeologicky_zaznam_katastr_archeologicky_zaznam_fkey;
ALTER TABLE archeologicky_zaznam_katastr DROP CONSTRAINT archeologicky_zaznam_katastr_katastr_fkey;
ALTER TABLE archeologicky_zaznam DROP CONSTRAINT archeologicky_zaznam_pristupnost_fkey;
ALTER TABLE auth_user_groups DROP CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id;
ALTER TABLE auth_user_groups DROP CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id;
ALTER TABLE auth_user DROP CONSTRAINT auth_user_historie_fkey;
ALTER TABLE auth_user DROP CONSTRAINT auth_user_hlavni_role;
ALTER TABLE auth_user DROP CONSTRAINT auth_user_organizace_fkey;
ALTER TABLE auth_user DROP CONSTRAINT auth_user_osoba_fkey;
ALTER TABLE dokument_autor DROP CONSTRAINT dokument_autor_autor_fk;
ALTER TABLE dokument_osoba DROP CONSTRAINT dokument_autor_autor_fk;
ALTER TABLE dokument_autor DROP CONSTRAINT dokument_autor_dokument_fk;
ALTER TABLE dokument_osoba DROP CONSTRAINT dokument_autor_dokument_fk;
ALTER TABLE dokument_cast DROP CONSTRAINT dokument_cast_archeologicky_zaznam_fkey;
ALTER TABLE dokument_cast DROP CONSTRAINT dokument_cast_komponenty_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT dokument_extra_data_format_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT dokument_extra_data_nahrada_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT dokument_extra_data_udalost_typ_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT dokument_extra_data_zachovalost_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT dokument_extra_data_zeme_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_historie_fkey;
ALTER TABLE dokument_jazyk DROP CONSTRAINT dokument_jazyk_jazyk_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_let_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_let_fkey1;
ALTER TABLE dokument DROP CONSTRAINT dokument_material_originalu_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_organizace_fkey;
ALTER TABLE dokument_posudek DROP CONSTRAINT dokument_posudek_posudek_fkey;
ALTER TABLE dokument_posudek DROP CONSTRAINT dokument_posudek_dokument_fk;
ALTER TABLE dokument DROP CONSTRAINT dokument_pristupnost_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_rada_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_soubory_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_typ_dokumentu_fkey;
ALTER TABLE dokument DROP CONSTRAINT dokument_ulozeni_originalu_fkey;
ALTER TABLE dokumentacni_jednotka DROP CONSTRAINT dokumentacni_jednotka_archeologicky_zaznam_fkey;
ALTER TABLE dokumentacni_jednotka DROP CONSTRAINT dokumentacni_jednotka_komponenty_fkey;
ALTER TABLE dokumentacni_jednotka DROP CONSTRAINT dokumentacni_jednotka_pian_fkey;
ALTER TABLE dokumentacni_jednotka DROP CONSTRAINT dokumentacni_jednotka_typ_fkey;
ALTER TABLE externi_odkaz DROP CONSTRAINT externi_odkaz_archeologicky_zaznam_fkey;
ALTER TABLE externi_odkaz DROP CONSTRAINT externi_odkaz_externi_zdroj_fkey;
ALTER TABLE externi_zdroj_autor DROP CONSTRAINT externi_zdroj_autor_autor_fk;
ALTER TABLE externi_zdroj_autor DROP CONSTRAINT externi_zdroj_autor_externi_zdroj_fk;
ALTER TABLE externi_zdroj_editor DROP CONSTRAINT externi_zdroj_editor_editor_fk;
ALTER TABLE externi_zdroj_editor DROP CONSTRAINT externi_zdroj_editor_externi_zdroj_fk;
ALTER TABLE externi_zdroj DROP CONSTRAINT externi_zdroj_historie_fkey;
ALTER TABLE externi_zdroj DROP CONSTRAINT externi_zdroj_typ_dokumentu_fkey;
ALTER TABLE externi_zdroj DROP CONSTRAINT externi_zdroj_typ_fkey;
ALTER TABLE dokument_extra_data DROP CONSTRAINT extra_data_dokument_fkey;
ALTER TABLE heslar_datace DROP CONSTRAINT heslar_datace_obdobi_fkey;
ALTER TABLE heslar_datace DROP CONSTRAINT heslar_datace_region_fkey;
ALTER TABLE heslar_dokument_typ_material_rada DROP CONSTRAINT heslar_dokument_typ_material_rada_dokument_material_fkey;
ALTER TABLE heslar_dokument_typ_material_rada DROP CONSTRAINT heslar_dokument_typ_material_rada_dokument_rada_fkey;
ALTER TABLE heslar_dokument_typ_material_rada DROP CONSTRAINT heslar_dokument_typ_material_rada_dokument_typ_fkey;
ALTER TABLE heslar_hierarchie DROP CONSTRAINT heslar_hierarchie_heslo_nadrazene_fkey;
ALTER TABLE heslar_hierarchie DROP CONSTRAINT heslar_hierarchie_heslo_podrazene_fkey;
ALTER TABLE heslar DROP CONSTRAINT heslar_nazev_heslare_fkey;
ALTER TABLE heslar_odkaz DROP CONSTRAINT heslar_odkaz_heslo_fkey;
ALTER TABLE historie DROP CONSTRAINT historie_uzivatel_fkey;
ALTER TABLE historie DROP CONSTRAINT historie_vazba_fkey;
ALTER TABLE dokument_cast DROP CONSTRAINT jednotka_dokument_dokument_fkey;
ALTER TABLE ruian_katastr DROP CONSTRAINT katastr_storage_okres_fkey;
ALTER TABLE ruian_katastr DROP CONSTRAINT katastr_storage_pian_fkey;
ALTER TABLE ruian_katastr DROP CONSTRAINT katastr_storage_soucasny_fkey;
ALTER TABLE komponenta_aktivita DROP CONSTRAINT komponenta_aktivita_aktivita_fkey;
ALTER TABLE komponenta_aktivita DROP CONSTRAINT komponenta_aktivita_komponenta_fk;
ALTER TABLE komponenta DROP CONSTRAINT komponenta_areal_fkey;
ALTER TABLE komponenta DROP CONSTRAINT komponenta_obdobi_fkey;
ALTER TABLE komponenta DROP CONSTRAINT komponenta_vazba_fkey;
ALTER TABLE let DROP CONSTRAINT let_dohlednost_fkey;
ALTER TABLE let DROP CONSTRAINT let_letiste_cil_fkey;
ALTER TABLE let DROP CONSTRAINT let_letiste_start_fkey;
ALTER TABLE let DROP CONSTRAINT let_organizace_fkey;
ALTER TABLE let DROP CONSTRAINT let_pocasi_fkey;
ALTER TABLE let DROP CONSTRAINT let_pozorovatel_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_archeologicky_zaznam_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_druh_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_jistota_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_typ_lokality_fkey;
ALTER TABLE lokalita DROP CONSTRAINT lokalita_zachovalost_fkey;
ALTER TABLE nalez_objekt DROP CONSTRAINT nalez_objekt_druh_fkey;
ALTER TABLE nalez_objekt DROP CONSTRAINT nalez_objekt_komponenta_fkey;
ALTER TABLE nalez_objekt DROP CONSTRAINT nalez_objekt_specifikace_fkey;
ALTER TABLE nalez_predmet DROP CONSTRAINT nalez_predmet_druh_fkey;
ALTER TABLE nalez_predmet DROP CONSTRAINT nalez_predmet_komponenta_fkey;
ALTER TABLE nalez_predmet DROP CONSTRAINT nalez_predmet_specifikace_fkey;
ALTER TABLE neident_akce DROP CONSTRAINT neident_akce_dokument_cast_fkey;
ALTER TABLE neident_akce DROP CONSTRAINT neident_akce_katastr_fkey;
ALTER TABLE neident_akce_vedouci DROP CONSTRAINT neident_akce_vedouci_neident_akce_fk;
ALTER TABLE neident_akce_vedouci DROP CONSTRAINT neident_akce_vedouci_vedouci_fk;
ALTER TABLE notifikace_projekt DROP CONSTRAINT notifikace_projekt_katastr_fkey;
ALTER TABLE notifikace_projekt DROP CONSTRAINT notifikace_projekt_uzivatel_fkey;
ALTER TABLE organizace DROP CONSTRAINT organizace_soucast_fkey;
ALTER TABLE organizace DROP CONSTRAINT organizace_typ_organizace_fkey;
ALTER TABLE organizace DROP CONSTRAINT organizace_zverejneni_pristupnost_fkey;
ALTER TABLE oznamovatel DROP CONSTRAINT oznamovatel_projekt_fkey;
ALTER TABLE pian DROP CONSTRAINT pian_historie_fkey;
ALTER TABLE pian DROP CONSTRAINT pian_presnost_fkey;
ALTER TABLE pian_sekvence DROP CONSTRAINT pian_sekvence_kladyzm_id_fkey;
ALTER TABLE pian DROP CONSTRAINT pian_typ_fkey;
ALTER TABLE pian DROP CONSTRAINT pian_zm10_fkey;
ALTER TABLE pian DROP CONSTRAINT pian_zm50_fkey;
ALTER TABLE projekt_oznameni_suffix DROP CONSTRAINT project_announcement_suffix_project_id_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_historie_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_hlavni_katastr_fkey;
ALTER TABLE projekt_katastr DROP CONSTRAINT projekt_katastr_katastr_fk;
ALTER TABLE projekt_katastr DROP CONSTRAINT projekt_katastr_projekt_fk;
ALTER TABLE projekt DROP CONSTRAINT projekt_kulturni_pamatka_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_organizace_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_soubory_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_typ_projektu_fkey;
ALTER TABLE projekt DROP CONSTRAINT projekt_vedouci_vyzkumu_fkey;
ALTER TABLE ruian_okres DROP CONSTRAINT ruian_okres_kraj_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostany_nalez_organizace_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostany_nalez_projekt_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_druh_nalezu_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_historie_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_katastr_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_nalezce_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_obdobi_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_okolnosti_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_pristupnost_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_soubory_fkey;
ALTER TABLE samostatny_nalez DROP CONSTRAINT samostatny_nalez_specifikace_fkey;
ALTER TABLE soubor DROP CONSTRAINT soubor_vazba_fkey;
ALTER TABLE soubor DROP CONSTRAINT soubor_vlastnik_fkey;
ALTER TABLE tvar DROP CONSTRAINT tvar_dokument_fkey;
ALTER TABLE tvar DROP CONSTRAINT tvar_tvar_fkey;
ALTER TABLE uzivatel DROP CONSTRAINT user_storage_historie_fkey;
ALTER TABLE uzivatel_notifikace DROP CONSTRAINT uzivatel_notifikace_notifikace_fkey;
ALTER TABLE uzivatel_notifikace DROP CONSTRAINT uzivatel_notifikace_uzivatel_fkey;
ALTER TABLE uzivatel DROP CONSTRAINT uzivatel_osoba_fkey;
ALTER TABLE uzivatel_spoluprace DROP CONSTRAINT uzivatel_spoluprace_spolupracovnik_fkey;
ALTER TABLE uzivatel_spoluprace DROP CONSTRAINT uzivatel_spoluprace_vedouci_fkey;
ALTER TABLE uzivatel_spoluprace DROP CONSTRAINT vazba_spoluprace_historie_fkey;
ALTER TABLE vyskovy_bod DROP CONSTRAINT vyskovy_bod_typ_fkey;
ALTER TABLE dokument_cast DROP CONSTRAINT dokument_cast_projekt_fkey;
ALTER TABLE soubor DROP CONSTRAINT soubor_historie_fkey;
ALTER TABLE soubor DROP CONSTRAINT soubor_projekt_fkey;
ALTER TABLE stats_login DROP CONSTRAINT stats_login_uzivatel_fkey;