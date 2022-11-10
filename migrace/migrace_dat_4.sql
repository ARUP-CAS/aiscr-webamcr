-- Migrace vsech heslaru do tabulky heslaru

-- 'heslar_aktivity'
-- 'heslar_areal_druha'
-- 'heslar_areal_prvni'
-- 'heslar_autorska_role'
-- 'heslar_dohlednost'
-- 'heslar_druh_lokality_druha'
-- 'heslar_druh_lokality_prvni'
-- 'heslar_format_dokumentu'
-- 'heslar_jazyk_dokumentu'
-- 'heslar_kulturni_pamatka'
-- 'heslar_letiste'
-- 'heslar_material_dokumentu'
-- 'heslar_nahrada'
-- 'heslar_nalezove_okolnosti'
-- 'heslar_obdobi_druha'
-- 'heslar_obdobi_prvni'
-- 'heslar_objekt_druh'
-- 'heslar_objekt_kategorie'
-- 'heslar_pocasi'
-- 'heslar_podnet'
-- 'heslar_posudek'
-- 'heslar_predmet_druh'
-- 'heslar_predmet_kategorie'
-- 'heslar_presnost'
-- 'heslar_pristupnost'
-- 'heslar_rada'
-- 'heslar_specifikace_data'
-- 'heslar_specifikace_objektu_druha'
-- 'heslar_specifikace_objektu_prvni'
-- 'heslar_specifikace_predmetu'
-- 'heslar_tvar'
-- 'heslar_typ_akce_druha'
-- 'heslar_typ_akce_prvni'
-- 'heslar_typ_dj'
-- 'heslar_typ_dokumentu'
-- 'heslar_typ_externiho_zdroje'
-- 'heslar_typ_lokality'
-- 'heslar_typ_nalezu'
-- 'heslar_typ_organizace'
-- 'heslar_typ_pian'
-- 'heslar_typ_projektu'
-- 'heslar_typ_sondy'
-- 'heslar_typ_udalosti'
-- 'heslar_typ_vyskovy_bod'
-- 'heslar_ulozeni_originalu'
-- 'heslar_zachovalost'
-- 'heslar_zeme'

-- COMMENT: ulozim si puvodin id_cka abych o ne neprisel
alter table heslar add column puvodni_id integer;
-- COMMENT: docasne odeberu not_null protoze nevim jak vygenerovat ident_cely
alter table heslar alter column ident_cely drop not null;
-- COMMENT: docasne odebrat taky not_null sloupce heslo
alter table heslar alter column heslo drop not null;

-- HESLARE KTERYM CHYBI PREKLAD
-- heslar_autorska_role
alter table heslar_autorska_role add column en text;
update heslar_autorska_role set en = 'author' where id = 1;
update heslar_autorska_role set en = 'editor' where id = 2;
-- heslar_letiste taky chybi en, nastavuji na cesky nazev letiste
alter table heslar_letiste add column en text;
update heslar_letiste set en = nazev;
-- helsar_specifikace_data TODO doplnit preklad
alter table heslar_specifikace_data add column en text;
update heslar_specifikace_data set en = 'translate: ' || ident_cely;
-- heslar_typ_organizace TODO doplnit preklad
alter table heslar_typ_organizace add column en text;
update heslar_typ_organizace set en = 'translate: ' || ident_cely;

-- COMMENT: musim odebrat key "heslar_heslo_en_key", protoze napr. preklad 'hradba' a 'val' v heslar_objekt_druh je stejny
-- stejny problem je v heslari heslar_specifikace_objektu_druha u sloupce heslo (stribro je tam 2x), to je mozna ale chyba dat
-- DN: Toto by již mělo být ošetřeno, ale pro jistotu necháme a k navrácení constraints dojde dále v migraci.
alter table heslar drop constraint heslar_heslo_en_key;
alter table heslar drop constraint heslar_heslo_key;
-- TODO pridat smazane constraints

