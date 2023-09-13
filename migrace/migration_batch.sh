#!/bin/bash

if [ -n "$1" ]; then
  echo "Database name is set as ${1}."
else
  echo "Database name has to be set as a first parameter."
fi

if [ -n "$2" ]; then
  echo "Username is set as ${2}."
else
  echo "Username has to be set as a second parameter."
fi

migration_scripts=("chyby_dat.sql"
"migrace_1.sql"
"migrace_2.sql"
"migrace_3.sql"
"migrace_4.sql"
"migrace_dat_1.sql"
"migrace_dat_2.sql"
"migrace_dat_3.sql"
"migrace_dat_4.sql"
"migrace_dat_5.sql"
"django.sql"
"1_migrace_django_users.sql"
"2_migrace_notifikace.sql"
"3_migrace_archeologicky_zaznam.sql"
"4_migrace_akce_stavy.sql"
"5_migrace_oznamovatel.sql"
"6a_migrace_dalsi.sql"
"6c_migrace_dalsi.sql"
"7_migrace_hlavni_katastry.sql"
"9_migrace_heslare_specifikace_data.sql"
"11_migrace_dokument_many_to_many.sql"
"13_migrace_rozdeleni_tabulky_nalez.sql"
"14_migrace_nazvy_heslaru.sql"
"15_migrace_aktivity_komponent_id_a_dalsi.sql"
"16_migrace_ident_adb.sql"
"17_migrace_ident_projekt.sql"
"18_migrace_mix.sql"
"19_migrace.sql"
"20_migrace.sql"
"21_rules.sql"
"22_dokumenty_projekt.sql"
"24_soubor_vazba.sql"
"25_komponenta_null_fields.sql"
"26_ostatni_vedouci_id.sql"
"27_adb_ident_update.sql"
"27_validation_linie.sql"
"27_vychozi_aktivity_podle_arealu.sql"
"28_validation_geometry.sql"
"29_sjtsk_geometrie.sql"
"30_geometry_migration_timestamp.sql"
"33_komponenta_boolean.sql"
"33_typ_souboru.sql"
"35_vyskovy_bod_geom.sql"
"36_migrace-sam_nalez.sql"
"37_odstavka_systemu.sql"
"38_migrace_lokalita.sql"
"39_migrace_revize_cizich_klicu_delete.sql"
"40_migrace_revize_cizich_klicu_create.sql"
"41_rosetta_role.sql"
"41_watchdog.sql"
"42_user_is_staff.sql"
"44_katastry.sql"
"44_DN_ruzne_opravy.sql"
"44c_DN_ruzne_opravy.sql"
"44_migrace_revize_db.sql"
"44_notifications.sql"
"46_role_odstavka.sql"
"47_akce_typ.sql"
"48_dokumenty_opravy.sql"
"48_sekvence_user_groups.sql"
"49_rename_pian_column.sql"
"50_hlavni_role.sql"
"51_ext_zdroje_typ_razeni.sql"
"52_lokalita_typ_druh.sql"
"54_rename_and_update_notifications.sql"
"54_soubor_size.sql"
"55_vymena_sablony_notifikace.sql"
"57_migrace_oprava_pes.sql"
"98_heat_mapa.sql"
"99_migrace_notifikace_nove.sql"
"99_set_DB_privileges.sql"
"999_prevod_null_hodnot_texty"
"migrace_mazani.sql"
)



mkdir -p ./logs
n=1

for item in "${migration_scripts[@]}"
do
    echo "run [${n}] - migration with: ${item}"
    psql -d $1 -U $2 -f ${item} -L logs/${item}.log
    let n++
done

echo "*** MIGRATIONS DONE [${n}] ***"

# hashovani hesel
python3 encrypt_passwords.py

#echo "This is only for development, comment out for production"
#psql -d prod_zaloha -f import_testovacich_uctu.sql
