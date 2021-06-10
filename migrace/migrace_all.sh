echo "Oprava chyb"
psql -d prod_zaloha -f chyby_dat.sql

echo "Migrace 1"
psql -d prod_zaloha -f migrace_1.sql
echo "Migrace 2"
psql -d prod_zaloha -f migrace_2.sql
echo "Migrace 3"
psql -d prod_zaloha -f migrace_3.sql
echo "Migrace 4"
psql -d prod_zaloha -f migrace_4.sql
echo "Migrace dat 1"
psql -d prod_zaloha -f migrace_dat_1.sql
echo "Migrace dat 2"
psql -d prod_zaloha -f migrace_dat_2.sql
echo "Migrace dat 3"
psql -d prod_zaloha -f migrace_dat_3.sql
echo "Migrace dat 4"
psql -d prod_zaloha -f migrace_dat_4.sql
echo "Migrace dat 5"
psql -d prod_zaloha -f migrace_dat_5.sql
echo "Migrace content types"
psql -d prod_zaloha -f django.sql
echo "Migrace django_users"
psql -d prod_zaloha -f 1_migrace_django_users.sql
echo "Migrace notifikace"
psql -d prod_zaloha -f 2_migrace_notifikace.sql
echo "Migrace archeologicky_zaznam"
psql -d prod_zaloha -f 3_migrace_archeologicky_zaznam.sql
echo "Migrace stavy akci"
psql -d prod_zaloha -f 4_migrace_akce_stavy.sql
echo "Migrace oznamovatele do dalsi tabulky"
psql -d prod_zaloha -f 5_migrace_oznamovatel.sql
echo "Migrace Dalsi-2"
psql -d prod_zaloha -f 6_migrace_dalsi-2.sql
echo "7"
psql -d prod_zaloha -f 7_migrace_hlavni_katastry.sql
echo "8"
psql -d prod_zaloha -f 8_check_constraints.sql
echo "9"
psql -d prod_zaloha -f 9_migrace_heslare_specifikace_data.sql
echo "10"
psql -d prod_zaloha -f 10_prejmenovani_vazeb.sql
echo "11"
psql -d prod_zaloha -f 11_migrace_dokument_many_to_many.sql
echo "12"
psql -d prod_zaloha -f 12_migrace_fk_revision.sql
echo "13"
psql -d prod_zaloha -f 13_migrace_rozdeleni_tabulky_nalez.sql
echo "14"
psql -d prod_zaloha -f 14_migrace_nazvy_heslaru.sql
echo "15"
psql -d prod_zaloha -f 15_migrace_aktivity_komponent_id_a_dalsi.sql
echo "16"
psql -d prod_zaloha -f 16_migrace_ident_adb.sql
echo "17"
psql -d prod_zaloha -f 17_migrace_ident_projekt.sql
echo "18"
psql -d prod_zaloha -f 18_migrace_mix.sql

echo "!!!Zbyva prehashovani hesel je potreba udelat manualne!!!"

#echo "Migrace mazani" TOHLE ZAVOLAT MANULANE
#psql -d prod_zaloha -f migrace_mazani.sql

#echo "This is only for development, comment out for production"
#psql -d prod_zaloha -f import_testovacich_uctu.sql