-- vlozeni nazvu heslaru
insert into heslar_nazev(heslar) values
('heslar_aktivity'),
('heslar_areal_druha'),
('heslar_areal_prvni'),
('heslar_autorska_role'),
('heslar_dohlednost'),
('heslar_druh_lokality_druha'),
('heslar_druh_lokality_prvni'),
('heslar_format_dokumentu'),
('heslar_jazyk_dokumentu'),
('heslar_kulturni_pamatka'),
('heslar_letiste'),
('heslar_material_dokumentu'),
('heslar_nahrada'),
('heslar_nalezove_okolnosti'),
('heslar_obdobi_druha'),
('heslar_obdobi_prvni'),
('heslar_objekt_druh'),
('heslar_objekt_kategorie'),
('heslar_pocasi'),
('heslar_podnet'),
('heslar_posudek'),
('heslar_predmet_druh'),
('heslar_predmet_kategorie'),
('heslar_presnost'),
('heslar_pristupnost'),
('heslar_rada'),
('heslar_specifikace_data'),
('heslar_specifikace_objektu_druha'),
('heslar_specifikace_objektu_prvni'),
('heslar_specifikace_predmetu'),
('heslar_tvar'),
('heslar_typ_akce_druha'),
('heslar_typ_akce_prvni'),
('heslar_typ_dj'),
('heslar_typ_dokumentu'),
('heslar_typ_externiho_zdroje'),
('heslar_typ_lokality'),
('heslar_typ_nalezu'),
('heslar_typ_organizace'),
('heslar_typ_pian'),
('heslar_typ_projektu'),
('heslar_typ_sondy'),
('heslar_typ_udalosti'),
('heslar_typ_vyskovy_bod'),
('heslar_ulozeni_originalu'),
('heslar_zachovalost'),
('heslar_zeme');

-- vlozeni hodnot COMMENT: v heslari_pristupnost se mapuje jinak vyznam -> heslo
alter table heslar alter column heslo_en drop not null;
insert into heslar(puvodni_id, nazev_heslare, heslo, heslo_en, razeni, zkratka, ident_cely)
( select id, 1 as nazev_heslare, nazev, en, poradi, zkratka, ident_cely from heslar_aktivity order by id )    union
( select id, 2 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_areal_druha order by id )               union
( select id, 3 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_areal_prvni order by id )              union
( select id, 4 as nazev_heslare, nazev, en, null, zkratka, ident_cely from heslar_autorska_role order by id )              union
( select id, 5 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_dohlednost order by id)               union
( select id, 6 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_druh_lokality_druha order by id)        union
( select id, 7 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_druh_lokality_prvni order by id)        union
( select id, 8 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_format_dokumentu order by id)           union
( select id, 9 as nazev_heslare, null, en, poradi, nazev, ident_cely from heslar_jazyk_dokumentu order by id)            union
( select id, 10 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_kulturni_pamatka order by id)          union
( select id, 11 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_letiste  order by id)                   union
( select id, 12 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_material_dokumentu  order by id)        union
( select id, 13 as nazev_heslare, null, en, poradi, nazev, ident_cely from heslar_nahrada  order by id)                   union
( select id, 14 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_nalezove_okolnosti  order by id)      union
( select id, 15 as nazev_heslare, nazev, en, poradi, zkratka, ident_cely from heslar_obdobi_druha  order by id)           union
( select id, 16 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_obdobi_prvni  order by id)         union
( select id, 17 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_objekt_druh  order by id)          union
( select id, 18 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_objekt_kategorie order by id)       union
( select id, 19 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_pocasi order by id)               union
( select id, 20 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_podnet order by id)                union
( select id, 21 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_posudek order by id)               union
( select id, 22 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_predmet_druh  order by id)            union
( select id, 23 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_predmet_kategorie order by id)        union
( select id, 24 as nazev_heslare, null, en, null, nazev, ident_cely from heslar_presnost order by id )                   union
( select id, 25 as nazev_heslare, vyznam, en, null, nazev, ident_cely from heslar_pristupnost order by id )               union
( select id, 26 as nazev_heslare, vysvetlivka, en, null, nazev, ident_cely from heslar_rada order by id )                      union
( select id, 27 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_specifikace_data order by id )          union
( select id, 28 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_specifikace_objektu_druha order by id ) union
( select id, 29 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_specifikace_objektu_prvni order by id)  union
( select id, 30 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_specifikace_predmetu order by id )      union
( select id, 31 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_tvar  order by id)                      union
( select id, 32 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_akce_druha order by id  )           union
( select id, 33 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_akce_prvni  order by id )           union
( select id, 34 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_dj order by id )                     union
( select id, 35 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_dokumentu order by id )             union
( select id, 36 as nazev_heslare, nazev, en, null, vysvetlivka, ident_cely from heslar_typ_externiho_zdroje order by id )      union
( select id, 37 as nazev_heslare, nazev, en, poradi, nazev_id, ident_cely from heslar_typ_lokality order by id )              union
( select id, 38 as nazev_heslare, null, en, null, nazev, ident_cely from heslar_typ_nalezu order by id )                union
( select id, 39 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_organizace order by id )            union
( select id, 40 as nazev_heslare, nazev, en, null, null, ident_cely from heslar_typ_pian order by id )                  union
( select id, 41 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_projektu order by id )              union
( select id, 42 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_sondy  order by id  )               union
( select id, 43 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_udalosti order by id   )            union
( select id, 44 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_typ_vyskovy_bod order by id )           union
( select id, 45 as nazev_heslare, nazev, en, poradi, null, ident_cely from heslar_ulozeni_originalu  order by id )        union
( select id, 46 as nazev_heslare, null, en, poradi, nazev, ident_cely from heslar_zachovalost order by id )               union
( select id, 47 as nazev_heslare, nazev, nazev_en, poradi, kod, ident_cely from heslar_zeme order by id ) order by nazev_heslare, id;

