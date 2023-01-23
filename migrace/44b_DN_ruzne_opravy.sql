-- Odstranění dokumentů ZA/ZL
DELETE FROM dokument USING heslar
WHERE dokument.rada = heslar.id
AND (heslar.ident_cely = 'HES-000884' OR heslar.ident_cely = 'HES-000885');
