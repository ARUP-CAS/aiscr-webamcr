alter table soubor drop constraint if exists soubor_filepath_key;
-- update historie uzivatel_spoluprce typ vazby na nove hodnoty
UPDATE historie hi
SET typ_zmeny = 'SP01'
FROM historie_vazby hv
where hi.vazba = hv.id
    and hv.typ_vazby = 'uzivatel_spoluprace'
    and hi.typ_zmeny_old = 1;
UPDATE historie hi
SET typ_zmeny = 'SP12'
FROM historie_vazby hv
where hi.vazba = hv.id
    and hv.typ_vazby = 'uzivatel_spoluprace'
    and hi.typ_zmeny_old = 2;
UPDATE historie hi
SET typ_zmeny = 'SP-1'
FROM historie_vazby hv
where hi.vazba = hv.id
    and hv.typ_vazby = 'uzivatel_spoluprace'
    and hi.typ_zmeny_old = 3;
UPDATE historie hi
SET typ_zmeny = 'SP12'
FROM historie_vazby hv
where hi.vazba = hv.id
    and hv.typ_vazby = 'uzivatel_spoluprace'
    and hi.typ_zmeny_old = 4;
