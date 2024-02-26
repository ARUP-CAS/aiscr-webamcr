--Presnost wgs-84 bude nastavena na 7mist
--Presnost SJTSK bude nastavena na 2 mista 
--SN-WGS-84
UPDATE public.samostatny_nalez  SET geom=ST_ReducePrecision(ST_MakeValid(geom),0.0000001)
WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom),0.0000001));
--SN-JRSK
UPDATE public.samostatny_nalez  SET geom_sjtsk=ST_ReducePrecision(ST_MakeValid(geom_sjtsk),0.01)
WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom_sjtsk),0.01));
--Dokument3D-WGS-84
UPDATE public.dokument_extra_data  SET geom=ST_ReducePrecision(ST_MakeValid(geom),0.0000001)
WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom),0.0000001));
--Projekt
UPDATE public.projekt  SET geom=ST_ReducePrecision(ST_MakeValid(geom),0.0000001)
WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom),0.0000001));
--Pian-WGS-84
UPDATE public.pian  SET geom=ST_ReducePrecision(ST_MakeValid(geom),0.0000001)
WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom),0.0000001));
--Pian-SJTSK
UPDATE public.pian  SET geom_sjtsk=ST_ReducePrecision(ST_MakeValid(geom_sjtsk),0.01)
WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(ST_MakeValid(geom_sjtsk),0.01));
