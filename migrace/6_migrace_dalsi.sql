-- Adding path to the soubor table
ALTER TABLE "soubor" ADD COLUMN "path" varchar(100) DEFAULT 'not specified yet' NOT NULL;

-- Opravit defaultni prisutpnost u organizace aby ukazovala v heslari na archivare (z 4 na 859)
ALTER TABLE "organizace" ALTER COLUMN "zverejneni_pristupnost" SET DEFAULT 859;
-- Opravit defaultni prisutpnost u organizace aby ukazovala v heslari na archivare (z 1 na 857)
ALTER TABLE "archeologicky_zaznam" ALTER COLUMN "pristupnost" SET DEFAULT 857;

ALTER TABLE projekt_katastr add column id serial;
ALTER TABLE projekt_katastr rename column projekt to projekt_id;
ALTER TABLE projekt_katastr rename column katastr to katastr_id;

ALTER TABLE archeologicky_zaznam_katastr add column id serial;
ALTER TABLE archeologicky_zaznam_katastr rename column archeologicky_zaznam to archeologicky_zaznam_id;
ALTER TABLE archeologicky_zaznam_katastr rename column katastr to katastr_id;

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
-- 1 - zapis = 1
-- 2 - autorizace = 2
-- 3 - vraceni = 4
-- 4 - archivace_zaa = 3
-- 5 - odlozeni_nz = 3
-- 6 - podani_nz = 2
-- 7 - vraceni = 4
-- 8 - archivace = 3
-- NOVE TRANZAKCE AKCI:
-- 1 - zapsani
-- 2 - odeslani
-- 3 - archivovani
-- 4 - vraceni

-- 4 -> 3
-- 5 -> 3
-- 8 -> 3
-- 6 -> 2
-- COMMENT: TO CO JE VE 3 MUSI JIT DO DOCASNEHO STAVU 111 abch tam mohl dat to co tam ma byt:
update historie h set typ_zmeny = 111 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=3) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=8) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=5) as sel where id=sel.hid;
update historie h set typ_zmeny = 3 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=4) as sel where id=sel.hid;
update historie h set typ_zmeny = 2 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='akce' and his.typ_zmeny=6) as sel where id=sel.hid;


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
-- TODO zmigrovat dokumenty ktere nejsou modely 3D ze stavu 2 na stav 1 POZOR: jenom ty dokumenty kterych akce (archeologicky_zaznam) jsou ve stavu 1
update dokument set stav = 1 where id in (select d.id from dokument as d join dokument_cast as dc on dc.dokument = d.id join archeologicky_zaznam as az on az.id = dc.archeologicky_zaznam where d.rada !=863 and d.stav = 2 and az.stav=1);
--Takze:
-- 5 -> 4
-- 6 a 7 smazat -> ANO
update historie h set typ_zmeny = 4 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=5) as sel where id=sel.hid;
delete from historie where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and (his.typ_zmeny = 7 or his.typ_zmeny=6));

-- Jak vyresit username? Ted je username ident_cely a prihlasovani je udelano skrz email
alter table auth_user rename column username to ident_cely;

-- Akce a lokality ted maji spolecneho rodice (Archeologicky zaznam), nastaveni spravneho typu_vazby v historii
-- Ukazkovy select pro relevantni zaznamy historie pro archeologicky_zaznam typu akce
-- select his.id from historie his join historie_vazby as hv on hv.id=his.vazba join archeologicky_zaznam as az on az.historie = hv.id where az.typ_zaznamu='A';
update historie_vazby set typ_vazby='archeologicky_zaznam' where typ_vazby='akce' or typ_vazby='lokalita';

-- Jeste jsem zapomel domigrovat tranzakce akci 3 a 7 na 4
update historie h set typ_zmeny = 4 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=111) as sel where id=sel.hid;
update historie h set typ_zmeny = 4 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=7) as sel where id=sel.hid;

-- Odstraneni tranzakce AKTUALIZACE z historie samostatnych nalezu
delete from historie where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny = 8);
-- 6 a 7 u SN bude 5
update historie h set typ_zmeny = 5 from (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and (his.typ_zmeny=7 or hist.typ_zmeny=6)) as sel where id=sel.hid;

-- Migrace integer IDcek transakci na text
alter table historie add column typ_zmeny_text text;

