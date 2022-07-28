--Prevedeni northing,easting,niveleta do sloupce reprezentujici geometrii bodu
UPDATE public.vyskovy_bod
SET geom=ST_GeomFromText(CONCAT('POINT(',abs(northing)::text,' ',abs(easting)::text,' ',niveleta::text,')'))
WHERE geom IS  null;