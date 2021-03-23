-- CASCADE ON DELETE

alter table akce drop constraint akce_archeologicky_zaznam_fkey;
alter table akce_vedouci drop constraint akce_vedouci_akce_fkey;
alter table archeologicky_zaznam_katastr drop constraint archeologicky_zaznam_katastr_archeologicky_zaznam_fkey;
alter table dokument_autor drop constraint dokument_autor_dokument_fk;
alter table dokument_jazyk drop constraint dokument_jazyk_dokument_fk;
alter table dokument_posudek drop constraint dokument_posudek_dokument_fk;
alter table dokumentacni_jednotka drop constraint dokumentacni_jednotka_archeologicky_zaznam_fkey;
alter table externi_odkaz drop constraint externi_odkaz_archeologicky_zaznam_fkey;
alter table externi_zdroj_autor drop constraint externi_zdroj_autor_externi_zdroj_fk;
alter table externi_zdroj_editor drop constraint externi_zdroj_editor_externi_zdroj_fk;
alter table heslar_datace drop constraint heslar_datace_obdobi_fkey;
alter table heslar_datace drop constraint heslar_datace_region_fkey;
alter table heslar_hierarchie drop constraint heslar_hierarchie_heslo_podrazene_fkey;
alter table heslar_odkaz drop constraint heslar_odkaz_heslo_fkey;
alter table historie drop constraint historie_vazba_fkey;
alter table dokument_cast drop constraint jednotka_dokument_dokument_fkey;
alter table komponenta_aktivita drop constraint komponenta_aktivita_komponenta_fk;
alter table komponenta drop constraint komponenta_komponenta_vazby_fkey;
alter table lokalita drop constraint lokalita_archeologicky_zaznam_fkey;
alter table nalez drop constraint nalez_komponenta_fkey;
alter table neident_akce drop constraint neident_akce_dokument_cast_fkey;
alter table neident_akce_vedouci drop constraint neident_akce_vedouci_neident_akce_fk;
alter table projekt_katastr drop constraint projekt_katastr_projekt_fk;
alter table soubor drop constraint soubor_vazba_fkey;
alter table uzivatel_notifikace drop constraint uzivatel_notifikace_notifikace_fkey;
alter table uzivatel_notifikace drop constraint uzivatel_notifikace_uzivatel_fkey;
alter table vyskovy_bod drop constraint vyskovy_bod_adb_fkey;

alter table akce add constraint akce_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete cascade;
alter table akce_vedouci add constraint akce_vedouci_akce_fkey foreign key (akce) references akce(archeologicky_zaznam) on delete cascade;
alter table archeologicky_zaznam_katastr add constraint archeologicky_zaznam_katastr_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete cascade;
alter table dokument_autor add constraint dokument_autor_dokument_fkey foreign key (dokument) references dokument(id) on delete cascade;
alter table dokument_jazyk add constraint dokument_jazyk_dokument_fkey foreign key (dokument) references dokument(id) on delete cascade;
alter table dokument_posudek add constraint dokument_posudek_dokument_fkey foreign key (dokument) references dokument(id) on delete cascade;
alter table dokumentacni_jednotka add constraint dokumentacni_jednotka_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete cascade;
alter table externi_odkaz add constraint externi_odkaz_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete cascade;
alter table externi_zdroj_autor add constraint externi_zdroj_autor_externi_zdroj_fkey foreign key (externi_zdroj) references externi_zdroj(id) on delete cascade;
alter table externi_zdroj_editor add constraint externi_zdroj_editor_externi_zdroj_fkey foreign key (externi_zdroj) references externi_zdroj(id) on delete cascade;
alter table heslar_datace add constraint heslar_datace_obdobi_fkey foreign key (obdobi) references heslar(id) on delete cascade;
alter table heslar_datace add constraint heslar_datace_region_fkey foreign key (region) references heslar(id) on delete cascade;
alter table heslar_hierarchie add constraint heslar_hierarchie_heslo_podrazene_fkey foreign key (heslo_podrazene) references heslar(id) on delete cascade;
alter table heslar_odkaz add constraint heslar_odkaz_heslo_fkey foreign key (heslo) references heslar(id) on delete cascade;
alter table historie add constraint historie_vazba_fkey foreign key (vazba) references historie_vazby(id) on delete cascade;
alter table dokument_cast add constraint dokument_cast_dokument_fkey foreign key (dokument) references dokument(id) on delete cascade;
alter table komponenta_aktivita add constraint komponenta_aktivita_komponenta_fkey foreign key (komponenta) references komponenta(id) on delete cascade;
alter table komponenta add constraint komponenta_komponenta_vazby_fkey foreign key (komponenta_vazby) references komponenta_vazby(id) on delete cascade;
alter table lokalita add constraint lokalita_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete cascade;
alter table nalez add constraint nalez_komponenta_fkey foreign key (komponenta) references komponenta(id) on delete cascade;
alter table neident_akce add constraint neident_akce_dokument_cast_fkey foreign key (dokument_cast) references dokument_cast(id) on delete cascade;
alter table neident_akce_vedouci add constraint neident_akce_vedouci_neident_akce_fkey foreign key (neident_akce) references neident_akce(id) on delete cascade;
alter table projekt_katastr add constraint projekt_katastr_projekt_fkey foreign key (projekt_id) references projekt(id) on delete cascade;
alter table soubor add constraint soubor_vazba_fkey foreign key (vazba) references soubor_vazby(id) on delete cascade;
alter table uzivatel_notifikace add constraint uzivatel_notifikace_notifikace_fkey foreign key (notifikace) references notifikace(id) on delete cascade;
alter table uzivatel_notifikace add constraint uzivatel_notifikace_uzivatel_fkey foreign key (uzivatel) references auth_user(id) on delete cascade;
alter table vyskovy_bod add constraint vyskovy_bod_adb_fkey foreign key (adb) references adb(dokumentacni_jednotka) on delete cascade;

-- SET NULL ON DELETE
alter table dokument_cast drop constraint dokument_cast_archeologicky_zaznam_fkey;
alter table dokument_cast add constraint dokument_cast_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id) on delete set null;

