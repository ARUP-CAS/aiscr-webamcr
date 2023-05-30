from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_test"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.projekt_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.projekt_xident_seq;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.dokument_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.dokument_xident_seq;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.lokalita_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.lokalita_xident_seq;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.pian_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.pian_xident_seq;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.akce_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.akce_xident_seq;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS public.externi_zdroj_xident_seq
            INCREMENT BY 1
            MINVALUE 1 MAXVALUE 999999999
            """,
            reverse_sql="DROP SEQUENCE public.externi_zdroj_xident_seq;",
        ),
    ]
