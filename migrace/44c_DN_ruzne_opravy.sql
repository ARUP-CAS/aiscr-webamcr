-- Nastavení správného EPSG a typu pro geometrie

DROP VIEW IF EXISTS public.view_novy_stary_katastr;

-- Oprava na singlepart
UPDATE kladyzm SET the_geom = ST_GeometryN(the_geom, 1);

-- 5514
ALTER TABLE kladysm5 ALTER COLUMN geom TYPE geometry(POLYGON, 5514) USING ST_SetSRID(geom, 5514);
ALTER TABLE kladyzm ALTER COLUMN the_geom TYPE geometry(POLYGON, 5514) USING ST_SetSRID(the_geom, 5514);
ALTER TABLE pian ALTER COLUMN geom_sjtsk TYPE geometry(GEOMETRY, 5514) USING ST_SetSRID(geom_sjtsk, 5514);
ALTER TABLE samostatny_nalez ALTER COLUMN geom_sjtsk TYPE geometry(POINT, 5514) USING ST_SetSRID(geom_sjtsk, 5514);
ALTER TABLE vyskovy_bod ALTER COLUMN geom TYPE geometry(POINTZ, 5514) USING ST_SetSRID(geom, 5514);

-- 4326
ALTER TABLE pian ALTER COLUMN geom TYPE geometry(GEOMETRY, 4326) USING ST_SetSRID(geom, 4326);
ALTER TABLE projekt ALTER COLUMN geom TYPE geometry(GEOMETRY, 4326) USING ST_SetSRID(geom, 4326);
ALTER TABLE ruian_katastr ALTER COLUMN definicni_bod TYPE geometry(POINT, 4326) USING ST_SetSRID(definicni_bod, 4326);
ALTER TABLE ruian_katastr ALTER COLUMN hranice TYPE geometry(MULTIPOLYGON, 4326) USING ST_SetSRID(hranice, 4326);
ALTER TABLE ruian_kraj ALTER COLUMN definicni_bod TYPE geometry(POINT, 4326) USING ST_SetSRID(definicni_bod, 4326);
ALTER TABLE ruian_kraj ALTER COLUMN hranice TYPE geometry(MULTIPOLYGON, 4326) USING ST_SetSRID(hranice, 4326);
ALTER TABLE ruian_okres ALTER COLUMN definicni_bod TYPE geometry(POINT, 4326) USING ST_SetSRID(definicni_bod, 4326);
ALTER TABLE ruian_okres ALTER COLUMN hranice TYPE geometry(MULTIPOLYGON, 4326) USING ST_SetSRID(hranice, 4326);
ALTER TABLE samostatny_nalez ALTER COLUMN geom TYPE geometry(POINT, 4326) USING ST_SetSRID(geom, 4326);
