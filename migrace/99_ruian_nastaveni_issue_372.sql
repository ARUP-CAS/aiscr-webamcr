-- Issue 372
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_nazev_key UNIQUE(nazev);
ALTER TABLE ruian_katastr ADD CONSTRAINT ruian_katastr_kod_key UNIQUE(kod);
ALTER TABLE ruian_katastr DROP COLUMN nazev_stary; 
ALTER TABLE ruain_katastr DROP COLUMN aktualni; 
ALTER TABLE ruian_katastr DROP COLUMN soucasny; 

ALTER TABLE ruian_kraj ALTER COLUMN definicni_bod SET NOT NULL;
ALTER TABLE ruian_kraj ALTER COLUMN hranice SET NOT NULL;

ALTER TABLE ruian_okres ALTER COLUMN definicni_bod SET NOT NULL;
ALTER TABLE ruian_okres ALTER COLUMN hranice SET NOT NULL;
