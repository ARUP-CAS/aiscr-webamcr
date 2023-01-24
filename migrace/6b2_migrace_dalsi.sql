-- COMMENT: tahle query je nejaka pomala, nevim proc ... :( DN: nahrazeno alternativou;
-- update historie h set typ_zmeny = 4 where id in (select his.id as hid from historie his join historie_vazby as hv on hv.id=his.vazba where hv.typ_vazby='archeologicky_zaznam' and his.typ_zmeny=7);
UPDATE historie h SET typ_zmeny = 4
FROM historie_vazby hv
WHERE hv.typ_vazby='archeologicky_zaznam'
AND h.vazba = hv.id
AND hv.typ_zmeny = 7;
