ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_geom_system_check ;
UPDATE samostatny_nalez set geom_system = '5514' where  geom_system="sjtsk"
UPDATE samostatny_nalez set geom_system = '5514*' where  geom_system="sjtsk*"
UPDATE samostatny_nalez set geom_system = '4326' where  geom_system="wgs84"
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_geom_system_check CHECK ((geom_system = '5514' AND geom_sjtsk IS NOT NULL) OR (geom_system = '5514*' AND geom_sjtsk IS NOT NULL) OR (geom_system = '4326' AND geom IS NOT NULL) OR (geom_sjtsk IS NULL AND geom IS NULL));

ALTER TABLE pian ADD CONSTRAINT pian_geom_system_check ;
UPDATE samostatny_nalez set geom_system = '5514' where  geom_system="sjtsk"
UPDATE samostatny_nalez set geom_system = '5514*' where  geom_system="sjtsk*"
UPDATE samostatny_nalez set geom_system = '4326' where  geom_system="wgs84"
ALTER TABLE pian ADD CONSTRAINT pian_geom_system_check CHECK ((geom_system = '5514' AND geom_sjtsk IS NOT NULL) OR (geom_system = '5514*' AND geom_sjtsk IS NOT NULL) OR  (geom_system = '4326' AND geom IS NOT NULL) OR (geom_sjtsk IS NULL AND geom IS NULL));