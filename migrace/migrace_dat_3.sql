

-- 1. migrace dokument.typ_dokumentu_posudek dle heslar_posudek do nove tabulky

-- a) Validace dat

update dokument set typ_dokumentu_posudek = sel.kat from (
SELECT
  id, STRING_AGG(DISTINCT katastru.naz, ';') AS kat
FROM (
  SELECT
    id,
    naz
  FROM
    dokument v,
    UNNEST(STRING_TO_ARRAY(v.typ_dokumentu_posudek, ';')) AS naz
) AS katastru
GROUP BY katastru.id
) AS sel
where dokument.id = sel.id;


update dokument set typ_dokumentu_posudek = substr(typ_dokumentu_posudek, 1, length(typ_dokumentu_posudek) - 1) where typ_dokumentu_posudek like '%;';

-- b) Migrace dat

CREATE OR REPLACE FUNCTION migratePosudkyFromDokument() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..10
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            insert into dokument_posudek(dokument, posudek) select distinct a.id, r.id from dokument a join heslar_posudek r on r.nazev = split_part(typ_dokumentu_posudek, ';', counter) where split_part(a.typ_dokumentu_posudek, ';', counter) != '';
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select migratePosudkyFromDokument();
drop function migratePosudkyFromDokument();

-- c) Test dat


-- 2. migrace referenci akci, lokality a neident_akce na dokument_cast

-- a) Validace dat
-- b) Migrace dat
---- 1. seskupujici zaznamy na ktere se bude odkazovat (pro kazdou akci/lokalitu jeden)
insert into dokument_cast_vazby(typ_vazby) select 'akce' from akce;
insert into dokument_cast_vazby(typ_vazby) select 'lokalita' from lokalita;

---- 2. prirazeni akci a lokalite aby referovali na svoji vazbu

update akce d set dokumenty_casti = sub.rn from (select id, row_number() OVER (order by id) as rn from akce) sub where d.id = sub.id;
update lokalita d set dokumenty_casti = sub.rn from (select id, (select count(*) from akce) + row_number() OVER (order by id) as rn from lokalita) sub where d.id = sub.id;

---- 3. prirazeni reference na seskupujici zaznam v tabulce dokument_cast

update dokument_cast s set vazba = d.dokumenty_casti from (select id, dokumenty_casti from akce) d where d.id = s.vazba;
update dokument_cast s set vazba = d.dokumenty_casti from (select id, dokumenty_casti from lokalita) d where d.id = s.vazba;

-- c) Test migrace


-- 3. spojeni tabulek komponenta_dokument a komponenta a migrace referenci dokumentacni_jednotky a dokumentu_cast na komopnenu

------ a) Validace dat
------ b) Migrace dat

insert into komponenta_vazby(typ_vazby) select 'dokument_cast' from dokument_cast;
insert into komponenta_vazby(typ_vazby) select 'dokumentacni_jednotka' from dokumentacni_jednotka;
update dokument_cast d set komponenty = sub.rn from (select id, row_number() OVER (order by id) as rn from dokument_cast) sub where d.id = sub.id;
update dokumentacni_jednotka d set komponenty = sub.rn from (select id, (select count(*) from dokument_cast) + row_number() OVER (order by id) as rn from dokumentacni_jednotka) sub where d.id = sub.id;

-- dropnu foreign key sloupce jednotka_dokument na dokument_cast
alter table komponenta_dokument drop constraint komponenta_dokument_jednotka_dokument_fkey;
-- nastavim aby sloupec jednotka_dokument ukazoval na stejnou vazbu v tabulce komponenta_vazby jako ukazuje sloupec komponenty z tabulky dokument_cast
update komponenta_dokument s set jednotka_dokument = d.komponenty from (select id, komponenty from dokument_cast) d where d.id = s.jednotka_dokument;
-- nastavim aby komponenta.vazba ukazovala na vazbu ktera patri zaznamu dokumentacni_jednotka COMMENT: 199 komponenta neukazuje na dokumentacni_jednotku ale nevim kam
update komponenta s set vazba = d.komponenty from (select id, komponenty from dokumentacni_jednotka) d where d.id = s.parent;

-- spojeni tabulky komponenta a komponenta_dokument a migrace aktivit komponenty_dokument do komponenta_aktivita, COMMENT: zaznamy komponenta_dokument budou mit nove id
alter table komponenta add column komponenta_dokument_id integer;
insert into komponenta(obdobi, presna_datace, areal, poznamka, jistota, ident_cely, vazba, aktivita_sidlistni, aktivita_pohrebni, aktivita_vyrobni, aktivita_tezebni, aktivita_kultovni, aktivita_komunikace, aktivita_deponovani, aktivita_boj, aktivita_jina, aktivita_intruze, komponenta_dokument_id) select obdobi, presna_datace, areal, poznamka, jistota, ident_cely, jednotka_dokument, aktivita_sidlistni, aktivita_pohrebni, aktivita_vyrobni, aktivita_tezebni, aktivita_kultovni, aktivita_komunikace, aktivita_deponovani, aktivita_boj, aktivita_jina, aktivita_intruze, id from komponenta_dokument;

