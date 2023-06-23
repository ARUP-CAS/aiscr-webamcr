from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import PROJEKT_STAV_OZNAMENY, CESKY, ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('heslar', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE heslar_ident_cely_seq START 1;
            """,
            reverse_sql="",
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE IF EXISTS heslar
            ALTER COLUMN ident_cely SET DEFAULT('HES-'::text || "right"(
            concat('000000', (nextval('heslar_ident_cely_seq'::regclass))::text), 6));
            """,
            reverse_sql="",
        ),
        AddDefaultValue(
            model_name='HeslarNazev',
            name='povolit_zmeny',
            value=True
        )
    ]
