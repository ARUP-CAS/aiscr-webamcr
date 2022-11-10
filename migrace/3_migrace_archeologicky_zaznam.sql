-- Nova tabulka archeologicky_zaznam
CREATE table public.archeologicky_zaznam (
    id serial primary key,
    typ_zaznamu text not null,
    pristupnost integer not null ,
    ident_cely text,
    stav smallint not null,
    historie integer not null,
    uzivatelske_oznaceni text
);

alter table archeologicky_zaznam add constraint archeologicky_zaznam_pristupnost_fkey foreign key (pristupnost) references heslar(id);
alter table archeologicky_zaznam add constraint check_correct_type check (typ_zaznamu = 'L' or typ_zaznamu = 'A');
alter table archeologicky_zaznam add constraint archeologicky_zaznam_historie_fkey foreign key (historie) references historie_vazby(id);

-- Prejmenovana tabulka akce_katastr
alter table akce_katastr rename to archeologicky_zaznam_katastr;
alter table archeologicky_zaznam_katastr drop constraint akce_katastr_akce_fk;
alter table archeologicky_zaznam_katastr rename column akce to archeologicky_zaznam;
ALTER TABLE archeologicky_zaznam_katastr RENAME CONSTRAINT "akce_katastr_pkey" TO "archeologicky_zaznam_katastr_pkey";
ALTER TABLE archeologicky_zaznam_katastr RENAME CONSTRAINT "akce_katastr_katastr_fk" TO "archeologicky_zaznam_katastr_katastr_fkey";

-- migrace akci a lokalit do archeologickych zaznamu
-- 1. presunout akce
insert into archeologicky_zaznam (id, typ_zaznamu, pristupnost, ident_cely, stav, historie, uzivatelske_oznaceni) select id, 'A', pristupnost, ident_cely, stav, historie, uzivatelske_oznaceni from akce;

-- 2. presunout lokality
insert into archeologicky_zaznam (id, typ_zaznamu, pristupnost, ident_cely, stav, historie, uzivatelske_oznaceni) select id, 'L', pristupnost, ident_cely, stav, historie, uzivatelske_oznaceni from lokalita;

-- nastavit sekvenci archeologickeho_zaznamu na spravne cislo
select setval('archeologicky_zaznam_id_seq', (select MAX(id) from archeologicky_zaznam) + 1);

-- pridat cizi klic
alter table archeologicky_zaznam_katastr add constraint archeologicky_zaznam_katastr_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);

----- Editace relaci
--- Tabulka akce
----- pridat
--1. archeologicky_zaznam
alter table akce add column archeologicky_zaznam integer;
--2. odlozena_nz
alter table akce add column odlozena_nz boolean default false not null;
-- migrace odlozena_nz
update akce set odlozena_nz = true where stav = 5;
-- migrace reference na archeologicky zaznamu
update akce set archeologicky_zaznam = akce.id;
-- cizy klic na archeologicky zaznamu
alter table akce add constraint akce_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);
alter table akce add constraint akce_archeologicky_zaznam_key unique (archeologicky_zaznam);
alter table akce_vedouci drop constraint akce_vedouci_akce_fk;
alter table akce_vedouci add constraint akce_vedouci_akce_fkey foreign key (akce) references akce(archeologicky_zaznam);
-- akce ma jako primarni klic archeologicky_zaznam ne id
alter table vazba_projekt_akce drop constraint if exists vazba_projekt_akce_akce_fkey;
alter table historie_akce drop constraint if exists historie_akce_akce_fkey;
ALTER TABLE akce DROP CONSTRAINT akce_pkey;
ALTER TABLE akce ADD PRIMARY KEY (archeologicky_zaznam);

-- prejmenovat
--1. lokalizace na lokalizace_okolnosti
alter table akce rename column lokalizace to lokalizace_okolnosti;
--2. poznamka na souhrn_upresneni
alter table akce rename column poznamka to souhrn_upresneni;

-- migrace + smazat
--1. dokumentacni_jednotky
alter table dokumentacni_jednotka rename column vazba to archeologicky_zaznam;
alter table dokumentacni_jednotka drop constraint dokumentacni_jednotka_vazba_fkey;
-- migrace (mapovani id vazby na id akce(archeologickeho zaznamu))
-- nastav hodnoty sloupce archeologicky_zaznam na hodnotu sloupce archeologicky_zaznam z tabulky akce kde akce.dokumentacni_jednotky = dokumentacni_jednotka.vazba;
update dokumentacni_jednotka set archeologicky_zaznam = sel.zaznam from (select a.archeologicky_zaznam as zaznam, a.dokumentacni_jednotky, dj.id as sid from akce as a join dokumentacni_jednotka as dj on dj.archeologicky_zaznam = a.dokumentacni_jednotky) as sel where sel.sid = id;
-- nastav hodnoty sloupce archeologicky_zaznam na hodnotu sloupce archeologicky_zaznam z tabulky lokalita kde lokalita.dokumentacni_jednotky = dokumentacni_jednotka.vazba;
update dokumentacni_jednotka set archeologicky_zaznam = sel.zaznam from (select l.id as zaznam, l.dokumentacni_jednotky, dj.id as sid from lokalita as l join dokumentacni_jednotka as dj on dj.archeologicky_zaznam = l.dokumentacni_jednotky) as sel where sel.sid = id;
alter table dokumentacni_jednotka add constraint dokumentacni_jednotka_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);

