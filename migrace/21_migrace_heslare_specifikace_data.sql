-- Migrace dle issue #36

-- Zaloha sloupcu pred migraci
alter table akce rename column datum_ukonceni to datum_ukonceni_old;
alter table akce rename column datum_zahajeni to datum_zahajeni_old;
alter table akce add column specifikace_data_zaloha integer;
update akce set specifikace_data_zaloha = specifikace_data;

alter table akce rename column datum_zahajeni_v to datum_zahajeni;
alter table akce rename column datum_ukonceni_v to datum_ukonceni;

-- přesně -> přesně
-- před rokem -> někdy v letech
-- po roce -> někdy v letech
-- kolem -> někdy v letech
-- neznámo -> někdy v letech
-- v letech -> přesně v letech
-- v roce -> přesně v letech

-- 2 zaznamy predelam na spravny typ, presne zustava a zbytek smazu
update heslar set heslo = 'někdy v letech' where nazev_heslare = 27 and heslo = 'před rokem';
update heslar set heslo = 'přesně v letech' where nazev_heslare = 27 and heslo = 'v roce';

-- MIGRACE referenci
-- po roce -> nekdy v letech
update akce set specifikace_data = sel.new_id from (select id as new_id from heslar where heslo = 'někdy v letech') sel where archeologicky_zaznam in (select a.archeologicky_zaznam from akce a join heslar h on h.id = a.specifikace_data where h.heslo = 'po roce');
-- kolem -> nekdy v letech
update akce set specifikace_data = sel.new_id from (select id as new_id from heslar where heslo = 'někdy v letech') sel where archeologicky_zaznam in (select a.archeologicky_zaznam from akce a join heslar h on h.id = a.specifikace_data where h.heslo = 'kolem');
-- neznamo -> nekdy v letech
update akce set specifikace_data = sel.new_id from (select id as new_id from heslar where heslo = 'někdy v letech') sel where archeologicky_zaznam in (select a.archeologicky_zaznam from akce a join heslar h on h.id = a.specifikace_data where h.heslo = 'neznámo');
-- v letech -> presne v letech
update akce set specifikace_data = sel.new_id from (select id as new_id from heslar where heslo = 'přesně v letech') sel where archeologicky_zaznam in (select a.archeologicky_zaznam from akce a join heslar h on h.id = a.specifikace_data where h.heslo = 'v letech');

-- SMAZANI NEPOTREBNYCH ZAZNAMU Z HESLARE - dlouhy dotaz, nevim proc
delete from heslar where (heslo = 'po roce' or heslo = 'kolem' or heslo = 'neznámo' or heslo = 'v letech') and nazev_heslare = 27;

-- Uprava razeni
update heslar set razeni  = 1 where (heslo = 'přesně' AND nazev_heslare = 27);
update heslar set razeni  = 2 where (heslo = 'přesně v letech' AND nazev_heslare = 27);
update heslar set razeni  = 3 where (heslo = 'někdy v letech' AND nazev_heslare = 27);

-- Zmena 1000-01-01 na 1800-01-01
update akce set datum_zahajeni = '1800-01-01' where datum_zahajeni  = '1000-01-01';

-- MAZANI ZALOHOVYCH SLOUPCU
alter table akce drop datum_ukonceni_old;
alter table akce drop datum_zahajeni_old;
alter table akce drop specifikace_data_zaloha;
