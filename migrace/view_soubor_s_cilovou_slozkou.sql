CREATE OR REPLACE VIEW soubor_s_cilovou_slozkou AS
	SELECT soubor.id as id_souboru, nazev_zkraceny, nazev_puvodni,
	CASE
		-- AG - napojeno na projekt + název ve struktuře [hash]_oznameni_[projekt.ident_cely]*.pdf
		WHEN soubor_vazby.typ_vazby = 'projekt' THEN
			CASE
				WHEN nazev ~ '\w*_oznameni_?C-\d*\.pdf' THEN 'AG/'
				ELSE 'PD/'
			END
		-- FN - vše co má vazbu na samostatný nález
		WHEN soubor_vazby.typ_vazby = 'samostatny_nalez' THEN 'FN/'
		-- SD - vše co má vazbu na DT Dokument
		WHEN soubor_vazby.typ_vazby = 'dokument'  THEN
			CASE
				WHEN heslar_typ_dokumetu.zkratka IN ('ZA', 'ZL') THEN '!DO NOT MIGRATE'
				ELSE 'SD/'
			END
	END AS hlavni_slozka,
	TO_CHAR(soubor.vytvoreno, 'YYYY/MM/DD/') AS podslozka
	FROM public.soubor
	INNER JOIN public.soubor_vazby on soubor.vazba = soubor_vazby.id
	LEFT OUTER JOIN public.dokument on dokument.soubory = soubor_vazby.id
	LEFT OUTER JOIN public.heslar as heslar_typ_dokumetu on heslar_typ_dokumetu.id = dokument.rada;
