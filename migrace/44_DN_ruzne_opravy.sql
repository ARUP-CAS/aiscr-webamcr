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
