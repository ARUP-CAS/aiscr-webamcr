-- Adding path to the soubor table
ALTER TABLE "soubor" ADD COLUMN "path" varchar(100) DEFAULT 'not specified yet' NOT NULL;

-- Opravit defaultni prisutpnost u organizace aby ukazovala v heslari na archivare (z 4 na 859)
ALTER TABLE "organizace" ALTER COLUMN "zverejneni_pristupnost" SET DEFAULT 859;

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
-- 4 - vraceni COMMENT: bude samostatna tranzakce nebo vzdy stejna?? u projektu je vzdy stejna

-- 4 -> 3
-- 5 -> 3
-- 8 -> 3
-- 6 -> 2
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=8) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=5) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=4) as sel where id=sel.hid;
update historie h set typ_zmeny = 2 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=6) as sel where id=sel.hid;
