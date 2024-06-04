--Rozsireni tabulky o geometrii S-JTSK
ALTER TABLE public.samostatny_nalez ADD geom_sjtsk  geometry;
ALTER TABLE public.samostatny_nalez ADD geom_system  VARCHAR(4) NOT NULL default '4326';
ALTER TABLE samostatny_nalez ADD CONSTRAINT samostatny_nalez_geom_system_check CHECK ((geom_system = '5514' AND geom_sjtsk IS NOT NULL) OR (geom_system = '4326' AND geom IS NOT NULL) OR (geom_sjtsk IS NULL AND geom IS NULL));

ALTER TABLE public.pian ADD geom_sjtsk  geometry;
ALTER TABLE public.pian ADD geom_system  VARCHAR(4) NOT NULL default '4326';
ALTER TABLE pian ADD CONSTRAINT pian_geom_system_check CHECK ((geom_system = '5514' AND geom_sjtsk IS NOT NULL) OR  (geom_system = '4326' AND geom IS NOT NULL) OR (geom_sjtsk IS NULL AND geom IS NULL));
