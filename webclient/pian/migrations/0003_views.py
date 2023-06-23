from django.db import migrations,models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pian', '0002_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name="pian",
            name="ident_cely",
            field=models.CharField(max_length=16, unique=True),
        ),
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_pian_l1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.01) AS geom from public.pian;
            CREATE MATERIALIZED VIEW amcr_heat_pian_l2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_l1 group by st_centroid having count(*) >10;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_l1;
            """
        ),
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW amcr_heat_pian_lx1 as select id,ident_cely,ST_ReducePrecision(st_centroid(st_buffer(geom,1)),0.0001) AS geom from public.pian;
            CREATE MATERIALIZED VIEW amcr_heat_pian_lx2 as select count(*) as count, geom as st_centroid from amcr_heat_pian_lx1 group by st_centroid;
            """,
            reverse_sql="""
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_lx2;
            DROP MATERIALIZED VIEW IF EXISTS amcr_heat_pian_lx1;
            """
        ),
    ]
