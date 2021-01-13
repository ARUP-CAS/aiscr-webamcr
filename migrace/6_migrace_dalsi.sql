-- Adding path to the soubor table
ALTER TABLE "soubor" ADD COLUMN "path" varchar(100) DEFAULT 'not specified yet' NOT NULL;

-- Opravit defaultni prisutpnost u organizace aby ukazovala v heslari na archivare (z 4 na 859)
ALTER TABLE "organizace" ALTER COLUMN "zverejneni_pristupnost" SET DEFAULT 859;

ALTER TABLE heslar_nazev RENAME COLUMN heslar to nazev;

-- TODO jak u akci premigrovat historii tranzakci akci kdyz doslo k zjednoduseni stavovych tranzakci
-- mapovani stavu:
-- A3 = A1
-- A7 = A1
-- A6 = A2
-- A8 = A3
-- A4 = A3
-- A5 = A3 + set column odlozena_nz
-- mapovani tranzakci:
-- 1 - zapis =
-- 2 - autorizace =
-- 3 - (nebyl migrovan) = nic
-- 4 - archivace_zaa =
-- 5 - odlozeni_nz =
-- 6 - podani_nz =
-- 7 - (nebyl migrovan) = nic
-- 8 - archivace =
-- NOVE TRANZAKCE AKCI:
-- 1 - zapsani
-- 2 - odeslani
-- 3 - archivovani
-- 4 - vraceni COMMENT: bude samostatna tranzakce nebo vzdy stejna?? u projektu je vzdy stejna
