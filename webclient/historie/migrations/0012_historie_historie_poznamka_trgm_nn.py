from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('historie', '0011_enable_pg_trgm'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX historie_poznamka_upper_trgm_idx
                ON historie
                USING GIN (UPPER(poznamka) gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS historie_poznamka_upper_trgm_idx;
            """,
        ),
    ]
