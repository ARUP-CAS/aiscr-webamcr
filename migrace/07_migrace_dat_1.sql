-- 1. migrace sloupce katastr a dalsi_katastry tabulky akce do sloupce katastr tabulky akce%katastr -> mapovani katastru na jejich id

-- a) Prikazy migrace

-- Kdyz chci muzi si zazalohovat tabulku akci
--CREATE TABLE akce_backup AS TABLE akce;

-- VALIDACE DAT
-- trim nazvu, protoze tam jsou i mezery na konci
update ruian_katastr set nazev = TRIM(nazev);
-- nektere radky maji na konci ';' prikaz by je mel odebrat
update akce set dalsi_katastry = substr(dalsi_katastry, 1, length(dalsi_katastry) - 1) where dalsi_katastry like '%;';
-- odstraneni duplicit
update akce set dalsi_katastry = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT katastru.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    akce v,
    UNNEST(STRING_TO_ARRAY(v.dalsi_katastry, ';')) AS naz
) AS katastru
GROUP BY katastru.id
) AS sel
where akce.id = sel.id;

-- Odstraneni duplicit kde hlavni katastr je taky ve sloupci dalsi_katastry (50)
update akce set dalsi_katastry = sel.trimmed from (
select p.id as pid, p.katastr, r.nazev, p.dalsi_katastry, REPLACE(p.dalsi_katastry, r.nazev || ' (' || UPPER(o.nazev) || ')', '') as trimmed from akce p join ruian_katastr r on r.id = p.katastr join ruian_okres o on o.id = r.okres where p.dalsi_katastry like
'%;' || r.nazev || ' (' || UPPER(o.nazev) || ')' || '%' or p.dalsi_katastry like r.nazev || ' (' || UPPER(o.nazev) || ')' || '%') as sel where sel.pid = akce.id;
-- Uklidit oddelovace
update akce set dalsi_katastry = REPLACE(dalsi_katastry, ';;', ';') where dalsi_katastry like '%;;%';
update akce set dalsi_katastry = REPLACE(dalsi_katastry, ';', '') where dalsi_katastry like ';%';

-- Podivam se kolik katastru akce ma v relaci:
-- SELECT id, (length(dalsi_katastry) - length(replace(dalsi_katastry, ';', '')) + 1) as maximum from akce where dalsi_katastry is not null and dalsi_katastry != '' order by maximum desc;

-- Celkovy pocet druhych katastru: 3327
-- SELECT sum(length(dalsi_katastry) - length(replace(dalsi_katastry, ';', '')) + 1) from akce where dalsi_katastry is not null and dalsi_katastry != '';

-- migrace sloupce akce.katastr je v pohode protoze tam jsou id-cka
insert into akce_katastr(akce, katastr, hlavni) select id, katastr, true from akce where katastr is not null;

-- Funkce ktera zmigruje vsechny druhe a dalsi katastry
CREATE OR REPLACE FUNCTION migrateCatastersFromAkce() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..150
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            with kat AS
            (
              SELECT k.id, k.nazev || ' (' || UPPER(o.nazev) || ')' AS naz FROM ruian_katastr k
              JOIN ruian_okres o ON k.okres = o.id
            )
            insert into akce_katastr(akce, katastr, hlavni)
            select distinct a.id, kat.id, false from akce a
            join kat on kat.naz = SUBSTRING(split_part(a.dalsi_katastry, ';', counter), 1, POSITION(')' in split_part(a.dalsi_katastry, ';', counter)))
            where split_part(a.dalsi_katastry, ';', counter) != '' AND NOT EXISTS (SELECT 1 FROM akce_katastr AS ak WHERE ak.akce = a.id AND ak.katastr = kat.id);
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateCatastersFromAkce();
drop function migrateCatastersFromAkce();

-- b) Tesovani migrace

-- TODO

-- 2. Migrace katastru z tabulky lokalita

-- VALIDACE DAT
-- nektere radky maji na konci ';' prikaz by je mel odebrat
update lokalita set dalsi_katastry = substr(dalsi_katastry, 1, length(dalsi_katastry) - 1) where dalsi_katastry like '%;';
-- odstraneni duplicit
update lokalita set dalsi_katastry = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT katastru.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    lokalita v,
    UNNEST(STRING_TO_ARRAY(v.dalsi_katastry, ';')) AS naz
) AS katastru
GROUP BY katastru.id
) AS sel
where lokalita.id = sel.id;