-- Pridani popisu u nasledujicich heslaru
-- heslar_areal_druha
update heslar set popis = sel.napoveda from (select id, napoveda from heslar_areal_druha where napoveda != '') sel where puvodni_id = sel.id and nazev_heslare = 2;
-- heslar_areal_prvni COMMENT: tady nic neni
update heslar set popis = sel.napoveda from (select id, napoveda from heslar_areal_prvni where napoveda != '') sel where puvodni_id = sel.id and nazev_heslare = 3;
-- heslar_druh_lokality_druha COMMENT: taky nic neni
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_druh_lokality_druha where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 6;
-- heslar_nahrada
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_nahrada where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 13;
-- heslar_nalezove_okolnosti COMMENT: tady nic neni
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_nalezove_okolnosti where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 14;
-- heslar_obdobi_druha
update heslar set popis = sel.napoveda from (select id, napoveda from heslar_obdobi_druha where napoveda != '') sel where puvodni_id = sel.id and nazev_heslare = 15;
-- heslar_presnost
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_presnost where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 24;
-- heslar_specifikace_data
update heslar set popis = sel.poznamka from (select id, poznamka from heslar_specifikace_data where poznamka != '') sel where puvodni_id = sel.id and nazev_heslare = 27;
-- heslar_tvar
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_tvar where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 31;
-- heslar_typ_akce_druha
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_typ_akce_druha where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 32;
-- heslar_ulozeni_originalu
update heslar set popis = sel.poznamka from (select id, poznamka from heslar_ulozeni_originalu where poznamka != '') sel where puvodni_id = sel.id and nazev_heslare = 45;
-- heslar_zachovalost
update heslar set popis = sel.vysvetlivka from (select id, vysvetlivka from heslar_zachovalost where vysvetlivka != '') sel where puvodni_id = sel.id and nazev_heslare = 46;

-- hierarchie
-- podrizenost
-- heslar_areal_druha
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_areal_druha ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 2) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 3;
-- heslar_druh_lokality_druha
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_druh_lokality_druha ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 6) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 7;
-- heslar_obdobi_druha
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_obdobi_druha ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 15) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 16;
-- heslar_objekt_druh
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_objekt_druh ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 17) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 18;
-- heslar_predmet_druh
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_predmet_druh ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 22) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 23;
-- heslar_specifikace_objektu_druha
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_specifikace_objektu_druha ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 28) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 29;
-- heslar_typ_akce_druha
insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select h.id, sel.heslo_podrazene, 'podřízenost' from heslar h join (select ha.prvni as prvni_puvodni_id, h.id as heslo_podrazene from heslar_typ_akce_druha ha join heslar h on h.puvodni_id = ha.id and h.nazev_heslare = 32) sel on sel.prvni_puvodni_id = h.puvodni_id and h.nazev_heslare = 33;
-- migarce relaci typu vychozi hodnota a uplatneni

