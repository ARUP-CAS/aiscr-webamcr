CREATE TABLE nalez_objekt(
    id serial,
    komponenta integer not null,
    druh integer not null,
    specifikace integer,
    pocet text,
    poznamka text
);

CREATE TABLE nalez_predmet(
    id serial,
    komponenta integer not null,
    druh integer not null,
    specifikace integer,
    pocet text,
    poznamka text
);

insert into nalez_objekt(komponenta, druh, specifikace, pocet, poznamka) select n.komponenta, n.druh_nalezu, n.specifikace, n.pocet, n.poznamka from nalez n join heslar h on h.id = n.druh_nalezu where h.nazev_heslare = 17; -- objekt druh

insert into nalez_predmet(komponenta, druh, specifikace, pocet, poznamka) select n.komponenta, n.druh_nalezu, n.specifikace, n.pocet, n.poznamka from nalez n join heslar h on h.id = n.druh_nalezu where h.nazev_heslare = 22; -- predmet druh

alter table nalez_objekt add constraint nalez_objekt_komponenta_fkey foreign key (komponenta) references komponenta(id) on delete cascade;
alter table nalez_predmet add constraint nalez_predmet_komponenta_fkey foreign key (komponenta) references komponenta(id) on delete cascade;

--Add foreign keys to heslare

alter table nalez_objekt add constraint nalez_objekt_druh_fkey foreign key (druh) references heslar(id);
alter table nalez_objekt add constraint nalez_objekt_specifikace_fkey foreign key (specifikace) references heslar(id);

alter table nalez_predmet add constraint nalez_predmet_druh_fkey foreign key (druh) references heslar(id);
alter table nalez_predmet add constraint nalez_predmet_specifikace_fkey foreign key (specifikace) references heslar(id);

-- Erase old tables
drop table nalez;
drop table soubor_docasny;