-- Odstraneni duplicit kde hlavni katastr je taky ve sloupci dalsi_katastry
update lokalita set dalsi_katastry = sel.trimmed from (
select p.id as pid, p.katastr, r.nazev, p.dalsi_katastry, REPLACE(p.dalsi_katastry, r.nazev || ' (' || UPPER(o.nazev) || ')', '') as trimmed from lokalita p join ruian_katastr r on r.id = p.katastr join ruian_okres o on o.id = r.okres where p.dalsi_katastry like
'%;' || r.nazev || ' (' || UPPER(o.nazev) || ')' || '%' or p.dalsi_katastry like r.nazev || ' (' || UPPER(o.nazev) || ')' || '%') as sel where sel.pid = lokalita.id;
-- Uklidit oddelovace
update lokalita set dalsi_katastry = REPLACE(dalsi_katastry, ';;', ';') where dalsi_katastry like '%;;%';
update lokalita set dalsi_katastry = REPLACE(dalsi_katastry, ';', '') where dalsi_katastry like ';%';

-- a) migrace dat

insert into lokalita_katastr(lokalita, katastr, hlavni) select id, katastr, true from lokalita where katastr is not null;

CREATE OR REPLACE FUNCTION migrateCatastersFromLokalita() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..10
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            with kat AS
            (
              SELECT k.id, k.nazev || ' (' || UPPER(o.nazev) || ')' AS naz FROM ruian_katastr k
              JOIN ruian_okres o ON k.okres = o.id
            )
            insert into lokalita_katastr(lokalita, katastr, hlavni)
            select distinct a.id, kat.id, false from lokalita a
            join kat on kat.naz = SUBSTRING(split_part(a.dalsi_katastry, ';', counter), 1, POSITION(')' in split_part(a.dalsi_katastry, ';', counter)))
            where split_part(a.dalsi_katastry, ';', counter) != '' AND NOT EXISTS (SELECT 1 FROM lokalita_katastr AS ak WHERE ak.lokalita = a.id AND ak.katastr = kat.id);
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateCatastersFromLokalita();
drop function migrateCatastersFromLokalita();

-- b) Tesovani migrace

-- TODO

-- 3. Migrace katastru z tabulky projekt

-- Validace dat
-- Odstraneni koncu textu kde text konci na ';'
update projekt set dalsi_katastry = substr(dalsi_katastry, 1, length(dalsi_katastry) - 1) where dalsi_katastry like '%;';

-- Kolik nejvic katastru je v relaci s jednim projektem? 71
--SELECT id, (length(dalsi_katastry) - length(replace(dalsi_katastry, ';', '')) + 1) as maximum from projekt where dalsi_katastry is not null and dalsi_katastry != '' order by maximum desc;

-- ostraneni duplicit kde hlavni katastr je taky ve sloupci dalsi_katastry (48)
update projekt set dalsi_katastry = sel.trimmed from (
select p.id as pid, p.katastr, r.nazev, p.dalsi_katastry, REPLACE(p.dalsi_katastry, r.nazev || ' (' || UPPER(o.nazev) || ')', '') as trimmed from projekt p join ruian_katastr r on r.id = p.katastr join ruian_okres o on o.id = r.okres where p.dalsi_katastry like
'%;' || r.nazev || ' (' || UPPER(o.nazev) || ')' || '%' or p.dalsi_katastry like r.nazev || ' (' || UPPER(o.nazev) || ')' || '%') as sel where sel.pid = projekt.id;
-- Uklidit oddelovace
update projekt set dalsi_katastry = REPLACE(dalsi_katastry, ';;', ';') where dalsi_katastry like '%;;%';
update projekt set dalsi_katastry = REPLACE(dalsi_katastry, ';', '') where dalsi_katastry like ';%';

-- Odstraneni duplicit ve sloupci dalsi_katastry
update projekt set dalsi_katastry = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT katastru.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    projekt v,
    UNNEST(STRING_TO_ARRAY(v.dalsi_katastry, ';')) AS naz
) AS katastru
GROUP BY katastru.id
) AS sel
where projekt.id = sel.id;


-- a) migarace dat
-- 117 000 hlavnich katastru
insert into projekt_katastr(projekt, katastr, hlavni) select id, katastr, true from projekt where katastr is not null;

-- dalsi katastry
CREATE OR REPLACE FUNCTION migrateCatastersFromProjekt() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..150
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            with kat AS
            (
              SELECT k.id, k.nazev || ' (' || UPPER(o.nazev) || ')' AS naz FROM ruian_katastr k
              JOIN ruian_okres o ON k.okres = o.id
            )
            insert into projekt_katastr(projekt, katastr, hlavni)
            select distinct a.id, kat.id, false from projekt a
            join kat on kat.naz = SUBSTRING(split_part(a.dalsi_katastry, ';', counter), 1, POSITION(')' in split_part(a.dalsi_katastry, ';', counter)))
            where split_part(a.dalsi_katastry, ';', counter) != '' AND NOT EXISTS (SELECT 1 FROM projekt_katastr AS ak WHERE ak.projekt = a.id AND ak.katastr = kat.id);
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migrateCatastersFromProjekt();
drop function migrateCatastersFromProjekt();

-- b) Testovani migrace

-- TODO
