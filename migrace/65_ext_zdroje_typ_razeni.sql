update externi_zdroj ez
set organizace = null
where organizace = '-1'
    or organizace = '';
alter table externi_zdroj
alter column organizace type INT using organizace::integer;
alter table externi_zdroj
add CONSTRAINT externi_zdroj_organizace_fkey FOREIGN KEY(organizace) REFERENCES organizace(id) ON UPDATE CASCADE ON DELETE NO ACTION;
update heslar h
set razeni = c.rowNum
from (
        SELECT T2.id,
            row_number() over (
                order by T2.heslo asc
            ) rowNum
        from heslar T2
        where T2.nazev_heslare = 36
    ) c
where h.id = c.id;
