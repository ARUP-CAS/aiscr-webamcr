-- 1. migrace sloupce vedouci_akce a vedouci_akce_ostatni tabulky akce do tabulky akce_vedouci
-- TODO MIGRACE ORGANIZACE A OSTATNI_ORGANIZACE

-- a) validace dat
--- odstraneni duplicit ve vedouci_akce_ostatni (az 2024 pripadu?)

update akce set vedouci_akce_ostatni = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT vedou.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    akce v,
    UNNEST(STRING_TO_ARRAY(v.vedouci_akce_ostatni, ';')) AS naz
) AS vedou
GROUP BY vedou.id
) AS sel
where akce.id = sel.id;

--- odstraneni duplicit kde uz je vedouci_akce_ostatni uveden jako hlavni
update akce set vedouci_akce_ostatni = sel.trimmed from (
select a.id as pid, a.vedouci_akce_ostatni, REPLACE(a.vedouci_akce_ostatni, r.vypis_cely, '') as trimmed from akce a join osoba r on r.id = a.vedouci_akce where a.vedouci_akce_ostatni like '%;' || r.vypis_cely || '%' or a.vedouci_akce_ostatni like r.vypis_cely || '%') as sel where sel.pid = akce.id;

-- Uklidit oddelovace
update akce set vedouci_akce_ostatni = REPLACE(vedouci_akce_ostatni, ';;', ';') where vedouci_akce_ostatni like '%;;%';
update akce set vedouci_akce_ostatni = REPLACE(vedouci_akce_ostatni, ';', '') where vedouci_akce_ostatni like ';%';

-- b) migrace dat
-- COMMENT: zatim nemigrujeme organizaci, proto odstranim not null
alter table akce_vedouci alter column organizace drop not null;

-- Vlozeni hlavnich vedoucich + jejich organizace (to jen pro jistotu, protože sloupec nakonec zachováme a data by se tak neměla ztratit)
insert into akce_vedouci(akce, vedouci, hlavni, organizace) select id, vedouci_akce, true, organizace from akce where vedouci_akce is not null;

-- Vlozeni ostatnich vecoucích + výchozí organizace pro ostatní vedoucí (správné nastavení budeme řešit updatem na konci migrace jako samostatný problém)
CREATE OR REPLACE FUNCTION migrateVedouciOstatniFromAkce() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..10
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            insert into akce_vedouci(akce, vedouci, hlavni, organizace) select distinct a.id, r.id, false, (SELECT organizace.id FROM organizace WHERE organizace.nazev_zkraceny = '[neuvedeno]') from akce a join osoba r on (r.vypis_cely) = split_part(vedouci_akce_ostatni, ';', counter) where split_part(a.vedouci_akce_ostatni, ';', counter) != '';
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateVedouciOstatniFromAkce();
drop function migrateVedouciOstatniFromAkce();

-- c) Tesovani migrace

-- TODO

-- 2. migrace vedoucich z neident_akce do tabulky neident_akce_vedouci
-- Přesunuto do migrace_dat_3.sql

-- 3. migrace dokument_autor

-- a) Validace dat

update dokument set autor = substr(autor, 1, length(autor) - 1) where autor like '%;';

update dokument set autor = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT katastru.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    dokument v,
    UNNEST(STRING_TO_ARRAY(v.autor, ';')) AS naz
) AS katastru
GROUP BY katastru.id
) AS sel
where dokument.id = sel.id;


-- b) Migrace dat

CREATE OR REPLACE FUNCTION migrateAutorFromDokument() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..20
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            insert into dokument_autor(dokument, autor, poradi) select distinct a.id, r.id, counter from dokument a join osoba r on r.vypis_cely = split_part(autor, ';', counter) where split_part(a.autor, ';', counter) != '';
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateAutorFromDokument();
drop function migrateAutorFromDokument();

-- c) Test migrace

-- COMMENT: sloupec autor obsahuje taky hodnotu anonym ktera nejde namapovat takze se nezmigruje (14 000 zaznamu); DN: Opraveno změnou napojení na vypis_cely.

-- 4. migrace mapovani autora externiho zdroje na jejich id z heslare jmen

-- a) Validace dat

update externi_zdroj set autori = substr(autori, 1, length(autori) - 1) where autori like '%;';

-- b) Migrace dat

CREATE OR REPLACE FUNCTION migrateAutorFromExterniZdroj() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..20
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            insert into externi_zdroj_autor(externi_zdroj, autor, poradi) select distinct a.id, r.id, counter from externi_zdroj a join osoba r on r.vypis_cely = split_part(autori, ';', counter) where split_part(a.autori, ';', counter) != '';
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateAutorFromExterniZdroj();
drop function migrateAutorFromExterniZdroj();

-- c) Test migrace