--# Projekty
--OZNAMENI_PROJ: Final = "PX0"  # 0 Tady jde jeno o nove tranzakce protoze nulovych tranzakci se z predchozi databaze moc nezmigorvalo (datetime_born tam nebylo)
update historie set typ_zmeny_text = 'PX0' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=0);
--SCHVALENI_OZNAMENI_PROJ: Final = "P01"  # 1 Tady je jich nula protoze
-- COMMENT: Schvaleni je v pripade historie to same jako zapsani
--ZAPSANI_PROJ: Final = "PX1"  # 1
update historie set typ_zmeny_text = 'PX1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=1);
--PRIHLASENI_PROJ: Final = "P12"  # 2
update historie set typ_zmeny_text = 'PX1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=2);
--ZAHAJENI_V_TERENU_PROJ: Final = "P23"  # 3
update historie set typ_zmeny_text = 'P23' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=3);
--UKONCENI_V_TERENU_PROJ: Final = "P34"  # 4
update historie set typ_zmeny_text = 'P34' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=4);
--UZAVRENI_PROJ: Final = "P45"  # 5
update historie set typ_zmeny_text = 'P45' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=5);
--ARCHIVACE_PROJ: Final = "P56"  # 6
update historie set typ_zmeny_text = 'P56' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=6);
--NAVRZENI_KE_ZRUSENI_PROJ: Final = "P*7"  # 7
update historie set typ_zmeny_text = 'P*7' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=7);
--RUSENI_PROJ: Final = "P78"  # 8
update historie set typ_zmeny_text = 'P78' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=8);
--VRACENI_PROJ: Final = "P-1"  # New
--# Akce + Lokalita (archeologicke zaznamy)
--ZAPSANI_AZ: Final = "AZ01"  # 1
update historie set typ_zmeny_text = 'AZ01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=1);
--ODESLANI_AZ: Final = "AZ12"  # 2
update historie set typ_zmeny_text = 'AZ12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=2);
--ARCHIVACE_AZ: Final = "AZ23"  # 3
update historie set typ_zmeny_text = 'AZ23' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=3);
--VRACENI_AZ: Final = "AZ-1"  # New
update historie set typ_zmeny_text = 'AZ-1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=4);
--# Dokument
--ZAPSANI_DOK: Final = "D01"  # 1
update historie set typ_zmeny_text = 'D01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=1);
--ODESLANI_DOK: Final = "D12"  # 2
update historie set typ_zmeny_text = 'D12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=2);
--ARCHIVACE_DOK: Final = "D23"  # 3
update historie set typ_zmeny_text = 'D23' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=3);
--VRACENI_DOK: Final = "D-1"  # New
update historie set typ_zmeny_text = 'D-1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='dokument' and his.typ_zmeny=4);

--# Samostatny nalez
--ZAPSANI_SN: Final = "SN01"  # 1
update historie set typ_zmeny_text = 'SN01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny=1);
--ODESLANI_SN: Final = "SN12"  # 2
update historie set typ_zmeny_text = 'SN12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny=2);
--POTVRZENI_SN: Final = "SN23"  # 3
update historie set typ_zmeny_text = 'SN23' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny=3);
--ARCHIVACE_SN: Final = "SN34"  # 4
update historie set typ_zmeny_text = 'SN34' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny=4);
--VRACENI_SN: Final = "SN-1"  # 5
update historie set typ_zmeny_text = 'SN-1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny=5);

-- COMMENT: Jak resit stavy uzivatelu??? TEN NEMA SLOUPEC STAV!!!
--# Uzivatel
--update historie set typ_zmeny_text = 'SN01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='uzivatel' and his.typ_zmeny=1);
--# Pian
--ZAPSANI_PIAN: Final = "PI01"
update historie set typ_zmeny_text = 'PI01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='pian' and his.typ_zmeny=1);
--POTVRZENI_PIAN: Final = "PI12"
update historie set typ_zmeny_text = 'PI12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='pian' and his.typ_zmeny=2);
-- COMMENT: Tady taky neni sloupcec STAV ale puze prechody. Chtelo by to tady se tomu taky venovat a predelat to na stavy.
--# Uzivatel_spoluprace
--# Externi_zdroj
--IMPORT_EXT_ZD: Final = "EZ01"  # 1
update historie set typ_zmeny_text = 'EZ01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='externi_zdroj' and his.typ_zmeny=1);
--ZAPSANI_EXT_ZD: Final = "EZ12"  # 2
update historie set typ_zmeny_text = 'EZ12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='externi_zdroj' and his.typ_zmeny=2);
--POTVRZENI_EXT_ZD: Final = "EZ23"  # 3
update historie set typ_zmeny_text = 'EZ23' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='externi_zdroj' and his.typ_zmeny=3);
--VRACENI_EXT_ZD: Final = "EZ-1"  # New
-- COMMENT: tohle neni treba migrovat
alter table historie rename column typ_zmeny to typ_zmeny_old;
alter table historie rename column typ_zmeny_text to typ_zmeny;
alter table historie alter typ_zmeny_old drop not null;

-- COMMENT: tenhle sloupec tam nemusi byt, je to jen pro migraci
alter table archeologicky_zaznam alter column stav_stary drop not null;
