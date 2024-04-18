from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pas', '0005_alter_samostatnynalez_projekt'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_pas_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.samostatny_nalez where geom is not null;
            CREATE MATERIALIZED VIEW amcr_heat_pas_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pas_l1 where ST_IsEmpty(geom) = false group by st_centroid having count(*) > 1;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pas_l2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pas_l1;
            """
        ),
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_pas_lx1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.0001) AS geom from public.samostatny_nalez where geom is not null;
            CREATE MATERIALIZED VIEW amcr_heat_pas_lx2 as select count(*) as count, geom as st_centroid from amcr_heat_pas_lx1 group by st_centroid;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pas_lx2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pas_lx1;
            """
        ),
    ]
