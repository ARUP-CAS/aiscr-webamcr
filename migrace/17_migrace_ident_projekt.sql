create table projekt_sekvence(
	id serial,
	rada CHAR(1) not null,
	rok integer not null,
	sekvence integer not null,
);

insert into projekt_sekvence (id, rada, rok, sekvence) values 
(1, 'C', 2021, 1),
(2, 'C', 2022, 1),
(3, 'C', 2023, 1),
(4, 'C', 2024, 1),
(5, 'C', 2025, 1),
(6, 'M', 2021, 1),
(7, 'M', 2022, 1),
(8, 'M', 2023, 1),
(9, 'M', 2024, 1),
(10, 'M', 2025, 1);