-- heslar_material_dokumentu (relace s heslar_typ_dokumentu)
alter table heslar_material_dokumentu add column nove_id integer;
update heslar_material_dokumentu set nove_id = sel.new_id from (select id as new_id, puvodni_id as old_id from heslar h where h.nazev_heslare = 12) as sel where sel.old_id = id;
-- DN: pro jistotu navýšen counter na 50, aby byla rezerva
CREATE OR REPLACE FUNCTION migrateUplatneniFromMaterialDokumentu() RETURNS void AS $$
DECLARE
BEGIN
    FOR counter IN 1..50
    LOOP
        RAISE NOTICE '%', counter;
        BEGIN
            insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select a.nove_id, h.id, 'uplatnění' from heslar_material_dokumentu a join heslar_typ_dokumentu r on r.id = split_part(a.uplatneni, ';', counter)::INTEGER join heslar h on h.puvodni_id = split_part(a.uplatneni, ';', counter)::INTEGER and h.nazev_heslare = 35 where split_part(a.uplatneni, ';', counter) != '';
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
select migrateUplatneniFromMaterialDokumentu();
drop function migrateUplatneniFromMaterialDokumentu();

alter table heslar_material_dokumentu drop column nove_id;

-- heslar_nahrada (relace s heslar_rada) COMMENT: Po diskuzi s Davidem nakonec neni protreba migrovat
-- heslar_predmet_druh (relace s heslar_specifikace_predmetu)

insert into heslar_hierarchie(heslo_nadrazene, heslo_podrazene, typ) select hes.id, sel.material_id, 'výchozí hodnota' from heslar hes join (select h.id as material_id, pd.id as predmet_id from heslar h join heslar_specifikace_predmetu sp on sp.id = h.puvodni_id and h.nazev_heslare = 30 join heslar_predmet_druh pd on pd.implicitni_material = sp.id) as sel on sel.predmet_id = hes.puvodni_id and hes.nazev_heslare = 22;

-- heslar_zachovalost (realce s heslar_rada) COMMENT: Po diskuzi s Davidem nakonec neni protreba migrovat

-- TODO: zmigrovat typy "uplatneni" z heslar_format_dokumentu a heslar_typ_dokumentu

-- Precislovani referenci ze starych heslaru na nove ID-cka z jednoho heslare

