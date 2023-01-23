-- Nastavení správného EPSG pro geometrie
-- 5514
SELECT UpdateGeometrySRID('kladysm5','geom',5514);
SELECT UpdateGeometrySRID('kladyzm','the_geom',5514);
SELECT UpdateGeometrySRID('vyskovy_bod','geom',5514);
SELECT UpdateGeometrySRID('pian','geom_sjtsk',5514);
SELECT UpdateGeometrySRID('samostatny_nalez','geom_sjtsk',5514);
-- 4326
SELECT UpdateGeometrySRID('pian','geom',4326);
SELECT UpdateGeometrySRID('projekt','geom',4326);
SELECT UpdateGeometrySRID('ruian_katastr','definicni_bod',4326);
SELECT UpdateGeometrySRID('ruian_katastr','hranice',4326);
SELECT UpdateGeometrySRID('ruian_kraj','definicni_bod',4326);
SELECT UpdateGeometrySRID('ruian_kraj','hranice',4326);
SELECT UpdateGeometrySRID('ruian_okres','definicni_bod',4326);
SELECT UpdateGeometrySRID('ruian_okres','hranice',4326);
SELECT UpdateGeometrySRID('samostatny_nalez','geom',4326);
