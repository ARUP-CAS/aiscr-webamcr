-- Vytvorit
alter table archeologicky_zaznam rename column stav to stav_stary;
alter table archeologicky_zaznam add column stav smallint;
update archeologicky_zaznam set stav = stav_stary;

update akce set odlozena_nz = true from (select id as aid from archeologicky_zaznam az where az.stav_stary = 5) as sel where sel.aid = archeologicky_zaznam;

update archeologicky_zaznam set stav = 1 where stav_stary = 3 and typ_zaznamu='A';
update archeologicky_zaznam set stav = 1 where stav_stary = 7 and typ_zaznamu='A';
update archeologicky_zaznam set stav = 2 where stav_stary = 6 and typ_zaznamu='A';
update archeologicky_zaznam set stav = 3 where stav_stary = 8 and typ_zaznamu='A';
update archeologicky_zaznam set stav = 3 where stav_stary = 4 and typ_zaznamu='A';
update archeologicky_zaznam set stav = 3  where stav_stary = 5 and typ_zaznamu='A';

alter table archeologicky_zaznam alter column stav set not null;