--1. akce.specifikace_data -> heslar (heslar_specifikace_data = 27)
alter table akce drop constraint akce_specifikace_data_fkey;
update akce set specifikace_data = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 27) sel where specifikace_data = sel.puvodni;
alter table akce add constraint akce_specifikace_data_fkey foreign key (specifikace_data) references heslar(id);
--2. akce.hlavni_typ -> heslar (heslar_typ_akce_druha = 32)
alter table akce drop constraint akce_hlavni_typ_fkey;
update akce set hlavni_typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 32) sel where hlavni_typ = sel.puvodni;
alter table akce add constraint akce_hlavni_typ_fkey foreign key (hlavni_typ) references heslar(id);
--3. akce.vedlejsi_typ -> heslar (heslar_typ_akce_druha = 32)
alter table akce drop constraint akce_vedlejsi_typ_fkey;
update akce set vedlejsi_typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 32) sel where vedlejsi_typ = sel.puvodni;
alter table akce add constraint akce_vedlejsi_typ_fkey foreign key (vedlejsi_typ) references heslar(id);
--4. akce.pristupnost -> heslar (heslar_pristupnost = 25)
alter table akce drop constraint akce_pristupnost_fkey;
update akce set pristupnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 25) sel where pristupnost = sel.puvodni;
alter table akce add constraint akce_pristupnost_fkey foreign key (pristupnost) references heslar(id);
--5. adb.typ_sondy -> heslar (heslar_typ_sondy = 42)
alter table adb drop constraint archeologicky_dokumentacni_bod_typ_sondy_fkey;
update adb set typ_sondy = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 42) sel where typ_sondy = sel.puvodni;
alter table adb add constraint adb_typ_sondy_fkey foreign key (typ_sondy) references heslar(id);
--6. adb.podnet -> heslar (heslar_podnet = 20)
alter table adb drop constraint archeologicky_dokumentacni_bod_podnet_fkey;
update adb set podnet = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 20) sel where podnet = sel.puvodni;
alter table adb add constraint adb_podnet_fkey foreign key (podnet) references heslar(id);
--7. dokument.rada -> heslar (heslar_rada = 26)
alter table dokument drop constraint dokument_rada_fkey;
update dokument set rada = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 26) sel where rada = sel.puvodni;
alter table dokument add constraint dokument_rada_fkey foreign key (rada) references heslar(id);
--8. dokument.typ_dokumentu -> heslar (heslar_typ_dokumentu = 35)
alter table dokument drop constraint dokument_typ_dokumentu_fkey;
update dokument set typ_dokumentu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 35) sel where typ_dokumentu = sel.puvodni;
alter table dokument add constraint dokument_typ_dokumentu_fkey foreign key (typ_dokumentu) references heslar(id);
--9. dokument.pristupnost -> heslar (heslar_pristupnost = 25)
alter table dokument drop constraint dokument_pristupnost_fkey;
update dokument set pristupnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 25) sel where pristupnost = sel.puvodni;
alter table dokument add constraint dokument_pristupnost_fkey foreign key (pristupnost) references heslar(id);
--10. dokument.material_originalu -> heslar (heslar_material_dokumentu = 12)
alter table dokument drop constraint dokument_material_originalu_fkey;
update dokument set material_originalu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 12) sel where material_originalu = sel.puvodni;
alter table dokument add constraint dokument_material_originalu_fkey foreign key (material_originalu) references heslar(id);
--11. dokument.ulozeni_originalu -> heslar (heslar_ulozeni_originalu = 45)
alter table dokument drop constraint dokument_ulozeni_originalu_fkey;
update dokument set ulozeni_originalu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 45) sel where ulozeni_originalu = sel.puvodni;
alter table dokument add constraint dokument_ulozeni_originalu_fkey foreign key (ulozeni_originalu) references heslar(id);
--12. dokument_extra_data.zachovalost -> heslar (heslar_zachovalost = 46)
alter table dokument_extra_data drop constraint extra_data_zachovalost_fkey;
update dokument_extra_data set zachovalost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 46) sel where zachovalost = sel.puvodni;
alter table dokument_extra_data add constraint dokument_extra_data_zachovalost_fkey foreign key (zachovalost) references heslar(id);
--13. dokument_extra_data.nahrada -> heslar (heslar_nahrada = 13)
alter table dokument_extra_data drop constraint extra_data_nahrada_fkey;
update dokument_extra_data set nahrada = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 13) sel where nahrada = sel.puvodni;
alter table dokument_extra_data add constraint dokument_extra_data_nahrada_fkey foreign key (nahrada) references heslar(id);
--14. dokument_extra_data.format -> heslar (heslar_format_dokumentu = 8)
alter table dokument_extra_data drop constraint extra_data_format_fkey;
update dokument_extra_data set format = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 8) sel where format = sel.puvodni;
alter table dokument_extra_data add constraint dokument_extra_data_format_fkey foreign key (format) references heslar(id);
--15. dokument_extra_data.zeme -> heslar (heslar_zeme = 47)
alter table dokument_extra_data drop constraint extra_data_zeme_fkey;
update dokument_extra_data set zeme = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 47) sel where zeme = sel.puvodni;
alter table dokument_extra_data add constraint dokument_extra_data_zeme_fkey foreign key (zeme) references heslar(id);
--16. dokument_extra_data.udalost_typ -> heslar (heslar_typ_udalosti = 43) COMMENT: Tady nic neni
alter table dokument_extra_data drop constraint extra_data_udalost_typ_fkey;
update dokument_extra_data set udalost_typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 43) sel where udalost_typ = sel.puvodni;
alter table dokument_extra_data add constraint dokument_extra_data_udalost_typ_fkey foreign key (udalost_typ) references heslar(id);
--17. dokument_jazyk.jazyk -> heslar (heslar_jazyk_dokumentu = 9)
alter table dokument_jazyk drop constraint dokument_jazyk_jazyk_fk;
update dokument_jazyk set jazyk = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 9) sel where jazyk = sel.puvodni;
alter table dokument_jazyk add constraint dokument_jazyk_jazyk_fkey foreign key (jazyk) references heslar(id);
--18. dokument_posudek.posudek -> heslar (heslar_posudek = 21)
alter table dokument_posudek drop constraint dokument_posudek_posudek_fk;
update dokument_posudek set posudek = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 21) sel where posudek = sel.puvodni;
alter table dokument_posudek add constraint dokument_posudek_posudek_fkey foreign key (posudek) references heslar(id);
--19. dokumentacni_jednotka.typ -> heslar (heslar_typ_dj = 34)
alter table dokumentacni_jednotka drop constraint dj_typ_fkey;
update dokumentacni_jednotka set typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 34) sel where typ = sel.puvodni;
alter table dokumentacni_jednotka add constraint dokumentacni_jednotka_typ_fkey foreign key (typ) references heslar(id);
--20. externi_zdroj.typ -> heslar  (heslar_typ_externiho_zdroje = 36)
alter table externi_zdroj drop constraint externi_zdroj_typ_fkey;
update externi_zdroj set typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 36) sel where typ = sel.puvodni;
alter table externi_zdroj add constraint externi_zdroj_typ_fkey foreign key (typ) references heslar(id);
--21. externi_zdroj.typ_dokumentu -> heslar (heslar_typ_dokumentu = 35)
alter table externi_zdroj drop constraint externi_zdroj_typ_dokumentu_fkey;
update externi_zdroj set typ_dokumentu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 35) sel where typ_dokumentu = sel.puvodni;
alter table externi_zdroj add constraint externi_zdroj_typ_dokumentu_fkey foreign key (typ_dokumentu) references heslar(id);
--22. heslar_dokument_typ_material_rada.dokument_rada -> heslar (heslar_rada = 26)
alter table heslar_dokument_typ_material_rada drop constraint heslar_typ_material_rada_heslar_rada_id_fkey;
update heslar_dokument_typ_material_rada set dokument_rada = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 26) sel where dokument_rada = sel.puvodni;
alter table heslar_dokument_typ_material_rada add constraint heslar_dokument_typ_material_rada_dokument_rada_fkey foreign key (dokument_rada) references heslar(id);
--23. heslar_dokument_typ_material_rada.dokument_typ -> heslar (heslar_typ_dokumentu = 35)
alter table heslar_dokument_typ_material_rada drop constraint heslar_typ_material_rada_heslar_typ_dokumentu_id_fkey;
update heslar_dokument_typ_material_rada set dokument_typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 35) sel where dokument_typ = sel.puvodni;
alter table heslar_dokument_typ_material_rada add constraint heslar_dokument_typ_material_rada_dokument_typ_fkey foreign key (dokument_typ) references heslar(id);
--24. heslar_dokument_typ_material_rada.dokument_material -> heslar (heslar_material_dokumentu = 12)
alter table heslar_dokument_typ_material_rada drop constraint heslar_typ_material_rada_heslar_material_dokumentu_id_fkey;
update heslar_dokument_typ_material_rada set dokument_material = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 12) sel where dokument_material = sel.puvodni;
alter table heslar_dokument_typ_material_rada add constraint heslar_dokument_typ_material_rada_dokument_material_fkey foreign key (dokument_material) references heslar(id);
--25. komponenta.obdobi -> heslar (heslar_obdobi_druha = 15)
alter table komponenta drop constraint komponenta_kultura_fkey;
update komponenta set obdobi = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 15) sel where obdobi = sel.puvodni;
alter table komponenta add constraint komponenta_obdobi_fkey foreign key (obdobi) references heslar(id);
--26. komponenta.areal -> heslar (heslar_areal_druha = 2)
alter table komponenta drop constraint komponenta_areal_fkey;
update komponenta set areal = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 2) sel where areal = sel.puvodni;
alter table komponenta add constraint komponenta_areal_fkey foreign key (areal) references heslar(id);
--27. komponenta_aktivita.aktivita -> heslar (heslar_aktivity = 1)
alter table komponenta_aktivita drop constraint komponenta_aktivita_aktivita_fk;
alter table komponenta_aktivita rename column aktivita to aktivita_old;
alter table komponenta_aktivita add column aktivita integer;
update komponenta_aktivita set aktivita = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 1) sel where aktivita_old = sel.puvodni;
alter table komponenta_aktivita add constraint komponenta_aktivita_aktivita_fkey foreign key (aktivita) references heslar(id);
alter table komponenta_aktivita drop constraint komponenta_aktivita_pkey;
alter table komponenta_aktivita add constraint komponenta_aktivita_pkey primary key (komponenta, aktivita);
alter table komponenta_aktivita drop column aktivita_old;
--28. let.letiste_start -> heslar (heslar_letiste = 11)
alter table let drop constraint let_letiste_start_fkey;
update let set letiste_start = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 11) sel where letiste_start = sel.puvodni;
alter table let add constraint let_letiste_start_fkey foreign key (letiste_start) references heslar(id);
--29. let.letiste_cil -> heslar (heslar_letiste = 11)
alter table let drop constraint let_letiste_cil_fkey;
update let set letiste_cil = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 11) sel where letiste_cil = sel.puvodni;
alter table let add constraint let_letiste_cil_fkey foreign key (letiste_cil) references heslar(id);
--30. let.pocasi -> heslar (heslar_pocasi = 19)
alter table let drop constraint let_pocasi_fkey;
update let set pocasi = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 19) sel where pocasi = sel.puvodni;
alter table let add constraint let_pocasi_fkey foreign key (pocasi) references heslar(id);
--31. let.dohlednost -> heslar (heslar_dohlednost = 5)
alter table let drop constraint let_dohlednost_fkey;
update let set dohlednost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 5) sel where dohlednost = sel.puvodni;
alter table let add constraint let_dohlednost_fkey foreign key (dohlednost) references heslar(id);
--32. lokalita.druh -> heslar (heslar_druh_lokality_druha = 6)
alter table lokalita drop constraint lokalita_druh_fkey;
update lokalita set druh = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 6) sel where druh = sel.puvodni;
alter table lokalita add constraint lokalita_druh_fkey foreign key (druh) references heslar(id);
--33. lokalita.typ_lokality -> heslar (heslar_typ_lokality = 37)
alter table lokalita drop constraint lokalita_typ_lokality_fkey;
update lokalita set typ_lokality = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 37) sel where typ_lokality = sel.puvodni;
alter table lokalita add constraint lokalita_typ_lokality_fkey foreign key (typ_lokality) references heslar(id);
--34. lokalita.pristupnost -> heslar (heslar_pristupnost = 25)
alter table lokalita drop constraint lokalita_pristupnost_fkey;
update lokalita set pristupnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 25) sel where pristupnost = sel.puvodni;
alter table lokalita add constraint lokalita_pristupnost_fkey foreign key (pristupnost) references heslar(id);
--35. nalez.druh_nalezu -> heslar (COMMENT: MIGRACE momentalne ukazuje na 2 ruzne heslare, je potreba podle typu nalezu namapovat na spravny zaznam v novem heslari) (heslar_predmet_druh = 22, heslar_objekt_druh = 17)

