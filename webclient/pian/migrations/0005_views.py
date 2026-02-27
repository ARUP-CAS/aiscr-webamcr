from django.db import migrations,models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pian', '0004_alter_piansekvence_unique_together_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l1;
            CREATE MATERIALIZED VIEW amcr_heat_pian_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.05) AS geom from pian;
            CREATE MATERIALIZED VIEW amcr_heat_pian_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_l1 group by st_centroid ;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l1;
            CREATE MATERIALIZED VIEW amcr_heat_pian_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from pian;
            CREATE MATERIALIZED VIEW amcr_heat_pian_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_l1 group by st_centroid having count(*) >10;
            """
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX amcr_heat_pian_l2_st_centroid ON amcr_heat_pian_l2 USING gist (st_centroid); 
            CREATE INDEX amcr_heat_pian_lx2_st_centroid ON amcr_heat_pian_lx2 USING gist (st_centroid); 
            
            CREATE INDEX amcr_heat_pas_l2_st_centroid ON amcr_heat_pas_l2 USING gist (st_centroid); 
            CREATE INDEX amcr_heat_pas_lx2_st_centroid ON amcr_heat_pas_lx2 USING gist (st_centroid); 
            
            CREATE INDEX amcr_heat_projekt_l2_st_centroid ON amcr_heat_projekt_l2 USING gist (st_centroid); 
            CREATE INDEX amcr_heat_projekt_lx2_st_centroid ON amcr_heat_projekt_lx2 USING gist (st_centroid);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS amcr_heat_pian_l2_st_centroid;
            DROP INDEX IF EXISTS amcr_heat_pian_lx2_st_centroid;
            
            DROP INDEX IF EXISTS amcr_heat_pas_l2_st_centroid;
            DROP INDEX IF EXISTS amcr_heat_pas_lx2_st_centroid;
            
            DROP INDEX IF EXISTS amcr_heat_projekt_l2_st_centroid;
            DROP INDEX IF EXISTS amcr_heat_projekt_lx2_st_centroid;
            """
        ),
    ]
