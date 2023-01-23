
-- Jeste jsem zapomel domigrovat tranzakce akci 3 a 7 na 4
-- TODO Issue 107
-- update historie h set typ_zmeny = 4 where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=111);
UPDATE historie h SET typ_zmeny = 4 WHERE id IN (SELECT his.id AS hid FROM historie his WHERE his.vazba IN (SELECT hv.id FROM historie_vazby hv WHERE hv.typ_vazby='archeologicky_zaznam') AND his.typ_zmeny=111);
-- COMMENT: tahle query je nejaka pomala, nevim proc ... :( DN: nahrazeno alternativou;
-- update historie h set typ_zmeny = 4 where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=7);
UPDATE historie h SET typ_zmeny = 4 WHERE id IN (SELECT his.id AS hid FROM historie his WHERE his.vazba IN (SELECT hv.id FROM historie_vazby hv WHERE hv.typ_vazby='archeologicky_zaznam') AND his.typ_zmeny=7);
