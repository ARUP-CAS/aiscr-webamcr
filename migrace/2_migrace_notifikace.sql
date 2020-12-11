-- Vytvoreni strukuty tabulek pro notifikace
-- Tabulka by mela typovie obsahovat skupiny notifikaci ktere si uzivatel muze zapnout nebo vypnout
CREATE TABLE public.notifikace (
    id integer primary key,
    nazev text unique not null
);

ALTER TABLE notifikace add column popis text not null;

CREATE TABLE public.uzivatel_notifikace (
    uzivatel integer not null,
    notifikace integer not null
);

ALTER TABLE uzivatel_notifikace add constraint uzivatel_notifikace_key UNIQUE (uzivatel, notifikace);
ALTER TABLE uzivatel_notifikace add constraint uzivatel_notifikace_uzivatel_fkey FOREIGN KEY (uzivatel) references auth_user(id);
ALTER TABLE uzivatel_notifikace add constraint uzivatel_notifikace_notifikace_fkey FOREIGN KEY (notifikace) references notifikace(id);

CREATE TABLE public.notifikace_projekt (
    uzivatel integer not null,
    katastr integer not null
);

ALTER TABLE notifikace_projekt add constraint notifikace_projekt_key UNIQUE (uzivatel, katastr);
ALTER TABLE notifikace_projekt add constraint notifikace_projekt_uzivatel_fkey FOREIGN KEY (uzivatel) references auth_user(id);
ALTER TABLE notifikace_projekt add constraint notifikace_projekt_katastr_fkey FOREIGN KEY (katastr) references ruian_katastr(id);

insert into notifikace(id, nazev, popis) values
(1, 'SN1', 'popis emailu'),
(2, 'SN2', 'popis emailu'),
(3, 'SN3', 'popis emailu'),
(4, 'SN4', 'popis emailu'),
(5, 'SN5', 'popis emailu'),
(6, 'SN6', 'popis emailu'),
(7, 'SN7', 'popis emailu'),
(8, '3D1', 'popis emailu'),
(9, '3D2', 'popis emailu'),
(10, '3D3', 'popis emailu'),
(11, '3D4', 'popis emailu'),
(12, 'PN', 'popis emailu');

--- CAST MIGRACE
-- Migrace tabulky uzivatel_notifikace_projekty COMMENT: > 127 000 zaznamu

insert into notifikace_projekt (uzivatel, katastr) select u.uzivatel, rk.id as okres from uzivatel_notifikace_projekty as u join ruian_okres as ro on ro.kraj = u.kraj join ruian_katastr as rk on rk.okres = ro.id order by (u.uzivatel, rk.id) asc;

insert into uzivatel_notifikace (uzivatel, notifikace) select distinct uzivatel, 12 from notifikace_projekt;

-- Migrace nastaveni z uzivatelskych uctu
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 1 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 2 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 3 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 4 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 5 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 6 from auth_user where notifikace_nalezu is true;
insert into uzivatel_notifikace (uzivatel, notifikace) select id, 7 from auth_user where notifikace_nalezu is true;

--- CAST MAZANI
alter table auth_user drop column notifikace_nalezu;
drop table uzivatel_notifikace_projekty;
