--pians
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l2;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l1;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_lx2;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_lx1;
--master view of all projekts with 0.01 precision
CREATE MATERIALIZED VIEW amcr_heat_pian_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.pian;
CREATE MATERIALIZED VIEW amcr_heat_pian_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_l1 group by st_centroid having count(*) >10;
--detail view of all projekts with 0.0001 precision
CREATE MATERIALIZED VIEW amcr_heat_pian_lx1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.0001) AS geom from public.pian;
CREATE MATERIALIZED VIEW amcr_heat_pian_lx2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_lx1 group by st_centroid;
--projects
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_l2;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_l1;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_lx2;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_lx1;
--master view of all projekts with 0.01 precision
CREATE MATERIALIZED VIEW amcr_heat_projekt_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.projekt where geom is not null;
CREATE MATERIALIZED VIEW amcr_heat_projekt_l2 as select count(*) as count, geom as st_centroid from amcr_heat_projekt_l1 group by st_centroid having count(*) >10;
--detail view of all projekts with 0.0001 precision
CREATE MATERIALIZED VIEW amcr_heat_projekt_lx1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.0001) AS geom from public.projekt where geom is not null;
CREATE MATERIALIZED VIEW amcr_heat_projekt_lx2 as select count(*) as count, geom as st_centroid from amcr_heat_projekt_lx1 group by st_centroid;