--!!!! SPATNE update nalez set druh_nalezu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 22) sel where druh_nalezu = sel.puvodni;
--!!!! SPATNE update nalez set druh_nalezu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 17) sel where druh_nalezu = sel.puvodni;

-- DOBRE:
UPDATE nalez AS n SET druh_nalezu = h.id FROM heslar AS h WHERE h.puvodni_id = n.druh_nalezu and h.nazev_heslare = 22 and n.typ_nalezu = 2;
UPDATE nalez AS n SET druh_nalezu = h.id FROM heslar AS h WHERE h.puvodni_id = n.druh_nalezu and h.nazev_heslare = 17 and n.typ_nalezu = 1;

alter table nalez add constraint nalez_druh_nalezu_fkey foreign key (druh_nalezu) references heslar(id);
--36. nalez.specifikace -> heslar (COMMENT: MIGRACE momentalne ukazuje na 2 ruzne heslare, je potreba podle typu nalezu namapovat na spravny zaznam v novem heslari) (heslar_specifikace_objektu_druha = 28, heslar_specifikace_predmetu = 30)

--!!!! SPATNE update nalez set specifikace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 28) sel where specifikace = sel.puvodni;
--!!!! SPATNE update nalez set specifikace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 30) sel where specifikace = sel.puvodni;

