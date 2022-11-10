-- Placeholdery pro chybějící či duplkicitní EN hesla.
UPDATE heslar SET heslo_en = 'translate: ' & ident_cely WHERE (heslo_en Is Null);
UPDATE heslar SET heslo_en = 'chain necklace' WHERE ident_cely = 'HES-000756';
UPDATE heslar SET heslo_en = 'chopper' WHERE ident_cely = 'HES-000801';
