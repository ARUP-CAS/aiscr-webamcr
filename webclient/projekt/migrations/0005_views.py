from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projekt', '0004_default'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_projekt_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.projekt where geom is not null;
            CREATE MATERIALIZED VIEW amcr_heat_projekt_l2 as select count(*) as count, geom as st_centroid from amcr_heat_projekt_l1 group by st_centroid having count(*) >10;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_l2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_l1;
            """
        ),
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_projekt_lx1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.0001) AS geom from public.projekt where geom is not null;
            CREATE MATERIALIZED VIEW amcr_heat_projekt_lx2 as select count(*) as count, geom as st_centroid from amcr_heat_projekt_lx1 group by st_centroid;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_lx2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_projekt_lx1;
            """
        ),
    ]
