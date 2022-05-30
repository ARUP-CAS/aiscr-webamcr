--Rozsireni tabulky o geometrii S-JTSK
ALTER TABLE public.samostatny_nalez ADD geom_sjtsk  geometry;
ALTER TABLE public.samostatny_nalez ADD geom_system  VARCHAR(6) default 'wgs84';

ALTER TABLE public.pian ADD geom_sjtsk  geometry;
ALTER TABLE public.pian ADD geom_system  VARCHAR(6) default 'wgs84';