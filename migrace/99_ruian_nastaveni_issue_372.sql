-- Issue 372
-- archeologicky_zaznam.hlavni_katastr
WITH prevod AS
(
    SELECT archeologicky_zaznam.historie as vazba, k1.nazev as stary, k2.nazev as novy FROM archeologicky_zaznam 
    JOIN ruian_katastr k1 ON k1.id = archeologicky_zaznam.hlavni_katastr
    JOIN ruian_katastr k2 ON k2.id = k1.soucasny
    WHERE k1.aktualni is false
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), stary || ' -> ' || novy, vazba, 'KAT' FROM prevod;
UPDATE archeologicky_zaznam SET hlavni_katastr = ruian_katastr.soucasny FROM ruian_katastr WHERE ruian_katastr.id = archeologicky_zaznam.hlavni_katastr AND aktualni is false;

-- archeologicky_zaznam_katastr.katastr_id
WITH prevod AS
(
    SELECT archeologicky_zaznam.historie as vazba, k1.nazev as stary, k2.nazev as novy FROM archeologicky_zaznam_katastr
    JOIN archeologicky_zaznam ON archeologicky_zaznam.id = archeologicky_zaznam_katastr.archeologicky_zaznam_id
    JOIN ruian_katastr k1 ON k1.id = archeologicky_zaznam_katastr.katastr_id
    JOIN ruian_katastr k2 ON k2.id = k1.soucasny
    WHERE k1.aktualni is false
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), stary || ' -> ' || novy, vazba, 'KAT' FROM prevod;
WITH prevod AS
(
    SELECT DISTINCT archeologicky_zaznam.id as az, ruian_katastr.soucasny as kat FROM archeologicky_zaznam_katastr
    JOIN archeologicky_zaznam ON archeologicky_zaznam.id = archeologicky_zaznam_katastr.archeologicky_zaznam_id
    JOIN ruian_katastr ON ruian_katastr.id = archeologicky_zaznam_katastr.katastr_id
    WHERE ruian_katastr.aktualni is false
)
INSERT INTO archeologicky_zaznam_katastr (archeologicky_zaznam_id, katastr_id) SELECT az, kat FROM prevod WHERE NOT EXISTS (SELECT * FROM archeologicky_zaznam_katastr WHERE archeologicky_zaznam_id = az AND katastr_id = kat);
DELETE FROM archeologicky_zaznam_katastr WHERE (SELECT aktualni FROM ruian_katastr WHERE ruian_katastr.id = archeologicky_zaznam_katastr.katastr_id) is false;
DELETE FROM archeologicky_zaznam_katastr WHERE (SELECT hlavni_katastr FROM archeologicky_zaznam WHERE archeologicky_zaznam.id = archeologicky_zaznam_katastr.archeologicky_zaznam_id) = katastr_id;

-- neident_akce.katastr
UPDATE neident_akce SET katastr = ruian_katastr.soucasny FROM ruian_katastr WHERE ruian_katastr.id = neident_akce.katastr AND aktualni is false;

-- projekt.hlavni_katastr
WITH prevod AS
(
    SELECT projekt.historie as vazba, k1.nazev as stary, k2.nazev as novy FROM projekt 
    JOIN ruian_katastr k1 ON k1.id = projekt.hlavni_katastr
    JOIN ruian_katastr k2 ON k2.id = k1.soucasny
    WHERE k1.aktualni is false
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), stary || ' -> ' || novy, vazba, 'KAT' FROM prevod;
UPDATE projekt SET hlavni_katastr = ruian_katastr.soucasny FROM ruian_katastr WHERE ruian_katastr.id = projekt.hlavni_katastr AND aktualni is false;

-- projekt_katastr.katastr_id
WITH prevod AS
(
    SELECT projekt.historie as vazba, k1.nazev as stary, k2.nazev as novy FROM projekt_katastr
    JOIN projekt ON projekt.id = projekt_katastr.projekt_id
    JOIN ruian_katastr k1 ON k1.id = projekt_katastr.katastr_id
    JOIN ruian_katastr k2 ON k2.id = k1.soucasny
    WHERE k1.aktualni is false
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), stary || ' -> ' || novy, vazba, 'KAT' FROM prevod;
WITH prevod AS
(
    SELECT DISTINCT projekt.id as az, ruian_katastr.soucasny as kat FROM projekt_katastr
    JOIN projekt ON projekt.id = projekt_katastr.projekt_id
    JOIN ruian_katastr ON ruian_katastr.id = projekt_katastr.katastr_id
    WHERE ruian_katastr.aktualni is false
)
INSERT INTO projekt_katastr (projekt_id, katastr_id) SELECT az, kat FROM prevod WHERE NOT EXISTS (SELECT * FROM projekt_katastr WHERE projekt_id = az AND katastr_id = kat);
DELETE FROM projekt_katastr WHERE (SELECT aktualni FROM ruian_katastr WHERE ruian_katastr.id = projekt_katastr.katastr_id) is false;
DELETE FROM projekt_katastr WHERE (SELECT hlavni_katastr FROM projekt WHERE projekt.id = projekt_katastr.projekt_id) = katastr_id;

-- samostatny_nalez.katastr
WITH prevod AS
(
    SELECT samostatny_nalez.historie as vazba, k1.nazev as stary, k2.nazev as novy FROM samostatny_nalez 
    JOIN ruian_katastr k1 ON k1.id = samostatny_nalez.katastr
    JOIN ruian_katastr k2 ON k2.id = k1.soucasny
    WHERE k1.aktualni is false
)
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT now(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), stary || ' -> ' || novy, vazba, 'KAT' FROM prevod;
UPDATE samostatny_nalez SET katastr = ruian_katastr.soucasny FROM ruian_katastr WHERE ruian_katastr.id = samostatny_nalez.katastr AND aktualni is false;

-- smazání neaktuálních katastrů
DELETE FROM ruian_katastr WHERE aktualni is false;

-- úprava struktury
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_nazev_key UNIQUE(nazev);
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_kod_key UNIQUE(kod);
ALTER TABLE ruian_katastr DROP COLUMN nazev_stary; 
ALTER TABLE ruian_katastr DROP COLUMN aktualni; 
ALTER TABLE ruian_katastr DROP COLUMN soucasny;
