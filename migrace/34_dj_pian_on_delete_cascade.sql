alter table dokumentacni_jednotka
drop constraint dokumentacni_jednotka_pian_fkey,
add constraint dokumentacni_jednotka_pian_fkey
   foreign key (pian)
   references pian(id)
   on delete cascade;