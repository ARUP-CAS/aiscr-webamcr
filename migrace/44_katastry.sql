DELETE FROM pian where id in (
SELECT pian.id FROM heslar_nazev
INNER JOIN (heslar INNER JOIN (pian LEFT JOIN dokumentacni_jednotka ON pian.id = dokumentacni_jednotka.pian)
			ON heslar.ID = pian.presnost) ON heslar_nazev.ID = heslar.nazev_heslare
			WHERE (((heslar_nazev.nazev)='pian_presnost')
				   AND ((heslar.zkratka)='4' AND ((dokumentacni_jednotka.id) Is Null)))
)