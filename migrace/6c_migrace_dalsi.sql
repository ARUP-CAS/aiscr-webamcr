
-- Odstraneni tranzakce AKTUALIZACE z historie samostatnych nalezu
delete from historie where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and his.typ_zmeny = 8);
-- 6 a 7 u SN bude 5
update historie h set typ_zmeny = 5 where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='samostatny_nalez' and (his.typ_zmeny=7 or his.typ_zmeny=6));

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
update historie set typ_zmeny_text = 'P12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='projekt' and his.typ_zmeny=2);
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

--# Uzivatel
update historie set typ_zmeny_text = 'HR' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='uzivatel' and (his.typ_zmeny=1 or his.typ_zmeny=0));

--# Pian
--ZAPSANI_PIAN: Final = "PI01"
update historie set typ_zmeny_text = 'PI01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='pian' and his.typ_zmeny=1);
--POTVRZENI_PIAN: Final = "PI12"
update historie set typ_zmeny_text = 'PI12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='pian' and his.typ_zmeny=2);
-- COMMENT: Tady taky neni sloupcec STAV ale puze prechody. Chtelo by to tady se tomu taky venovat a predelat to na stavy.

--# Uzivatel_spoluprace
update historie set typ_zmeny_text = 'SP01' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='uzivatel_spoluprace' and his.typ_zmeny=1);
update historie set typ_zmeny_text = 'SP12' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='uzivatel_spoluprace' and (his.typ_zmeny=2 or his.typ_zmeny=4));
update historie set typ_zmeny_text = 'SP-1' where id in (select his.id from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='uzivatel_spoluprace' and his.typ_zmeny=3);

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
alter table historie alter column typ_zmeny set not null;

-- COMMENT: tenhle sloupec tam nemusi byt, je to jen pro migraci
alter table archeologicky_zaznam alter column stav_stary drop not null;

-- V heslari typ_nalezu chybi heslo
update heslar set heslo = zkratka where nazev_heslare = 38;
update heslar set heslo = popis where nazev_heslare=24;

-- nepotrebne pole ktere lze odvodit z IDENT_CELY Issue 16
alter table lokalita drop column final_cj;
alter table akce drop column final_cj;

-- Pridani reference na hlavni roli uzivatele
alter table auth_user add column hlavni_role integer;
-- Vlozeni dat na zaklade auth_level
update auth_user set hlavni_role = 1 where (auth_level & 1) = 1;
update auth_user set hlavni_role = 2 where (auth_level & 2) = 2;
update auth_user set hlavni_role = 4 where (auth_level & 4) = 4;
update auth_user set hlavni_role = 3 where (auth_level & 16) = 16;
-- Vsechni ostatni jsou neaktivni uzivatele
update auth_user set hlavni_role = null, is_active = false where (auth_level & 1 != 1 and auth_level & 2 != 2 and auth_level & 4 != 4 and auth_level & 16 != 16) or auth_level is null;
-- Pridani ciziko klice na user_groups
alter table auth_user add constraint auth_user_hlavni_role foreign key (hlavni_role) references auth_group (id);
alter table projekt alter column historie set not null;