insert into komponenta_aktivita(komponenta, aktivita) select id, 1 from komponenta where aktivita_sidlistni = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 2 from komponenta where aktivita_pohrebni = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 3 from komponenta where aktivita_vyrobni = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 4 from komponenta where aktivita_tezebni = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 5 from komponenta where aktivita_kultovni = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 6 from komponenta where aktivita_komunikace = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 7 from komponenta where aktivita_deponovani = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 8 from komponenta where aktivita_boj = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 9 from komponenta where aktivita_jina = true;
insert into komponenta_aktivita(komponenta, aktivita) select id, 10 from komponenta where aktivita_intruze = true;

------ c) Test dat


-- 4. migrace referenci akce a lokality na dokumentacni_jednotku

-- a) Validace dat
-- b) Migrace dat

---- 1. seskupujici zaznamy na ktere se bude odkazovat (pro kazdou akci/lokalitu jeden)
insert into dokumentacni_jednotka_vazby(typ_vazby) select 'akce' from akce;
insert into dokumentacni_jednotka_vazby(typ_vazby) select 'lokalita' from lokalita;

---- 2. prirazeni akci a lokalite aby referovali na svoji vazbu

update akce d set dokumentacni_jednotky = sub.rn from (select id, row_number() OVER (order by id) as rn from akce) sub where d.id = sub.id;
update lokalita d set dokumentacni_jednotky = sub.rn from (select id, (select count(*) from akce) + row_number() OVER (order by id) as rn from lokalita) sub where d.id = sub.id;

---- 3. prirazeni reference na seskupujici zaznam v tabulce dokumentacni_jednotka

update dokumentacni_jednotka s set vazba = a.dokumentacni_jednotky from (select id, dokumentacni_jednotky from akce) a where a.id = s.parent;
update dokumentacni_jednotka s set vazba = d.dokumentacni_jednotky from (select id, dokumentacni_jednotky from lokalita) d where d.id = s.parent;

-- c) Test dat

-- 5. migrace referenci akce a lokality na externi_odkaz

-- a) Validace dat
-- b) Migrace dat

---- 1. seskupujici zaznamy na ktere se bude odkazovat (pro kazdou akci/lokalitu jeden)
insert into externi_odkaz_vazby(typ_vazby) select 'akce' from akce;
insert into externi_odkaz_vazby(typ_vazby) select 'lokalita' from lokalita;

---- 2. prirazeni akci a lokalite aby referovali na svoji vazbu

update akce d set externi_odkazy = sub.rn from (select id, row_number() OVER (order by id) as rn from akce) sub where d.id = sub.id;
update lokalita d set externi_odkazy = sub.rn from (select id, (select count(*) from akce) + row_number() OVER (order by id) as rn from lokalita) sub where d.id = sub.id;

---- 3. prirazeni reference na seskupujici zaznam v tabulce externi_odkaz

update externi_odkaz s set vazba = a.externi_odkazy from (select id, externi_odkazy from akce) a where a.id = s.vazba;
update externi_odkaz s set vazba = d.externi_odkazy from (select id, externi_odkazy from lokalita) d where d.id = s.vazba;

---- 4. vytvoreni foreign key
alter table externi_odkaz add constraint externi_odkaz_vazba_fkey foreign key (vazba) references externi_odkaz_vazby(id);

-- c) Test dat

-- 6. zmena typu sloupce let.pilot ze string na integer z tabulky osoby COMMENT: nakonec rozhodnuto ponechat jako text
-- zjistit spravne mapovani a dedelat migraci
--alter table let rename column pilot to pilot_jmeno;
--alter table let add column pilot integer;
--alter table let add constraint let_pilot_fkey foreign key (pilot) references osoba(id);

-- 7. migrace referenci na neident_akci z dokument_cast.vazba do neidnet_akce.dokument_cast

update neident_akce d set dokument_cast = sub.id from (select vazba, id from dokument_cast where vazba in (select id from neident_akce)) sub where d.id = sub.vazba;
-- smazu reference z vazby na neident_akci
update dokument_cast set vazba = null where vazba in (select id from neident_akce);

-- 8. migrace externi_zdroj.sbornik_editor
insert into externi_zdroj_editor(externi_zdroj, editor, poradi) values
(920770,29277, 1),
(778484,28785, 1),
(778484,29256, 2),
(778485,28785, 1),
(778485,29256, 2),
(734337,28771, 1),
(809030,29810, 1),
(700801,700800,1),
(769546,29277, 1),
(1030059,28950,1),
(778488,28785, 1),
(778488,29256, 2);
