-- prikazy kterymi lze zmigrovat uzivatele do nativni django autentizace, pred volanim techto prikazu je potreba udelat migraci tabulek djanga "python manage.py migrate"

-- modifikace stavajici tabulky auth_user
alter table auth_user add column osoba integer;
alter table auth_user add column auth_level integer; -- COMMENT: tohle az budou permissions definovane a rozdelene se muze smazat
alter table auth_user add column organizace integer;
alter table auth_user add column historie integer;
alter table auth_user add column email_potvrzen text;
alter table auth_user add column notifikace_nalezu boolean default true;
alter table auth_user add column jazyk character varying(15);
alter table auth_user add column sha_1 text;

-- vloazeni dat TODO: date_joined je v historii a heslo je potreba zabalit do jine heshovaci funkce COMMENT: uzivatele budou mit nova id-cka
insert into auth_user(password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, auth_level, email_potvrzen, notifikace_nalezu, jazyk, historie, sha_1, osoba) select heslo, false, ident_cely, jmeno, prijmeni, email, false, true, NOW(), auth_level, email_potvrzen, notifikace_nalezu, jazyk, historie, heslo, osoba from uzivatel;

-- prirazeni skupiny na zaklade role
-- 1 = Badatel, 2 = Archeolog, 3 = Archivar COMMNET: muze byt jinak
insert into auth_group(id, name) values (1, 'Badatel'), (2, 'Archeolog'), (3, 'Archivář'),(4, 'Administrátor');

-- vlozim si aut_level do auth_user tabulky
update auth_user set auth_level = sel.lev from (select u.auth_level as lev, u.ident_cely as ident from uzivatel u join auth_user au on au.username = u.ident_cely) as sel where sel.ident = username;

insert into auth_user_groups (user_id, group_id) select id, 1 from auth_user where (auth_level & 1) = 1;
insert into auth_user_groups (user_id, group_id) select id, 2 from auth_user where (auth_level & 2) = 2;
insert into auth_user_groups (user_id, group_id) select id, 4 from auth_user where (auth_level & 4) = 4;
insert into auth_user_groups (user_id, group_id) select id, 3 from auth_user where (auth_level & 16) = 16;
-- Zbytek uzivatelu kteri maji auth_level 0 nebo nic je potreba nastavit na neaktivnich cca 250 uzivatelu
update auth_user set is_active = false where auth_level & 1 != 1 and auth_level & 2 != 2 and auth_level & 4 != 4 and auth_level & 16 != 16;

-- TODO: adminum t.j. tem ktery maji mit pravo se prihlasit do admin rozhrani dat staff a pripadit je taky do skupiny ktera administruje vybrane tabulky

-- drop foreign keys na uzivatele a vytvorit je na auth_user
--1.uzivatel_spoluprace.spolupracovnik
alter table uzivatel_spoluprace drop constraint vazba_spoluprace_archeolog_fkey;
--2.uzivatel_spoluprace.vedouci
alter table uzivatel_spoluprace drop constraint vazba_spoluprace_badatel_fkey;
--3.historie.uzivatel
alter table historie drop constraint historie_uzivatel_fkey;
--4.stats_login.uzivatel
alter table stats_login drop constraint stats_login_user_id_fkey;
--5.soubor.vlastnik
alter table soubor drop constraint soubor_vlastnik_fkey;
--6.uzivatel_notifikace_projekty.uzivatel
alter table uzivatel_notifikace_projekty drop constraint user_notify_user_id_fkey;

-- migrace referenci na uzivatele na nove IDcka
update uzivatel_spoluprace set vedouci = sel.ved from (select au.id as ved, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where  vedouci = sel.userid;
update uzivatel_spoluprace set spolupracovnik = sel.ved from (select au.id as ved, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where  spolupracovnik = sel.userid;
update historie set uzivatel = sel.uzi from (select au.id as uzi, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where uzivatel = sel.userid;
update stats_login set uzivatel = sel.uzi from (select au.id as uzi, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where uzivatel = sel.userid;
update soubor set vlastnik = sel.uzi from (select au.id as uzi, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where vlastnik = sel.userid;
update uzivatel_notifikace_projekty set uzivatel = sel.uzi from (select au.id as uzi, u.id as userid from auth_user au join uzivatel u on u.ident_cely = au.username) as sel where uzivatel = sel.userid;

-- vytvoreni novych foreign keys
--1.uzivatel_spoluprace.vedouci
alter table uzivatel_spoluprace add constraint uzivatel_spoluprace_vedouci_fkey foreign key(vedouci) references auth_user(id);
--2.uzivatel_spoluprace.spolupracovnik
alter table uzivatel_spoluprace add constraint uzivatel_spoluprace_spolupracovnik_fkey foreign key(spolupracovnik) references auth_user(id);
--3.historie.uzivatel
alter table historie add constraint historie_uzivatel_fkey foreign key(uzivatel) references auth_user(id);
--4.stats_login.uzivatel
alter table stats_login add constraint stats_login_uzivatel_fkey foreign key(uzivatel) references auth_user(id);
--5.soubor.vlastnik
alter table soubor add constraint soubor_vlastnik_fkey foreign key(vlastnik) references auth_user(id);
--6.uzivatel_notifikace_projekty.uzivatel
alter table uzivatel_notifikace_projekty add constraint uzivatel_notifikace_projekty_uzivatel_fkey foreign key(uzivatel) references auth_user(id);

-- migrace organizace
update auth_user set organizace = sel.org from ( select u.organizace as org, u.ident_cely as ident from uzivatel u join auth_user au on au.username = u.ident_cely) as sel where username = sel.ident;
alter table uzivatel drop constraint user_storage_organizace_fkey;
alter table auth_user add constraint auth_user_organizace_fkey foreign key(organizace) references organizace(id);
alter table auth_user alter column organizace set not null;

alter table auth_user add constraint auth_user_historie_fkey foreign key (historie) references historie_vazby(id);
alter table auth_user add constraint auth_user_osoba_fkey foreign key (osoba) references osoba(id);

-- TODO: migrace osob na zaklade jmena a prijmeni

-- TODO Na konec smazani tabulky uzivatel
--drop table uzivatel;
