WITH zrus AS
(
    SELECT DISTINCT pr.historie FROM projekt pr
    JOIN historie h ON pr.historie = h.vazba
    WHERE pr.stav = 1 AND h.typ_zmeny in ('PX0', 'PX1') AND h.datum_zmeny < (now() - interval '3 year') AND upper(pr.planovane_zahajeni) < (now() - interval '1 year')
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny)
SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), 'Automatické zrušení projektů starších tří let, u kterých již nelze očekávat zahájení.', zrus.historie, 'P18'
FROM zrus;

WITH zrus AS
(
    SELECT DISTINCT pr.ident_cely FROM projekt pr
    JOIN historie h ON pr.historie = h.vazba
    WHERE pr.stav = 1 AND h.typ_zmeny in ('PX0', 'PX1') AND h.datum_zmeny < (now() - interval '3 year') AND upper(pr.planovane_zahajeni) < (now() - interval '1 year')
)
UPDATE projekt SET stav = 8 FROM zrus WHERE projekt.ident_cely = zrus.ident_cely;
