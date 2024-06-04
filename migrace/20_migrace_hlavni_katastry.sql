-- Zmena ulozeni hlavniho katastru primo do tabulky projekt
alter table projekt add column hlavni_katastr integer;
alter table projekt add constraint projekt_hlavni_katastr_fkey foreign key (hlavni_katastr) references ruian_katastr(id);
-- Migrace stavajicich hlavnich katastru do spravnych projektu > 125665 katastru je uvedeno jako hlavnich
update projekt set hlavni_katastr = sel.k from (select projekt_id as p, katastr_id as k from projekt_katastr pk where pk.hlavni = true) as sel where sel.p = id;
delete from projekt_katastr where hlavni = true;
alter table projekt_katastr drop column hlavni;
alter table projekt alter column hlavni_katastr set not null;


-- Zmena ulozeni hlavniho katastru u archeologickeho zaznamu
alter table archeologicky_zaznam add column hlavni_katastr integer;
alter table archeologicky_zaznam add constraint archeologicky_zaznam_hlavni_katastr_fkey foreign key (hlavni_katastr) references ruian_katastr(id);
-- > 67 795 zaznamu
update archeologicky_zaznam set hlavni_katastr = sel.k from (select archeologicky_zaznam_id as p, katastr_id as k from archeologicky_zaznam_katastr pk where pk.hlavni = true) as sel where sel.p = id;
delete from archeologicky_zaznam_katastr where hlavni = true;
alter table archeologicky_zaznam_katastr drop column hlavni;

-- Zmena ulozeni vedouciho akce
alter table akce add column hlavni_vedouci integer;
alter table akce add constraint akce_hlavni_vedouci_fkey foreign key (hlavni_vedouci) references osoba(id);
-- > 66 865 zaznamu
update akce set hlavni_vedouci = sel.v from (select akce as a, vedouci as v from akce_vedouci av where av.hlavni = true) as sel where sel.a = archeologicky_zaznam;
delete from akce_vedouci where hlavni = true;
alter table akce_vedouci drop column hlavni;
