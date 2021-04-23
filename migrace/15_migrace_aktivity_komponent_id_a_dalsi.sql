ALTER TABLE komponenta_aktivita add column id serial;

ALTER TABLE komponenta alter obdobi set not null;
ALTER TABLE komponenta alter areal set not null;
ALTER TABLE dokumentacni_jednotka alter komponenty set not null;
alter table adb drop column final_cj;
alter table dokument drop column final_cj;
alter table dokument alter column ident_cely set not null;

update heslar set heslo = zkratka where nazev_heslare = 9;
update heslar set heslo = popis where nazev_heslare=46 or nazev_heslare=13;


ALTER TABLE dokument_osoba add column id serial;

-- Zmena relace z projektu.oznameni na oznameni.projekt
alter table oznamovatel add column projekt integer;
alter table oznamovatel add constraint oznamovatel_projekt_fkey foreign key (projekt) references projekt(id) on delete cascade;
alter table oznamovatel add unique (projekt);

update oznamovatel set projekt = sel.projekt from (select p.id as projekt, o.id as oznamovatel from projekt p join oznamovatel o on p.oznamovatel = o.id) as sel where oznamovatel.id = sel.oznamovatel;

alter table oznamovatel alter column projekt set not null;

alter table projekt drop oznamovatel;

