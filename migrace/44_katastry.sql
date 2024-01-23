ALTER TABLE ruian_katastr ALTER COLUMN pian DROP NOT NULL;

-- Mažeme všechny PIAN bez vazeb (zálohu provedeme před migrací).
DELETE FROM pian WHERE id IN
(
    SELECT pian.id FROM pian
    LEFT JOIN dokumentacni_jednotka ON pian.id = dokumentacni_jednotka.pian
    WHERE dokumentacni_jednotka.id is NULL
);
