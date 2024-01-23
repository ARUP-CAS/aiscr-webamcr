delete from heslar where ident_cely='HES-000869';

ALTER TABLE dokument_autor add column id serial;

create table dokument_sekvence(
	id serial,
	rada VARCHAR(4) not null,
	rok integer not null,
	sekvence integer not null
);

update auth_user set is_superuser = true where email = 'novak@arup.cas.cz';
update auth_user set is_staff = true where email = 'novak@arup.cas.cz';

alter table samostatny_nalez ALTER id SET DEFAULT nextval('samostatny_nalez_seq');
ALTER SEQUENCE samostatny_nalez_seq OWNED BY samostatny_nalez.id;
SELECT setval('samostatny_nalez_seq', (SELECT MAX(id) from samostatny_nalez), TRUE);

alter table uzivatel_spoluprace add column stav smallint;

-- migrace spolupaci do spravneho stavu
update uzivatel_spoluprace set stav = 1 where aktivni = false;
update uzivatel_spoluprace set stav = 2 where aktivni = true;

alter table uzivatel_spoluprace alter column stav set not null;

-- TODO remove aktivni and potvrzeno states
alter table uzivatel_spoluprace drop column aktivni;
alter table uzivatel_spoluprace drop column potvrzeno;
