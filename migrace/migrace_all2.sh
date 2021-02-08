echo "Migrace oznamovatele do dalsi tabulky"
psql -h 127.0.0.1 -p 5432 -U cz_archeologickamapa_api -d prod_zaloha -f 5_migrace_oznamovatel.sql
echo "Migrace Dalsi"
psql -h 127.0.0.1 -p 5432 -U cz_archeologickamapa_api -d prod_zaloha -f 6_migrace_dalsi.sql
