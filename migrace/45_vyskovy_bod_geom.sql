--Prevedeni northing,easting,niveleta do sloupce reprezentujici geometrii bodu
UPDATE public.vyskovy_bod
SET geom=ST_ReducePrecision(ST_MakeValid(ST_GeomFromText(CONCAT('POINT(',northing::text,' ',easting::text,' ',niveleta::text,')'))),0.01)
WHERE geom IS  null;
