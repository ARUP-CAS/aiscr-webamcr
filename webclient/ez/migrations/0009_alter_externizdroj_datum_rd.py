# Generated by Django 4.2.11 on 2024-04-05 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ez", "0008_rename_organizace_nazev_externizdroj_organizace"),
    ]

    operations = [
        migrations.RunSQL(
            "update externi_zdroj set datum_rd = null where datum_rd = ''",
            "update externi_zdroj set datum_rd = null where datum_rd = ''"
        ),
        migrations.RunSQL(
            "ALTER TABLE externi_zdroj ALTER COLUMN datum_rd TYPE DATE USING to_date(datum_rd, 'YYYY-MM-DD');",
            "ALTER TABLE externi_zdroj ALTER COLUMN datum_rd TYPE VARCHAR;"
        ),
        migrations.AlterField(
            model_name="externizdroj",
            name="datum_rd",
            field=models.DateField(blank=True, null=True),
        ),
    ]
