-- Řešení pro chybějící či duplkicitní EN hesla.
UPDATE heslar SET heslo_en = 'translate: ' || ident_cely WHERE (heslo_en Is Null);
UPDATE heslar SET heslo_en = 'chain necklace' WHERE ident_cely = 'HES-000756';
UPDATE heslar SET heslo_en = 'chopper' WHERE ident_cely = 'HES-000801';
UPDATE organizace SET nazev_zkraceny_en = 'translate: ' || id WHERE (nazev_zkraceny_en Is Null);

-- Odstranění dokumentů ZA/ZL
DELETE FROM dokument, soubor USING dokument
INNER JOIN heslar ON dokument.rada = heslar.id
INNER JOIN soubor ON soubor.vazba = dokument.soubory
WHERE heslar.ident_cely = 'HES-000884' OR heslar.ident_cely = 'HES-000885';

-- Migrace soubor.vlastnik a soubor.vytvoreno do historie
UPDATE soubor SET historie = (INSERT INTO historie_vazby (typ_vazby) VALUES 'soubor' RETURNING id) WHERE soubor.historie IS NULL;
ALTER TABLE soubor ADD CONSTRAINT soubor_historie_key UNIQUE (historie);
INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT vytvoreno, vlastnik, nazev_puvodni, historie, 'SBR0' FROM soubor;
ALTER TABLE soubor DROP COLUMN vytvoreno, vlastnik;

-- Smazat oznamovatele, pokud je všude „údaj odstraněn“
DELETE FROM oznamovatel WHERE email = 'údaj odstraněn' AND adresa = 'údaj odstraněn' AND odpovedna_osoba = 'údaj odstraněn' AND oznamovatel = 'údaj odstraněn' AND telefon = 'údaj odstraněn';

-- Odstranění nepotřebných tabulek
DROP TABLE projekt_oznameni_suffix;
DROP TABLE systemove_promenne;

-- Odstranění nepotřebných heslářů
DELETE FROM heslar WHERE nazev_heslare = (SELECT id FROM heslar_nazev WHERE nazev = 'autorska_role');
DELETE FROM heslar_nazev WHERE nazev = 'autorska_role';

-- Nastavení editovatelnosti heslářů
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'adb_podnet';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'adb_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'akce_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'akce_typ_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'aktivita';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'areal';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'areal_kat';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'datum_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dohlednost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dok_jednotka_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_format';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_material';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_nahrada';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_rada';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'dokument_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_ulozeni';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'dokument_zachovalost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'ext_zdroj_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'jazyk';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'jistota_urceni';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'letfoto_tvar';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'letiste';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'lokalita_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'lokalita_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'lokalita_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'nalez_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'nalezove_okolnosti';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'obdobi';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'obdobi_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'objekt_specifikace_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'organizace_typ';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pamatkova_ochrana';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pian_presnost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pian_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'pocasi';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'posudek_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_druh';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_druh_kat';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'predmet_specifikace';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'pristupnost';
UPDATE heslar_nazev SET povolit_zmeny = false WHERE nazev = 'projekt_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'stav_dochovani';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'udalost_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'vyskovy_bod_typ';
UPDATE heslar_nazev SET povolit_zmeny = true WHERE nazev = 'zeme';
