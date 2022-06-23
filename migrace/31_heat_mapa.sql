--First view of all pians with 0.01 precision
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l2;
DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l1;
CREATE MATERIALIZED VIEW amcr_heat_pian_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.pian;
-- create heat map for count(pians)>0
CREATE MATERIALIZED VIEW amcr_heat_pian_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_l1 group by st_centroid having count(*) >10;
