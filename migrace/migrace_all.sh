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

#echo "Migrace mazani"
#psql -d prod_zaloha -f migrace_mazani.sql

# Migrace tabulek django 3.0
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

#echo "Prehashovani hesel"
#Tohle je potreba zatim zavolat manualne

#Pak jeste volat dalsi migrace
# 5_migrace_oznamovatel.sql
# 6_migrace_dalsi.sql
