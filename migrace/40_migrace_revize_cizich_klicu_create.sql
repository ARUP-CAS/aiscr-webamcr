---this issue solve - revize cicic klicu bug id 48, it is not possible to update contraint, it must be deleted and created again.
ALTER TABLE adb ADD CONSTRAINT adb_podnet_fkey FOREIGN KEY (podnet) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE adb ADD CONSTRAINT adb_sm5_fkey FOREIGN KEY (sm5) REFERENCES kladysm5 (gid) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE adb ADD CONSTRAINT adb_typ_sondy_fkey FOREIGN KEY (typ_sondy) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce ADD CONSTRAINT akce_archeologicky_zaznam_fkey FOREIGN KEY (archeologicky_zaznam) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE akce ADD CONSTRAINT akce_hlavni_typ_fkey FOREIGN KEY (hlavni_typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce ADD CONSTRAINT akce_hlavni_vedouci_fkey FOREIGN KEY (hlavni_vedouci) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce ADD CONSTRAINT akce_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce ADD CONSTRAINT akce_specifikace_data_fkey FOREIGN KEY (specifikace_data) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce ADD CONSTRAINT akce_vedlejsi_typ_fkey FOREIGN KEY (vedlejsi_typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_akce_fkey FOREIGN KEY (akce) REFERENCES akce (archeologicky_zaznam) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE akce_vedouci ADD CONSTRAINT akce_vedouci_vedouci_fkey FOREIGN KEY (vedouci) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE adb ADD CONSTRAINT adb_autor_popisu_fkey FOREIGN KEY (autor_popisu) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE adb ADD CONSTRAINT adb_autor_revize_fkey FOREIGN KEY (autor_revize) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE adb ADD CONSTRAINT adb_dokumentacni_jednotka_fkey FOREIGN KEY (dokumentacni_jednotka) REFERENCES dokumentacni_jednotka (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE adb_sekvence ADD CONSTRAINT adb_sekvence_kladysm5_id_fkey FOREIGN KEY (kladysm5_id) REFERENCES kladysm5 (gid) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_hlavni_katastr_fkey FOREIGN KEY (hlavni_katastr) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE archeologicky_zaznam_katastr ADD CONSTRAINT archeologicky_zaznam_katastr_archeologicky_zaznam_id_fkey FOREIGN KEY (archeologicky_zaznam_id) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE archeologicky_zaznam_katastr ADD CONSTRAINT archeologicky_zaznam_katastr_katastr_id_fkey FOREIGN KEY (katastr_id) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE archeologicky_zaznam ADD CONSTRAINT archeologicky_zaznam_pristupnost_fkey FOREIGN KEY (pristupnost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE auth_user_groups ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group (id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE auth_user_groups ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE auth_user ADD CONSTRAINT auth_user_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE auth_user ADD CONSTRAINT auth_user_hlavni_role_fkey FOREIGN KEY (hlavni_role) REFERENCES auth_group (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE auth_user ADD CONSTRAINT auth_user_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE auth_user ADD CONSTRAINT auth_user_osoba_fkey FOREIGN KEY (osoba) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_autor ADD CONSTRAINT dokument_autor_autor_fkey FOREIGN KEY (autor) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
  --
  --
  --
  --
  --
ALTER TABLE dokument_osoba ADD CONSTRAINT dokument_osoba_osoba_fkey FOREIGN KEY (osoba) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
   --
ALTER TABLE dokument_autor ADD CONSTRAINT dokument_autor_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
   --
   --
   --
ALTER TABLE dokument_osoba ADD CONSTRAINT dokument_osoba_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
  --
  --
  --
  --
  --
  --
ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_archeologicky_zaznam_fkey FOREIGN KEY (archeologicky_zaznam) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_komponenty_fkey FOREIGN KEY (komponenty) REFERENCES komponenta_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_format_fkey FOREIGN KEY (format) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_nahrada_fkey FOREIGN KEY (nahrada) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_udalost_typ_fkey FOREIGN KEY (udalost_typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_zachovalost_fkey FOREIGN KEY (zachovalost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_zeme_fkey FOREIGN KEY (zeme) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE dokument_jazyk ADD CONSTRAINT dokument_jazyk_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE dokument_jazyk ADD CONSTRAINT dokument_jazyk_jazyk_fkey FOREIGN KEY (jazyk) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_let_fkey FOREIGN KEY (let) REFERENCES let (id) ON UPDATE CASCADE ON DELETE RESTRICT;
  --
ALTER TABLE dokument ADD CONSTRAINT dokument_material_originalu_fkey FOREIGN KEY (material_originalu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_posudek ADD CONSTRAINT dokument_posudek_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE dokument_posudek ADD CONSTRAINT dokument_posudek_posudek_fkey FOREIGN KEY (posudek) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_pristupnost_fkey FOREIGN KEY (pristupnost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_rada_fkey FOREIGN KEY (rada) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE dokument ADD CONSTRAINT dokument_typ_dokumentu_fkey FOREIGN KEY (typ_dokumentu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument ADD CONSTRAINT dokument_ulozeni_originalu_fkey FOREIGN KEY (ulozeni_originalu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_archeologicky_zaznam_fkey FOREIGN KEY (archeologicky_zaznam) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_komponenty_fkey FOREIGN KEY (komponenty) REFERENCES komponenta_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_pian_fkey FOREIGN KEY (pian) REFERENCES pian (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokumentacni_jednotka ADD CONSTRAINT dokumentacni_jednotka_typ_fkey FOREIGN KEY (typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE externi_odkaz ADD CONSTRAINT externi_odkaz_archeologicky_zaznam_fkey FOREIGN KEY (archeologicky_zaznam) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE externi_odkaz ADD CONSTRAINT externi_odkaz_externi_zdroj_fkey FOREIGN KEY (externi_zdroj) REFERENCES externi_zdroj (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE externi_zdroj_autor ADD CONSTRAINT externi_zdroj_autor_autor_fkey FOREIGN KEY (autor) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE externi_zdroj_autor ADD CONSTRAINT externi_zdroj_autor_externi_zdroj_fkey FOREIGN KEY (externi_zdroj) REFERENCES externi_zdroj (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE externi_zdroj_editor ADD CONSTRAINT externi_zdroj_editor_editor_fkey FOREIGN KEY (editor) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE externi_zdroj_editor ADD CONSTRAINT externi_zdroj_editor_externi_zdroj_fkey FOREIGN KEY (externi_zdroj) REFERENCES externi_zdroj (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_typ_dokumentu_fkey FOREIGN KEY (typ_dokumentu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE externi_zdroj ADD CONSTRAINT externi_zdroj_typ_fkey FOREIGN KEY (typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE dokument_extra_data ADD CONSTRAINT dokument_extra_data_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE heslar_datace ADD CONSTRAINT heslar_datace_obdobi_fkey FOREIGN KEY (obdobi) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE heslar_datace ADD CONSTRAINT heslar_datace_region_fkey FOREIGN KEY (region) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE heslar_dokument_typ_material_rada ADD CONSTRAINT heslar_dokument_typ_material_rada_dokument_material_fkey FOREIGN KEY (dokument_material) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE heslar_dokument_typ_material_rada ADD CONSTRAINT heslar_dokument_typ_material_rada_dokument_rada_fkey FOREIGN KEY (dokument_rada) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE heslar_dokument_typ_material_rada ADD CONSTRAINT heslar_dokument_typ_material_rada_dokument_typ_fkey FOREIGN KEY (dokument_typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_heslo_nadrazene_fkey FOREIGN KEY (heslo_nadrazene) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE heslar_hierarchie ADD CONSTRAINT heslar_hierarchie_heslo_podrazene_fkey FOREIGN KEY (heslo_podrazene) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE heslar ADD CONSTRAINT heslar_nazev_heslare_fkey FOREIGN KEY (nazev_heslare) REFERENCES heslar_nazev (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE heslar_odkaz ADD CONSTRAINT heslar_odkaz_heslo_fkey FOREIGN KEY (heslo) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE historie ADD CONSTRAINT historie_uzivatel_fkey FOREIGN KEY (uzivatel) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE historie ADD CONSTRAINT historie_vazba_fkey FOREIGN KEY (vazba) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_okres_fkey FOREIGN KEY (okres) REFERENCES ruian_okres (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_pian_fkey FOREIGN KEY (pian) REFERENCES pian (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_soucasny_fkey FOREIGN KEY (soucasny) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE komponenta_aktivita ADD CONSTRAINT komponenta_aktivita_aktivita_fkey FOREIGN KEY (aktivita) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE komponenta_aktivita ADD CONSTRAINT komponenta_aktivita_komponenta_fkey FOREIGN KEY (komponenta) REFERENCES komponenta (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE komponenta ADD CONSTRAINT komponenta_areal_fkey FOREIGN KEY (areal) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE komponenta ADD CONSTRAINT komponenta_komponenta_vazby_fkey FOREIGN KEY (vazba) REFERENCES komponenta_vazby (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE komponenta ADD CONSTRAINT komponenta_obdobi_fkey FOREIGN KEY (obdobi) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE let ADD CONSTRAINT let_dohlednost_fkey FOREIGN KEY (dohlednost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE let ADD CONSTRAINT let_letiste_cil_fkey FOREIGN KEY (letiste_cil) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE let ADD CONSTRAINT let_letiste_start_fkey FOREIGN KEY (letiste_start) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE let ADD CONSTRAINT let_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE let ADD CONSTRAINT let_pocasi_fkey FOREIGN KEY (pocasi) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE let ADD CONSTRAINT let_pozorovatel_fkey FOREIGN KEY (pozorovatel) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_archeologicky_zaznam_fkey FOREIGN KEY (archeologicky_zaznam) REFERENCES archeologicky_zaznam (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_druh_fkey FOREIGN KEY (druh) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_jistota_fkey FOREIGN KEY (jistota) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_typ_lokality_fkey FOREIGN KEY (typ_lokality) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE lokalita ADD CONSTRAINT lokalita_zachovalost_fkey FOREIGN KEY (zachovalost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_druh_fkey FOREIGN KEY (druh) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_komponenta_fkey FOREIGN KEY (komponenta) REFERENCES komponenta (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE nalez_predmet ADD CONSTRAINT nalez_predmet_specifikace_fkey FOREIGN KEY (specifikace) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_druh_fkey FOREIGN KEY (druh) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_komponenta_fkey FOREIGN KEY (komponenta) REFERENCES komponenta (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE nalez_objekt ADD CONSTRAINT nalez_objekt_specifikace_fkey FOREIGN KEY (specifikace) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE neident_akce ADD CONSTRAINT neident_akce_dokument_cast_fkey FOREIGN KEY (dokument_cast) REFERENCES dokument_cast (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE neident_akce ADD CONSTRAINT neident_akce_katastr_fkey FOREIGN KEY (katastr) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE neident_akce_vedouci ADD CONSTRAINT neident_akce_vedouci_neident_akce_fkey FOREIGN KEY (neident_akce) REFERENCES neident_akce (dokument_cast) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE neident_akce_vedouci ADD CONSTRAINT neident_akce_vedouci_vedouci_fkey FOREIGN KEY (vedouci) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE notifikace_projekt ADD CONSTRAINT notifikace_projekt_katastr_fkey FOREIGN KEY (katastr) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE notifikace_projekt ADD CONSTRAINT notifikace_projekt_uzivatel_fkey FOREIGN KEY (uzivatel) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE organizace ADD CONSTRAINT organizace_soucast_fkey FOREIGN KEY (soucast) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE organizace ADD CONSTRAINT organizace_typ_organizace_fkey FOREIGN KEY (typ_organizace) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE organizace ADD CONSTRAINT organizace_zverejneni_pristupnost_fkey FOREIGN KEY (zverejneni_pristupnost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE oznamovatel ADD CONSTRAINT oznamovatel_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE pian ADD CONSTRAINT pian_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE pian ADD CONSTRAINT pian_presnost_fkey FOREIGN KEY (presnost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE pian_sekvence ADD CONSTRAINT pian_sekvence_kladyzm_id_fkey FOREIGN KEY (kladyzm_id) REFERENCES kladyzm (gid) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE pian ADD CONSTRAINT pian_typ_fkey FOREIGN KEY (typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE pian ADD CONSTRAINT pian_zm10_fkey FOREIGN KEY (zm10) REFERENCES kladyzm (gid) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE pian ADD CONSTRAINT pian_zm50_fkey FOREIGN KEY (zm50) REFERENCES kladyzm (gid) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE projekt_oznameni_suffix ADD CONSTRAINT projekt_oznameni_suffix_project_id_fkey FOREIGN KEY (project_id) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE projekt ADD CONSTRAINT projekt_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE projekt ADD CONSTRAINT projekt_hlavni_katastr_fkey FOREIGN KEY (hlavni_katastr) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE projekt_katastr ADD CONSTRAINT projekt_katastr_katastr_id_fkey FOREIGN KEY (katastr_id) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE projekt_katastr ADD CONSTRAINT projekt_katastr_projekt_id_fkey FOREIGN KEY (projekt_id) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE projekt ADD CONSTRAINT projekt_kulturni_pamatka_fkey FOREIGN KEY (kulturni_pamatka) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE projekt ADD CONSTRAINT projekt_organizace_fkey FOREIGN KEY (organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE projekt ADD CONSTRAINT projekt_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE projekt ADD CONSTRAINT projekt_typ_projektu_fkey FOREIGN KEY (typ_projektu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE projekt ADD CONSTRAINT projekt_vedouci_projektu_fkey FOREIGN KEY (vedouci_projektu) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE ruian_okres ADD CONSTRAINT ruian_okres_kraj_fkey FOREIGN KEY (kraj) REFERENCES ruian_kraj (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_predano_organizace_fkey FOREIGN KEY (predano_organizace) REFERENCES organizace (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE RESTRICT;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_druh_nalezu_fkey FOREIGN KEY (druh_nalezu) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_katastr_fkey FOREIGN KEY (katastr) REFERENCES ruian_katastr (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_nalezce_fkey FOREIGN KEY (nalezce) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_obdobi_fkey FOREIGN KEY (obdobi) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_okolnosti_fkey FOREIGN KEY (okolnosti) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_pristupnost_fkey FOREIGN KEY (pristupnost) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_soubory_fkey FOREIGN KEY (soubory) REFERENCES soubor_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_specifikace_fkey FOREIGN KEY (specifikace) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE soubor ADD CONSTRAINT soubor_vazba_fkey FOREIGN KEY (vazba) REFERENCES soubor_vazby (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE soubor ADD CONSTRAINT soubor_vlastnik_fkey FOREIGN KEY (vlastnik) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE tvar ADD CONSTRAINT tvar_dokument_fkey FOREIGN KEY (dokument) REFERENCES dokument (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE tvar ADD CONSTRAINT tvar_tvar_fkey FOREIGN KEY (tvar) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE uzivatel ADD CONSTRAINT uzivatel_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE uzivatel_notifikace ADD CONSTRAINT uzivatel_notifikace_notifikace_fkey FOREIGN KEY (notifikace) REFERENCES notifikace (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE uzivatel_notifikace ADD CONSTRAINT uzivatel_notifikace_uzivatel_fkey FOREIGN KEY (uzivatel) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE uzivatel ADD CONSTRAINT uzivatel_osoba_fkey FOREIGN KEY (osoba) REFERENCES osoba (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE uzivatel_spoluprace ADD CONSTRAINT uzivatel_spoluprace_spolupracovnik_fkey FOREIGN KEY (spolupracovnik) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE uzivatel_spoluprace ADD CONSTRAINT uzivatel_spoluprace_vedouci_fkey FOREIGN KEY (vedouci) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE NO ACTION;
ALTER TABLE uzivatel_spoluprace ADD CONSTRAINT uzivatel_spoluprace_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE vyskovy_bod ADD CONSTRAINT vyskovy_bod_typ_fkey FOREIGN KEY (typ) REFERENCES heslar (id) ON UPDATE CASCADE ON DELETE NO ACTION;

ALTER TABLE dokument_cast ADD CONSTRAINT dokument_cast_projekt_fkey FOREIGN KEY (projekt) REFERENCES projekt (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE soubor ADD CONSTRAINT soubor_historie_fkey FOREIGN KEY (historie) REFERENCES historie_vazby (id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE stats_login ADD CONSTRAINT stats_login_uzivatel_fkey FOREIGN KEY (uzivatel) REFERENCES auth_user (id) ON UPDATE CASCADE ON DELETE CASCADE;
