-- Odstraneni souboru bez vazby
with navic_soubory as (
        select distinct(sv.id) as soubor_id,
                sv.typ_vazby,
                d.id
        from soubor s
                join soubor_vazby sv on s.vazba = sv.id
                left join dokument d on d.soubory = sv.id
        where d.id is null
                and sv.typ_vazby = 'dokument'
)
delete from soubor s2
where s2.vazba in (
                select soubor_id
                from navic_soubory
        ) with navic_soubory as (
                select distinct(sv.id) as soubor_id,
                        sv.typ_vazby,
                        d.id
                from soubor s
                        join soubor_vazby sv on s.vazba = sv.id
                        left join projekt d on d.soubory = sv.id
                where d.id is null
                        and sv.typ_vazby = 'projekt'
        )
delete from soubor s2
where s2.vazba in (
                select soubor_id
                from navic_soubory
        ) with navic_soubory as (
                select distinct(sv.id) as soubor_id,
                        sv.typ_vazby,
                        sn.id
                from soubor s
                        join soubor_vazby sv on s.vazba = sv.id
                        left join samostatny_nalez sn on sn.soubory = sv.id
                where sn.id is null
                        and sv.typ_vazby = 'samostatny_nalez'
        )
delete from soubor s2
where s2.vazba in (
                select soubor_id
                from navic_soubory
        );
        
--update razeni pri pristupnost heslare
update heslar h
set razeni = c.rowNum
from (
                SELECT T2.id,
                        row_number() over (
                                order by T2.heslo asc
                        ) rowNum
                from heslar T2
                where T2.nazev_heslare = 25
        ) c
where h.id = c.id;
