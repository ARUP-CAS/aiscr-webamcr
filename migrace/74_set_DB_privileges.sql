-- Odebrání všech oprávnění pro cz_archeologickamapa_api a cz_archeologickamapa_api_view
REVOKE ALL ON adb FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON adb_sekvence FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON akce FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON akce_vedouci FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON archeologicky_zaznam FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON archeologicky_zaznam_katastr FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON auth_group FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON auth_user FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON auth_user_groups FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON auth_user_notifikace_typ FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_autor FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_cast FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_extra_data FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_jazyk FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_osoba FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_posudek FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokument_sekvence FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON dokumentacni_jednotka FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON externi_odkaz FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON externi_zdroj FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON externi_zdroj_autor FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON externi_zdroj_editor FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar_datace FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar_dokument_typ_material_rada FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar_hierarchie FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar_nazev FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON heslar_odkaz FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON historie FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON historie_vazby FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON kladysm5 FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON kladyzm FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON komponenta FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON komponenta_aktivita FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON komponenta_vazby FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON let FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON lokalita FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON nalez_objekt FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON nalez_predmet FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON neident_akce FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON neident_akce_vedouci FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON notifikace_projekty_pes FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON notifikace_typ FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON odstavky_systemu  FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON organizace FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON osoba FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON oznamovatel FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON pian FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON pian_sekvence FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON projekt FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON projekt_katastr FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON projekt_sekvence FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON ruian_katastr FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON ruian_kraj FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON ruian_okres FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON samostatny_nalez FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON soubor FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON soubor_vazby FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON tvar FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON uzivatel_spoluprace FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;
REVOKE ALL ON vyskovy_bod FROM cz_archeologickamapa_api, cz_archeologickamapa_api_view;

-- Přidělení SELECT oprávnění pro cz_archeologickamapa_api_view
GRANT SELECT ON adb TO cz_archeologickamapa_api_view;
GRANT SELECT ON adb_sekvence TO cz_archeologickamapa_api_view;
GRANT SELECT ON akce TO cz_archeologickamapa_api_view;
GRANT SELECT ON akce_vedouci TO cz_archeologickamapa_api_view;
GRANT SELECT ON archeologicky_zaznam TO cz_archeologickamapa_api_view;
GRANT SELECT ON archeologicky_zaznam_katastr TO cz_archeologickamapa_api_view;
GRANT SELECT ON auth_group TO cz_archeologickamapa_api_view;
GRANT SELECT ON auth_user TO cz_archeologickamapa_api_view;
GRANT SELECT ON auth_user_groups TO cz_archeologickamapa_api_view;
GRANT SELECT ON auth_user_notifikace_typ TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_autor TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_cast TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_extra_data TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_jazyk TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_osoba TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_posudek TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokument_sekvence TO cz_archeologickamapa_api_view;
GRANT SELECT ON dokumentacni_jednotka TO cz_archeologickamapa_api_view;
GRANT SELECT ON externi_odkaz TO cz_archeologickamapa_api_view;
GRANT SELECT ON externi_zdroj TO cz_archeologickamapa_api_view;
GRANT SELECT ON externi_zdroj_autor TO cz_archeologickamapa_api_view;
GRANT SELECT ON externi_zdroj_editor TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar_datace TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar_dokument_typ_material_rada TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar_hierarchie TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar_nazev TO cz_archeologickamapa_api_view;
GRANT SELECT ON heslar_odkaz TO cz_archeologickamapa_api_view;
GRANT SELECT ON historie TO cz_archeologickamapa_api_view;
GRANT SELECT ON historie_vazby TO cz_archeologickamapa_api_view;
GRANT SELECT ON kladysm5 TO cz_archeologickamapa_api_view;
GRANT SELECT ON kladyzm TO cz_archeologickamapa_api_view;
GRANT SELECT ON komponenta TO cz_archeologickamapa_api_view;
GRANT SELECT ON komponenta_aktivita TO cz_archeologickamapa_api_view;
GRANT SELECT ON komponenta_vazby TO cz_archeologickamapa_api_view;
GRANT SELECT ON let TO cz_archeologickamapa_api_view;
GRANT SELECT ON lokalita TO cz_archeologickamapa_api_view;
GRANT SELECT ON nalez_objekt TO cz_archeologickamapa_api_view;
GRANT SELECT ON nalez_predmet TO cz_archeologickamapa_api_view;
GRANT SELECT ON neident_akce TO cz_archeologickamapa_api_view;
GRANT SELECT ON neident_akce_vedouci TO cz_archeologickamapa_api_view;
GRANT SELECT ON notifikace_projekty_pes TO cz_archeologickamapa_api_view;
GRANT SELECT ON notifikace_typ TO cz_archeologickamapa_api_view;
GRANT SELECT ON odstavky_systemu  TO cz_archeologickamapa_api_view;
GRANT SELECT ON organizace TO cz_archeologickamapa_api_view;
GRANT SELECT ON osoba TO cz_archeologickamapa_api_view;
GRANT SELECT ON oznamovatel TO cz_archeologickamapa_api_view;
GRANT SELECT ON pian TO cz_archeologickamapa_api_view;
GRANT SELECT ON pian_sekvence TO cz_archeologickamapa_api_view;
GRANT SELECT ON projekt TO cz_archeologickamapa_api_view;
GRANT SELECT ON projekt_katastr TO cz_archeologickamapa_api_view;
GRANT SELECT ON projekt_sekvence TO cz_archeologickamapa_api_view;
GRANT SELECT ON ruian_katastr TO cz_archeologickamapa_api_view;
GRANT SELECT ON ruian_kraj TO cz_archeologickamapa_api_view;
GRANT SELECT ON ruian_okres TO cz_archeologickamapa_api_view;
GRANT SELECT ON samostatny_nalez TO cz_archeologickamapa_api_view;
GRANT SELECT ON soubor TO cz_archeologickamapa_api_view;
GRANT SELECT ON soubor_vazby TO cz_archeologickamapa_api_view;
GRANT SELECT ON tvar TO cz_archeologickamapa_api_view;
GRANT SELECT ON uzivatel_spoluprace TO cz_archeologickamapa_api_view;
GRANT SELECT ON vyskovy_bod TO cz_archeologickamapa_api_view;

