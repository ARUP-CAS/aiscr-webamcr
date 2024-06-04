-- Odstraneni souboru bez vazby
WITH navic_soubory AS
  (SELECT distinct(sv.id) AS soubor_id,
          sv.typ_vazby,
          d.id
   FROM soubor s
   JOIN soubor_vazby sv ON s.vazba = sv.id
   LEFT JOIN dokument d ON d.soubory = sv.id
   WHERE d.id IS NULL
     AND sv.typ_vazby = 'dokument' )
DELETE
FROM soubor s2
WHERE s2.vazba in
    (SELECT soubor_id
     FROM navic_soubory);
WITH navic_soubory AS
    (SELECT distinct(sv.id) AS soubor_id,
            sv.typ_vazby,
            d.id
     FROM soubor s
     JOIN soubor_vazby sv ON s.vazba = sv.id
     LEFT JOIN projekt d ON d.soubory = sv.id
     WHERE d.id IS NULL
       AND sv.typ_vazby = 'projekt' )
  DELETE
  FROM soubor s2 WHERE s2.vazba in
    (SELECT soubor_id
     FROM navic_soubory);
WITH navic_soubory AS
    (SELECT distinct(sv.id) AS soubor_id,
            sv.typ_vazby,
            sn.id
     FROM soubor s
     JOIN soubor_vazby sv ON s.vazba = sv.id
     LEFT JOIN samostatny_nalez sn ON sn.soubory = sv.id
     WHERE sn.id IS NULL
       AND sv.typ_vazby = 'samostatny_nalez' )
  DELETE
  FROM soubor s2 WHERE s2.vazba in
    (SELECT soubor_id
     FROM navic_soubory);
        
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
