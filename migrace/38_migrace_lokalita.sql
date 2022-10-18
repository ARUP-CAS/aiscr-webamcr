insert into public.heslar_nazev
VALUES (48, 'jistota_urceni', true),
	(49, 'stav_dochovani', true);
insert into public.heslar
values (
		nextval('heslar_id_seq'::regclass),
		NULL,
		48,
		'jisté (> 95 %)',
		null,
		null,
		'certain (> 95 %)',
		null,
		null,
		1,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		48,
		'nejisté (50-95 %)',
		null,
		null,
		'uncertain (50-95 %)',
		null,
		null,
		2,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		48,
		'domnělé (5-50 %)',
		null,
		null,
		'alleged (5-50 %)',
		null,
		null,
		3,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		48,
		'pseudolokalita (< 5 %)',
		null,
		null,
		'pseudolocality (< 5 %)',
		null,
		null,
		4,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		49,
		'zaniklá lokalita',
		null,
		null,
		'extinct site',
		null,
		null,
		1,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		49,
		'lokalita pod zástavbou',
		null,
		null,
		'location under development',
		null,
		null,
		2,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		49,
		'nadzemní relikty',
		null,
		null,
		'aboveground relics',
		null,
		null,
		3,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		49,
		'ruina',
		null,
		null,
		'ruina',
		null,
		null,
		4,
		null
	),
	(
		nextval('heslar_id_seq'::regclass),
		NULL,
		49,
		'historická budova / komplex',
		null,
		null,
		'historical building / complex',
		null,
		null,
		5,
		null
	);
update heslar
set heslo = 'Katastrální území',
	heslo_en = 'Catastral area'
where heslo = 'Nelokalizovaná akce'