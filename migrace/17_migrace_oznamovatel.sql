CREATE TABLE oznamovatel (
	id serial PRIMARY KEY,
	email text NOT NULL,
	adresa text NOT NULL,
	odpovedna_osoba text NOT NULL,
	oznamovatel text NOT NULL,
    telefon text NOT NULL
);


ALTER TABLE projekt rename column oznamovatel to oznamovatel_text;
ALTER TABLE projekt add column oznamovatel integer;
ALTER TABLE projekt add constraint oznamovatel_ukey UNIQUE(id, oznamovatel);

-- migrace
-- ERROR 148 nulovych email, adresa, telefon (jen nezachranne projekty?)
-- ERROR 152 nulovych odpovedna_osoba, oznamovatel_text (jen nezachranne projekty?)

-- vygenerovat id pro oznamovatele zachrannych projektu
update projekt set oznamovatel = nextval('oznamovatel_id_seq') where typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136');

insert into oznamovatel (id, email, adresa, odpovedna_osoba, oznamovatel, telefon) select oznamovatel, email, adresa, odpovedna_osoba, oznamovatel_text, telefon from projekt where oznamovatel is not null order by oznamovatel asc;

ALTER TABLE projekt add constraint projekt_oznamovatel_fkey foreign key (oznamovatel) references oznamovatel(id) ON DELETE SET NULL;

-- Check ze kazdy zachranny projekt ma oznamovatele
--ALTER TABLE projekt ADD CONSTRAINT projekt_oznamovatel_check CHECK (not (oznamovatel IS NULL and typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136')));
-- Nezachranny projekt nemuze mit oznamovatele
--ALTER TABLE projekt ADD CONSTRAINT projekt_oznamovatel_null_check CHECK (not ((typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001137') or typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001138')) and oznamovatel IS NOT NULL));

-- Zmena typu sloupce planovane_zahajeni z textu na daterange
alter table projekt rename column planovane_zahajeni to planovane_zahajeni_text;
alter table projekt add column planovane_zahajeni daterange;

-- Pomocne selecty na analyzu sloupce planovane_zahajeni_text
-- select id, planovane_zahajeni_text from projekt where planovane_zahajeni_text like '__.__.____';
-- select id, planovane_zahajeni_text from projekt where planovane_zahajeni_text like '__/__/____';
-- select count(*) from projekt where planovane_zahajeni_text like 'leden ____' or \
--                                   planovane_zahajeni_text like 'únor ____' or \
--									planovane_zahajeni_text like 'březen ____' or  \
--									planovane_zahajeni_text like 'duben ____' or  \
--									planovane_zahajeni_text like 'květen ____' or  \
--									planovane_zahajeni_text like 'červen ____' or  \
--									planovane_zahajeni_text like 'červenec ____' or  \
--									planovane_zahajeni_text like 'srpen ____' or  \
--									planovane_zahajeni_text like 'září ____' or  \
--									planovane_zahajeni_text like 'říjen ____' or  \
--									planovane_zahajeni_text like 'listopad ____' or \
--									planovane_zahajeni_text like 'prosinec ____';--

-- TODO dodelat migraci planovane_zahajeni
