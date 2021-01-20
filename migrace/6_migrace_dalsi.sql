-- Adding path to the soubor table
ALTER TABLE "soubor" ADD COLUMN "path" varchar(100) DEFAULT 'not specified yet' NOT NULL;

-- Opravit defaultni prisutpnost u organizace aby ukazovala v heslari na archivare (z 4 na 859)
ALTER TABLE "organizace" ALTER COLUMN "zverejneni_pristupnost" SET DEFAULT 859;

ALTER TABLE projekt_katastr add column id serial;
ALTER TABLE projekt_katastr rename column projekt to projekt_id;
ALTER TABLE projekt_katastr rename column katastr to katastr_id;

alter table projekt_katastr drop constraint "projekt_katastr_katastr_fk";
alter table projekt_katastr add constraint projekt_katastr_katastr_fk foreign key (katastr_id) references ruian_katastr(id) on delete cascade;
alter table projekt_katastr drop constraint "projekt_katastr_projekt_fk";
alter table projekt_katastr add constraint projekt_katastr_projekt_fk foreign key (projekt_id) references projekt(id) on delete cascade;

ALTER TABLE heslar_nazev RENAME COLUMN heslar to nazev;

-- COMMENT: jak u akci premigrovat historii tranzakci akci kdyz doslo k zjednoduseni stavovych tranzakci
-- mapovani stavu:
-- A3 = A1
-- A7 = A1
-- A6 = A2
-- A8 = A3
-- A4 = A3
-- A5 = A3 + set column odlozena_nz
-- mapovani tranzakci:
-- 1 - zapis = 1 AX1 ZUSTAVA
-- 2 - autorizace = 2 A12 ZUSTAVA
-- 3 - (nebyl migrovan) = nic
-- 4 - archivace_zaa = 3 A24
-- 5 - odlozeni_nz = 3 A25
-- 6 - podani_nz = 2 A16
-- 7 - (nebyl migrovan) = nic
-- 8 - archivace = 3 A68
-- NOVE TRANZAKCE AKCI:
-- 1 - zapsani
-- 2 - odeslani
-- 3 - archivovani
-- 4 - vraceni

-- 4 -> 3
-- 5 -> 3
-- 8 -> 3
-- 6 -> 2
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=8) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=5) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=4) as sel where id=sel.hid;
update historie h set typ_zmeny = 2 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=6) as sel where id=sel.hid;

-- COMMENT???? CO S TIM?
-- Dalsi vec je ze v historii maji modely 3D (dokumenty) jinou historii (transakce) jako maji klasicke dokumenty:
--ZAPSANI = 1
--ODESLANI = 2
--ARCHIVACE = 3
--ZPET_K_ODESLANI = 4
--ZPET_K_ZAPSANI = 5
--AKTUALIZACE = 6
--ZMENA_AUTORA = 7
-- Tranzakce mezi stavy 3D modelu v nove historii musime namapovat na dokumenty aby byly stejne
--ZAPSANI = 1
--ODESLANI = 2
--ARCHIVACE = 3
--VRACENI = 4
--Takze:
-- 5 -> 4
-- 6 a 7 smazat ?
update historie h set typ_zmeny = 4 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=5) as sel where id=sel.hid;
delete from historie where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and (his.typ_zmeny = 7 or his.typ_zmeny=6));

-- Jak vyresit username? Ted je username ident_cely a prihlasovani je udelano skrz email