--DOBRE:
UPDATE nalez AS n SET specifikace = h.id FROM heslar AS h WHERE h.puvodni_id = n.specifikace and h.nazev_heslare = 30 and n.typ_nalezu = 2;
UPDATE nalez AS n SET specifikace = h.id FROM heslar AS h WHERE h.puvodni_id = n.specifikace and h.nazev_heslare = 28 and n.typ_nalezu = 1;

-- COMMENT: specifikace ktere jsou -1 ted budou null kvuli foreign key constrainu
update nalez set specifikace = null where specifikace = -1;
alter table nalez add constraint nalez_specifikace_fkey foreign key (specifikace) references heslar(id);
--37. organizace.typ_organizace -> heslar (heslar_typ_organizace = 39)
alter table organizace drop constraint organizace_typ_organizace_fkey;
update organizace set typ_organizace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 39) sel where typ_organizace = sel.puvodni;
alter table organizace add constraint organizace_typ_organizace_fkey foreign key (typ_organizace) references heslar(id);
--38. organizace.zverejneni_pristupnost -> heslar (heslar_pristupnost = 25)
alter table organizace drop constraint organizace_published_accessibility_fkey;
update organizace set zverejneni_pristupnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 25) sel where zverejneni_pristupnost = sel.puvodni;
alter table organizace add constraint organizace_zverejneni_pristupnost_fkey foreign key (zverejneni_pristupnost) references heslar(id);
--39. pian.presnost -> heslar (heslar_presnost = 24)
alter table pian drop constraint pian_presnost_fkey;
update pian set presnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 24) sel where presnost = sel.puvodni;
alter table pian add constraint pian_presnost_fkey foreign key (presnost) references heslar(id);
--40. pian.typ -> heslar (heslar_typ_pian = 40)
alter table pian drop constraint pian_typ_fkey;
update pian set typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 40) sel where typ = sel.puvodni;
alter table pian add constraint pian_typ_fkey foreign key (typ) references heslar(id);
--41. projekt.typ_projektu -> heslar (heslar_typ_projektu = 41)
alter table projekt drop constraint projekt_typ_projektu_fkey;
update projekt set typ_projektu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 41) sel where typ_projektu = sel.puvodni;
alter table projekt add constraint projekt_typ_projektu_fkey foreign key (typ_projektu) references heslar(id);
--42. projekt.kulturni_pamatka -> heslar (heslar_kulturni_pamatka = 10)
alter table projekt drop constraint projekt_kulturni_pamatka_fkey;
update projekt set kulturni_pamatka = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 10) sel where kulturni_pamatka = sel.puvodni;
alter table projekt add constraint projekt_kulturni_pamatka_fkey foreign key (kulturni_pamatka) references heslar(id);
--43. samostatny_nalez.okolnosti -> heslar  (heslar_nalezove_okolnosti = 14)
alter table samostatny_nalez drop constraint samostany_nalez_okolnosti_fkey;
update samostatny_nalez set okolnosti = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 14) sel where okolnosti = sel.puvodni;
alter table samostatny_nalez add constraint samostatny_nalez_okolnosti_fkey foreign key (okolnosti) references heslar(id);
--44. samostatny_nalez.pristupnost -> heslar (heslar_pristupnost = 25)
alter table samostatny_nalez drop constraint samostany_nalez_pristupnost_fkey;
update samostatny_nalez set pristupnost = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 25) sel where pristupnost = sel.puvodni;
alter table samostatny_nalez add constraint samostatny_nalez_pristupnost_fkey foreign key (pristupnost) references heslar(id);
--45. samostatny_nalez.obdobi -> heslar (heslar_obdobi_druha = 15)
alter table samostatny_nalez drop constraint samostany_nalez_obdobi_fkey;
update samostatny_nalez set obdobi = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 15) sel where obdobi = sel.puvodni;
alter table samostatny_nalez add constraint samostatny_nalez_obdobi_fkey foreign key (obdobi) references heslar(id);
--46. samostatny_nalez.druh_nalezu -> heslar (heslar_predmet_druh = 22)
alter table samostatny_nalez drop constraint samostany_nalez_druh_fkey;
update samostatny_nalez set druh_nalezu = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 22) sel where druh_nalezu = sel.puvodni;
alter table samostatny_nalez add constraint samostatny_nalez_druh_nalezu_fkey foreign key (druh_nalezu) references heslar(id);
--47. samostatny_nalez.specifikace -> heslar (heslar_specifikace_predmetu = 30)
alter table samostatny_nalez drop constraint samostany_nalez_specifikace_fkey;
update samostatny_nalez set specifikace = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 30) sel where specifikace = sel.puvodni;
alter table samostatny_nalez add constraint samostatny_nalez_specifikace_fkey foreign key (specifikace) references heslar(id);
--48. tvar.tvar -> heslar (heslar_tvar = 31)
alter table tvar drop constraint tvar_tvar_fkey;
update tvar set tvar = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 31) sel where tvar = sel.puvodni;
alter table tvar add constraint tvar_tvar_fkey foreign key (tvar) references heslar(id);
--49. vyskovy_bod.typ -> heslar (heslar_typ_vyskovy_bod = 44)
alter table vyskovy_bod drop constraint vyskovy_bod_typ_fkey;
update vyskovy_bod set typ = sel.new_id from (select id as new_id, puvodni_id as puvodni from heslar where nazev_heslare = 44) sel where typ = sel.puvodni;
alter table vyskovy_bod add constraint vyskovy_bod_typ_fkey foreign key (typ) references heslar(id);