--2. externi_odkazy
alter table externi_odkaz drop constraint externi_odkaz_vazba_fkey;
alter table externi_odkaz rename column vazba to archeologicky_zaznam;
update externi_odkaz set archeologicky_zaznam = sel.zaznam from (select a.archeologicky_zaznam as zaznam, a.externi_odkazy, eo.id as sid from akce as a join externi_odkaz as eo on eo.archeologicky_zaznam = a.externi_odkazy) as sel where sel.sid = id;
update externi_odkaz set archeologicky_zaznam = sel.zaznam from (select l.id as zaznam, l.externi_odkazy, eo.id as sid from lokalita as l join externi_odkaz as eo on eo.archeologicky_zaznam = l.externi_odkazy) as sel where sel.sid = id;
alter table externi_odkaz add constraint externi_odkaz_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);

--3. dokumenty_casti
alter table dokument_cast rename column vazba to archeologicky_zaznam;
update dokument_cast set archeologicky_zaznam = sel.zaznam from (select a.archeologicky_zaznam as zaznam, a.dokumenty_casti, dc.id as sid from akce as a join dokument_cast as dc on dc.archeologicky_zaznam = a.dokumenty_casti) as sel where sel.sid = id;
update dokument_cast set archeologicky_zaznam = sel.zaznam from (select l.id as zaznam, l.dokumenty_casti, dc.id as sid from lokalita as l join dokument_cast as dc on dc.archeologicky_zaznam = l.dokumenty_casti) as sel where sel.sid = id;
alter table dokument_cast add constraint dokument_cast_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);

--4. historie migrace done
--5. ident_cely migrace done
--6. id migrace done
--7. pristupnost migrace done
--8. stav migrace done
--9. uzivatelske_oznaceni migrace done

----- pridat k lokalite
--1. archeologicky_zaznam
alter table lokalita add column archeologicky_zaznam integer;
-- migrace reference na archeologicky zaznamu
update lokalita set archeologicky_zaznam = lokalita.id;
-- cizy klic na archeologicky zaznamu
alter table lokalita add constraint lokalita_archeologicky_zaznam_fkey foreign key (archeologicky_zaznam) references archeologicky_zaznam(id);
alter table lokalita add constraint lokalita_archeologicky_zaznam_key unique (archeologicky_zaznam);
alter table lokalita_katastr drop constraint lokalita_katastr_lokalita_fk;
-- akce ma jako primarni klic archeologicky_zaznam ne id
ALTER TABLE lokalita DROP CONSTRAINT lokalita_pkey;
ALTER TABLE lokalita ADD PRIMARY KEY (archeologicky_zaznam);

----- Migrace
--1. lokalita_katastr
insert into archeologicky_zaznam_katastr (archeologicky_zaznam, katastr, hlavni) select lokalita, katastr, hlavni from lokalita_katastr;


---- MAZANI
--- SLOUPCE
--1. dokumentacni_jednotky
alter table akce drop column dokumentacni_jednotky;
alter table lokalita drop column dokumentacni_jednotky;
--2. externi_odkazy
alter table akce drop column externi_odkazy;
alter table lokalita drop column externi_odkazy;
--3. dokumenty_casti
alter table akce drop column dokumenty_casti;
alter table lokalita drop column dokumenty_casti;
--4. historie migrace done
alter table akce drop column historie;
alter table lokalita drop column historie;
--5. ident_cely migrace done
alter table akce drop column ident_cely;
alter table lokalita drop column ident_cely;
--6. id migrace done
alter table akce drop column id;
alter table lokalita drop column id;
--7. pristupnost migrace done
alter table akce drop column pristupnost;
alter table lokalita drop column pristupnost;
--8. stav migrace done
alter table akce drop column stav;
alter table lokalita drop column stav;
--9. uzivatelske_oznaceni migrace done
alter table akce drop column uzivatelske_oznaceni;
alter table lokalita drop column uzivatelske_oznaceni;

--- TABULKY
drop table lokalita_katastr;
drop table dokument_cast_vazby;
drop table dokumentacni_jednotka_vazby;
drop table externi_odkaz_vazby;
