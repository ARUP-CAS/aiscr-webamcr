ALTER TABLE komponenta_aktivita add column id serial;

ALTER TABLE komponenta alter obdobi set not null;
ALTER TABLE komponenta alter areal set not null;
ALTER TABLE dokumentacni_jednotka alter komponenty set not null;
alter table adb drop column final_cj;
alter table dokument drop column final_cj;
alter table dokument alter column ident_cely set not null;

update heslar set heslo = zkratka where nazev_heslare = 9;
update heslar set heslo = popis where nazev_heslare=46 or nazev_heslare=13;
update heslar set heslo = popis where nazev_heslare = 24;


ALTER TABLE dokument_osoba add column id serial;

-- Zmena relace z projektu.oznameni na oznameni.projekt
alter table oznamovatel add column projekt integer;
alter table oznamovatel add constraint oznamovatel_projekt_fkey foreign key (projekt) references projekt(id) on delete cascade;
alter table oznamovatel add unique (projekt);

update oznamovatel set projekt = sel.projekt from (select p.id as projekt, o.id as oznamovatel from projekt p join oznamovatel o on p.oznamovatel = o.id) as sel where oznamovatel.id = sel.oznamovatel;

alter table oznamovatel alter column projekt set not null;

alter table projekt drop oznamovatel;

-- Zmena typu sloupce datum_vzniku
alter table dokument_extra_data rename column datum_vzniku to datum_vzniku_ts;
alter table dokument_extra_data add column datum_vzniku date;
update dokument_extra_data set datum_vzniku = date(datum_vzniku_ts);
alter table dokument_extra_data drop column datum_vzniku_ts;

-- Odstraneni sloupce pian.buffer
alter table pian drop column buffer;

alter table auth_user add column telefon text;
update auth_user au set telefon = sel.tel from (select email, telefon as tel from uzivatel) sel where sel.email = au.email;

