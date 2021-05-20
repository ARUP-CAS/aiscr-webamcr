#echo "Migrace oznamovatele do dalsi tabulky"
#psql -d prod_zaloha -f 5_migrace_oznamovatel.sql
echo "Migrace Dalsi-2"
psql -d prod_zaloha -f 6_migrace_dalsi-2.sql

echo "7"
psql -d prod_zaloha -f 7_migrace_hlavni_katastry.sql
echo "8"
psql -d prod_zaloha -f 8_check_constraints.sql
echo "9"
psql -d prod_zaloha -f 9_migrace_heslare_specifikace_data.sql

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


#echo "This is only for development, comment out for production"
#psql -d prod_zaloha -f import_testovacich_uctu.sql