-- Přidělení všech oprávnění pro cz_archeologickamapa_api
GRANT ALL ON adb TO cz_archeologickamapa_api;
GRANT ALL ON adb_sekvence TO cz_archeologickamapa_api;
GRANT ALL ON akce TO cz_archeologickamapa_api;
GRANT ALL ON akce_vedouci TO cz_archeologickamapa_api;
GRANT ALL ON archeologicky_zaznam TO cz_archeologickamapa_api;
GRANT ALL ON archeologicky_zaznam_katastr TO cz_archeologickamapa_api;
GRANT ALL ON auth_group TO cz_archeologickamapa_api;
GRANT ALL ON auth_user TO cz_archeologickamapa_api;
GRANT ALL ON auth_user_groups TO cz_archeologickamapa_api;
GRANT ALL ON auth_user_notifikace_typ TO cz_archeologickamapa_api;
GRANT ALL ON dokument TO cz_archeologickamapa_api;
GRANT ALL ON dokument_autor TO cz_archeologickamapa_api;
GRANT ALL ON dokument_cast TO cz_archeologickamapa_api;
GRANT ALL ON dokument_extra_data TO cz_archeologickamapa_api;
GRANT ALL ON dokument_jazyk TO cz_archeologickamapa_api;
GRANT ALL ON dokument_osoba TO cz_archeologickamapa_api;
GRANT ALL ON dokument_posudek TO cz_archeologickamapa_api;
GRANT ALL ON dokument_sekvence TO cz_archeologickamapa_api;
GRANT ALL ON dokumentacni_jednotka TO cz_archeologickamapa_api;
GRANT ALL ON externi_odkaz TO cz_archeologickamapa_api;
GRANT ALL ON externi_zdroj TO cz_archeologickamapa_api;
GRANT ALL ON externi_zdroj_autor TO cz_archeologickamapa_api;
GRANT ALL ON externi_zdroj_editor TO cz_archeologickamapa_api;
GRANT ALL ON heslar TO cz_archeologickamapa_api;
GRANT ALL ON heslar_datace TO cz_archeologickamapa_api;
GRANT ALL ON heslar_dokument_typ_material_rada TO cz_archeologickamapa_api;
GRANT ALL ON heslar_hierarchie TO cz_archeologickamapa_api;
GRANT ALL ON heslar_nazev TO cz_archeologickamapa_api;
GRANT ALL ON heslar_odkaz TO cz_archeologickamapa_api;
GRANT ALL ON historie TO cz_archeologickamapa_api;
GRANT ALL ON historie_vazby TO cz_archeologickamapa_api;
GRANT ALL ON kladysm5 TO cz_archeologickamapa_api;
GRANT ALL ON kladyzm TO cz_archeologickamapa_api;
GRANT ALL ON komponenta TO cz_archeologickamapa_api;
GRANT ALL ON komponenta_aktivita TO cz_archeologickamapa_api;
GRANT ALL ON komponenta_vazby TO cz_archeologickamapa_api;
GRANT ALL ON let TO cz_archeologickamapa_api;
GRANT ALL ON lokalita TO cz_archeologickamapa_api;
GRANT ALL ON nalez_objekt TO cz_archeologickamapa_api;
GRANT ALL ON nalez_predmet TO cz_archeologickamapa_api;
GRANT ALL ON neident_akce TO cz_archeologickamapa_api;
GRANT ALL ON neident_akce_vedouci TO cz_archeologickamapa_api;
GRANT ALL ON notifikace_projekty_pes TO cz_archeologickamapa_api;
GRANT ALL ON notifikace_typ TO cz_archeologickamapa_api;
GRANT ALL ON odstavky_systemu  TO cz_archeologickamapa_api;
GRANT ALL ON organizace TO cz_archeologickamapa_api;
GRANT ALL ON osoba TO cz_archeologickamapa_api;
GRANT ALL ON oznamovatel TO cz_archeologickamapa_api;
GRANT ALL ON pian TO cz_archeologickamapa_api;
GRANT ALL ON pian_sekvence TO cz_archeologickamapa_api;
GRANT ALL ON projekt TO cz_archeologickamapa_api;
GRANT ALL ON projekt_katastr TO cz_archeologickamapa_api;
GRANT ALL ON projekt_sekvence TO cz_archeologickamapa_api;
GRANT ALL ON ruian_katastr TO cz_archeologickamapa_api;
GRANT ALL ON ruian_kraj TO cz_archeologickamapa_api;
GRANT ALL ON ruian_okres TO cz_archeologickamapa_api;
GRANT ALL ON samostatny_nalez TO cz_archeologickamapa_api;
GRANT ALL ON soubor TO cz_archeologickamapa_api;
GRANT ALL ON soubor_vazby TO cz_archeologickamapa_api;
GRANT ALL ON tvar TO cz_archeologickamapa_api;
GRANT ALL ON uzivatel_spoluprace TO cz_archeologickamapa_api;
GRANT ALL ON vyskovy_bod TO cz_archeologickamapa_api;