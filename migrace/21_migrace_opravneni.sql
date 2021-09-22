-- vytvoreni tabulky s konkretnimi opravnenimi
alter TABLE opravneni
add CONSTRAINT opravneni_id_key UNIQUE (id);
CREATE TABLE opravneni_konkretni(
    id serial,
    druh_opravneni VARCHAR(10) not null,
    porovnani_stavu VARCHAR(50) null,
    stav integer null,
    vazba_na_konkretni_opravneni integer null,
    parent_opravneni integer NOT NULL,
    CONSTRAINT opravneni_konkretni_pkey PRIMARY KEY (id),
    CONSTRAINT opravneni_konkretni_id_key UNIQUE (id),
    CONSTRAINT opravneni_opravneni FOREIGN KEY (parent_opravneni) REFERENCES public.opravneni (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE
    SET NULL,
        CONSTRAINT opravneni_vazba_na_opravneni FOREIGN KEY (vazba_na_konkretni_opravneni) REFERENCES public.opravneni_konkretni (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE
    SET NULL
);
alter TABLE opravneni
alter column adresa_v_aplikaci TYPE VARCHAR(50);
alter TABLE opravneni drop column opravneni;
alter TABLE opravneni drop column opravneni_dle_stavu;