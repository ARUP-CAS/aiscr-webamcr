# Zrušení starých projektů (cron.cancel_old_projects)
WITH zrus AS (
	SELECT DISTINCT pr.historie FROM projekt pr
		JOIN historie h ON pr.historie = h.vazba
	WHERE pr.stav = 1 AND pr.typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136') AND h.typ_zmeny in ('PX0', 'PX1') AND h.datum_zmeny < (now() - INTERVAL '3 year') AND upper(pr.planovane_zahajeni) < (now() - interval '1 year')
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny)
SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), 'Automatické zrušení projektů starších tří let, u kterých již nelze očekávat zahájení.', zrus.historie, 'P18'
FROM zrus;

WITH zrus AS (
	SELECT DISTINCT pr.ident_cely FROM projekt pr
    		JOIN historie h ON pr.historie = h.vazba
	WHERE pr.stav = 1 AND pr.typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136') AND h.typ_zmeny in ('PX0', 'PX1') AND h.datum_zmeny < (now() - INTERVAL '3 year') AND upper(pr.planovane_zahajeni) < (now() - interval '1 year')
)
UPDATE projekt SET stav = 8 FROM zrus WHERE projekt.ident_cely = zrus.ident_cely;


# Smazání os. údajů u dříve zrušených projektů (cron.delete_personal_data_canceled_projects)
WITH stare AS (
	SELECT h1.vazba FROM historie h1	
		JOIN soubor ON soubor.historie = h1.vazba
		JOIN projekt ON projekt.soubory = soubor.vazba
		JOIN historie h2 ON h2.vazba = projekt.historie
	WHERE (projekt.stav = 8 AND h2.typ_zmeny = 'P78' AND h2.datum_zmeny < (now() - INTERVAL '1 year')) OR (projekt.stav = 8 AND h2.typ_zmeny = 'P18')
)
DELETE FROM historie WHERE historie.vazba IN (SELECT vazba FROM stare);
	
WITH stare AS (
	SELECT projekt.soubory FROM projekt
		JOIN historie ON historie.vazba = projekt.historie
	WHERE (stav = 8 AND typ_zmeny = 'P78' AND datum_zmeny < (now() - INTERVAL '1 year')) OR (stav = 8 AND typ_zmeny = 'P18')
)
DELETE FROM soubor WHERE soubor.vazba IN (SELECT soubory FROM stare);
    
WITH stare AS (
	SELECT oznamovatel.projekt FROM oznamovatel
		JOIN projekt ON oznamovatel.projekt = projekt.id
		JOIN historie ON historie.vazba = projekt.historie
	WHERE stav = 8 AND typ_zmeny = 'P78' AND datum_zmeny < (now() - INTERVAL '1 year') OR (stav = 8 AND typ_zmeny = 'P18')
)
UPDATE oznamovatel SET
	email = CURRENT_DATE || ': údaj odstraněn',
	adresa = CURRENT_DATE || ': údaj odstraněn',
	odpovedna_osoba = CURRENT_DATE || ': údaj odstraněn',
	telefon = CURRENT_DATE || ': údaj odstraněn'
FROM stare WHERE oznamovatel.projekt = stare.projekt;


# Smazání oznamovatelů u velmi starých projektů (cron.delete_reporter_data_ten_years)
WITH smaz AS (
	SELECT h1.vazba FROM historie h1	
		JOIN soubor ON soubor.historie = h1.vazba
		JOIN projekt ON projekt.soubory = soubor.vazba
		JOIN historie h2 ON h2.vazba = projekt.historie
	WHERE h2.typ_zmeny IN ('PX0', 'PX1') AND typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136') AND h2.datum_zmeny < (now() - INTERVAL '10 year')
)
DELETE FROM historie WHERE historie.vazba IN (SELECT vazba FROM smaz);
	
WITH smaz AS (
	SELECT projekt.soubory FROM projekt
		JOIN historie ON historie.vazba = projekt.historie
	WHERE typ_zmeny IN ('PX0', 'PX1') AND typ_projektu = (SELECT id FROM heslar WHERE ident_cely = 'HES-001136') AND datum_zmeny < (now() - INTERVAL '10 year')
)
DELETE FROM soubor WHERE soubor.vazba IN (SELECT soubory FROM smaz);
	
WITH smaz AS (
	SELECT oznamovatel.projekt FROM oznamovatel
		JOIN projekt ON oznamovatel.projekt = projekt.id
		JOIN historie ON historie.vazba = projekt.historie
	WHERE typ_zmeny IN ('PX0', 'PX1') AND datum_zmeny < (now() - INTERVAL '10 year')
)
DELETE FROM oznamovatel WHERE oznamovatel.projekt IN (SELECT projekt FROM smaz);
