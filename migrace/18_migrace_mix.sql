alter table dokument_autor alter column poradi drop not null;

delete from heslar where heslo='administrátor';

ALTER TABLE dokument_autor add column id serial;

create table dokument_sekvence(
	id serial,
	rada VARCHAR(4) not null,
	rok integer not null,
	sekvence integer not null
);

insert into dokument_sekvence (id, rada, rok, sekvence) values
(1, 'C-TX', 2021, 1),
(2, 'M-TX', 2021, 1),
(3, 'C-DD', 2021, 1),
(4, 'M-DD', 2021, 1),
(5, 'C-3D', 2021, 1),
(6, 'C-TX', 2022, 1),
(7, 'M-TX', 2022, 1),
(8, 'C-DD', 2022, 1),
(9, 'M-DD', 2022, 1),
(10, 'C-3D', 2022, 1),
(11, 'C-TX', 2023, 1),
(12, 'M-TX', 2023, 1),
(13, 'C-DD', 2023, 1),
(14, 'M-DD', 2023, 1),
(15, 'C-3D', 2023, 1);
