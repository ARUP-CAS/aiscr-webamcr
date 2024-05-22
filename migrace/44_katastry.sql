ALTER TABLE ruian_katastr ALTER COLUMN pian DROP NOT NULL;

-- Doplnění PIAN lokalit s přesností na katastr
WITH
	kvtab AS (
		SELECT nextval('komponenta_vazby_id_seq') AS new_id, az.id AS azid FROM lokalita lok
		LEFT JOIN archeologicky_zaznam az ON lok.archeologicky_zaznam = az.id
		LEFT JOIN dokumentacni_jednotka dj ON az.id = dj.archeologicky_zaznam
		WHERE dj.id is null
	),
	kvins AS (
		INSERT INTO komponenta_vazby (id, typ_vazby) SELECT new_id, 'dokumentacni_jednotka' FROM kvtab
	)
INSERT INTO dokumentacni_jednotka (negativni_jednotka, ident_cely, archeologicky_zaznam, pian, typ, komponenty)
SELECT true, az.ident_cely || '-D01', az.id, kat.pian_id, (SELECT id FROM heslar WHERE ident_cely = 'HES-001073'),
	(SELECT new_id FROM kvtab WHERE kvtab.azid = az.id) FROM lokalita lok
LEFT JOIN archeologicky_zaznam az ON lok.archeologicky_zaznam = az.id
LEFT JOIN dokumentacni_jednotka dj ON az.id = dj.archeologicky_zaznam
LEFT JOIN ruian_katastr kat ON az.hlavni_katastr = kat.id
WHERE dj.id is null;


-- Mažeme všechny PIAN bez vazeb (zálohu provedeme před migrací).
DELETE FROM pian WHERE id IN
(
    SELECT pian.id FROM pian
    LEFT JOIN dokumentacni_jednotka ON pian.id = dokumentacni_jednotka.pian
    WHERE dokumentacni_jednotka.id is NULL
);
